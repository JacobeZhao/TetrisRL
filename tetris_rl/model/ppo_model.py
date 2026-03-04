from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical


@dataclass(slots=True)
class ActorCriticOutput:
    logits: torch.Tensor
    value: torch.Tensor


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int, hidden_dim: int = 256, use_layer_norm: bool = True) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.use_layer_norm = use_layer_norm

        # First 10 features are column heights
        self.height_dim = 10
        self.other_dim = obs_dim - 14  # Total - heights - 2 piece one-hots

        # Column heights subnetwork (specialized for spatial structure)
        self.height_net = nn.Sequential(
            nn.Linear(self.height_dim, 128),
            nn.Tanh(),
            nn.LayerNorm(128) if use_layer_norm else nn.Identity(),
            nn.Linear(128, 128),
            nn.Tanh(),
            nn.LayerNorm(128) if use_layer_norm else nn.Identity(),
        )

        # Other features subnetwork (max_h, var_h, holes, etc.)
        self.other_net = nn.Sequential(
            nn.Linear(self.other_dim, 64),
            nn.Tanh(),
            nn.LayerNorm(64) if use_layer_norm else nn.Identity(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.LayerNorm(64) if use_layer_norm else nn.Identity(),
        )

        # Combined backbone
        combined_dim = 128 + 64 + 14  # height_out + other_out + piece_onehots
        self.backbone = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.Tanh(),
            nn.LayerNorm(hidden_dim) if use_layer_norm else nn.Identity(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.LayerNorm(hidden_dim) if use_layer_norm else nn.Identity(),
        )

        self.policy_head = nn.Linear(hidden_dim, self.act_dim)
        self.value_head = nn.Linear(hidden_dim, 1)

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                # Orthogonal initialization for stability
                nn.init.orthogonal_(m.weight, gain=1.0)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        # Smaller gain for policy head
        nn.init.orthogonal_(self.policy_head.weight, gain=0.01)
        if self.policy_head.bias is not None:
            nn.init.zeros_(self.policy_head.bias)

    def forward(self, obs: torch.Tensor) -> ActorCriticOutput:
        # Split observation into parts
        heights = obs[:, :self.height_dim]
        others = obs[:, self.height_dim:self.height_dim + self.other_dim]
        pieces = obs[:, self.height_dim + self.other_dim:]

        # Process through subnetworks
        h_out = self.height_net(heights)
        o_out = self.other_net(others)

        # Combine all features
        combined = torch.cat([h_out, o_out, pieces], dim=-1)

        # Process through backbone
        x = self.backbone(combined)
        logits = self.policy_head(x)
        value = self.value_head(x).squeeze(-1)
        return ActorCriticOutput(logits=logits, value=value)

    @staticmethod
    def _masked_logits(logits: torch.Tensor, action_mask: torch.Tensor | None) -> torch.Tensor:
        if action_mask is None:
            return logits
        mask = action_mask.to(dtype=torch.bool)
        neg = torch.full_like(logits, -1e9)
        return torch.where(mask, logits, neg)

    def dist(self, obs: torch.Tensor, action_mask: torch.Tensor | None = None) -> Categorical:
        out = self.forward(obs)
        logits = self._masked_logits(out.logits, action_mask)
        return Categorical(logits=logits)

    @torch.no_grad()
    def act(
        self,
        obs: np.ndarray,
        action_mask: np.ndarray | None = None,
        device: torch.device | None = None,
        deterministic: bool = False,
    ) -> tuple[int, float, float]:
        dev = device or next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=dev).unsqueeze(0)
        mask_t = None
        if action_mask is not None:
            mask_t = torch.as_tensor(action_mask, dtype=torch.float32, device=dev).unsqueeze(0)
        out = self.forward(obs_t)
        logits = self._masked_logits(out.logits, mask_t)
        dist = Categorical(logits=logits)
        if deterministic:
            action = torch.argmax(dist.probs, dim=-1)
        else:
            action = dist.sample()
        logprob = dist.log_prob(action)
        return int(action.item()), float(logprob.item()), float(out.value.item())

    def evaluate_actions(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        action_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        out = self.forward(obs)
        logits = self._masked_logits(out.logits, action_mask)
        dist = Categorical(logits=logits)
        logprob = dist.log_prob(actions)
        entropy = dist.entropy()
        return logprob, entropy, out.value
