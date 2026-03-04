from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import gymnasium as gym
import numpy as np

from tetris_rl.core.constants import BOARD
from tetris_rl.core.pieces import Tetromino
from tetris_rl.core.tetris_logic import LockResult, TetrisGame


@dataclass(frozen=True, slots=True)
class RewardConfig:
    survival: float = 0.01
    line_clear_scale: float = 1.0
    combo_bonus: float = 0.5  # Bonus for consecutive line clears
    tspin_bonus: float = 2.0  # Bonus for T-spin moves
    holes: float = 0.05
    deep_holes_penalty: float = 0.1  # Additional penalty for holes at bottom
    max_height: float = 0.02
    bumpiness: float = 0.01
    game_over: float = 5.0


def _one_hot_piece(piece: Tetromino) -> np.ndarray:
    names = ("I", "O", "T", "S", "Z", "J", "L")
    v = np.zeros((7,), dtype=np.float32)
    v[names.index(piece.value)] = 1.0
    return v


def _column_heights(board: list[list[int]]) -> np.ndarray:
    heights = np.zeros((BOARD.width,), dtype=np.float32)
    for x in range(BOARD.width):
        h = 0
        for y in range(BOARD.height):
            if board[y][x] != 0:
                h = BOARD.height - y
                break
        heights[x] = float(h)
    return heights


def _holes(board: list[list[int]], heights: np.ndarray) -> float:
    holes = 0
    for x in range(BOARD.width):
        col_h = int(heights[x])
        if col_h == 0:
            continue
        top_y = BOARD.height - col_h
        seen_block = False
        for y in range(top_y, BOARD.height):
            if board[y][x] != 0:
                seen_block = True
            elif seen_block:
                holes += 1
    return float(holes)


def _deep_holes(board: list[list[int]], heights: np.ndarray, threshold: int = 5) -> float:
    """Count holes near the bottom of the board (more dangerous)."""
    deep_holes = 0
    for x in range(BOARD.width):
        col_h = int(heights[x])
        if col_h < threshold:
            continue
        # Look at bottom portion of the column
        for y in range(BOARD.height - threshold, BOARD.height):
            if board[y][x] == 0:
                # Check if there's a block above
                has_block_above = False
                for ay in range(BOARD.height - col_h, y):
                    if board[ay][x] != 0:
                        has_block_above = True
                        break
                if has_block_above:
                    deep_holes += 1
    return float(deep_holes)


def _solid_rows(board: list[list[int]], heights: np.ndarray) -> float:
    """Count number of completely solid rows at the bottom (good for stability)."""
    solid_count = 0
    for y in range(BOARD.height - 1, -1, -1):
        is_solid = True
        for x in range(BOARD.width):
            if board[y][x] == 0 and heights[x] > 0:
                is_solid = False
                break
            elif heights[x] == 0:
                # Column is empty, row can't be solid from below
                break
        if is_solid and any(board[y][x] != 0 for x in range(BOARD.width)):
            solid_count += 1
        else:
            # Once we find a non-solid row, stop counting
            break
    return float(solid_count)


def _column_adjacency_match(board: list[list[int]], heights: np.ndarray) -> float:
    """Measure how well columns match their neighbors (good for T-spin opportunities)."""
    if len(heights) < 2:
        return 0.0
    # Count adjacent columns with similar heights
    match_count = 0
    for i in range(len(heights) - 1):
        if abs(heights[i] - heights[i + 1]) <= 1:
            match_count += 1
    # Also check for T-spin friendly patterns (3 columns with same height)
    tspin_pattern = 0
    for i in range(len(heights) - 2):
        if heights[i] == heights[i + 1] == heights[i + 2]:
            tspin_pattern += 1
    return float(match_count) + float(tspin_pattern * 0.5)


def _landing_options(game: TetrisGame) -> float:
    """Count the number of different legal placement options for current piece."""
    placements = game.legal_final_placements()
    # Normalize by max possible (typically 40-60 depending on piece)
    return float(len(placements)) / 60.0


def _bumpiness(heights: np.ndarray) -> float:
    return float(np.sum(np.abs(np.diff(heights))))


def _filled_ratio(board: list[list[int]]) -> float:
    filled = 0
    for y in range(BOARD.height):
        for x in range(BOARD.width):
            if board[y][x] != 0:
                filled += 1
    return float(filled) / float(BOARD.height * BOARD.width)


def _features(game: TetrisGame) -> np.ndarray:
    board = game.board
    heights = _column_heights(board)
    max_h = float(np.max(heights))
    var_h = float(np.var(heights))
    holes = _holes(board, heights)
    deep_h = _deep_holes(board, heights)
    solid_rows = _solid_rows(board, heights)
    col_match = _column_adjacency_match(board, heights)
    landing_opts = _landing_options(game)
    bump = _bumpiness(heights)
    agg_h = float(np.sum(heights))
    fill = _filled_ratio(board)
    cur = _one_hot_piece(game.current.name) if game.current is not None else np.zeros((7,), dtype=np.float32)
    nxt = _one_hot_piece(game.next_piece)

    # Extended feature vector:
    # - heights: 10 values
    # - [max_h, var_h, holes, deep_h, solid_rows, col_match, landing_opts, bump, agg_h, fill]: 10 values
    # - cur: 7 values
    # - nxt: 7 values
    # Total: 34 values (was 24)
    feats = np.concatenate(
        [
            heights,
            np.array(
                [max_h, var_h, holes, deep_h, solid_rows, col_match, landing_opts, bump, agg_h, fill],
                dtype=np.float32,
            ),
            cur,
            nxt,
        ],
        axis=0,
    )
    return feats.astype(np.float32, copy=False)


class TetrisEnv(gym.Env[np.ndarray, int]):
    metadata = {"render_modes": ["ansi"], "render_fps": 30}

    def __init__(
        self,
        seed: int = 0,
        reward: RewardConfig | None = None,
        max_actions: int = 64,
    ) -> None:
        super().__init__()
        self.game = TetrisGame(seed=seed)
        self.reward_cfg = reward or RewardConfig()
        self.max_actions = int(max_actions)

        feat_dim = int(_features(self.game).shape[0])
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(feat_dim,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(self.max_actions)

        self._last_lossless_score: float = 0.0
        self._combo_counter: int = 0

    def action_mask(self) -> np.ndarray:
        placements = self.game.legal_final_placements()
        mask = np.zeros((self.max_actions,), dtype=np.float32)
        mask[: min(len(placements), self.max_actions)] = 1.0
        return mask

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self.game.reset(seed=seed)
        self._last_lossless_score = float(self.game.score)
        self._combo_counter = 0
        obs = _features(self.game)
        info: dict[str, Any] = {"action_mask": self.action_mask(), "score": self.game.score}
        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        placements = self.game.legal_final_placements()
        if len(placements) == 0:
            self.game.game_over = True
            obs = _features(self.game)
            info: dict[str, Any] = {"action_mask": self.action_mask(), "score": self.game.score}
            return obs, -self.reward_cfg.game_over, True, False, info

        idx = int(action)
        if idx < 0 or idx >= len(placements):
            idx = 0
        rot, x, _y = placements[idx]
        res: LockResult = self.game.apply_final_placement(rot=rot, x=x)

        obs = _features(self.game)
        terminated = bool(self.game.game_over)
        truncated = False

        heights = obs[: BOARD.width]
        max_h = float(obs[BOARD.width])
        holes = float(obs[BOARD.width + 2])
        deep_holes = float(obs[BOARD.width + 3])
        bump = float(obs[BOARD.width + 7])

        reward = 0.0
        reward += self.reward_cfg.survival

        # Line clear reward with combo bonus
        if res.lines_cleared > 0:
            self._combo_counter += 1
            # Segmented reward: 1, 2, 4, 6 instead of 1, 4, 9, 16
            line_rewards = {1: 1.0, 2: 3.0, 3: 6.0, 4: 10.0}
            base_reward = line_rewards.get(res.lines_cleared, res.lines_cleared * 3.0)
            reward += self.reward_cfg.line_clear_scale * base_reward
            # Add combo bonus
            if self._combo_counter > 1:
                reward += self.reward_cfg.combo_bonus * (self._combo_counter - 1)
        else:
            self._combo_counter = 0

        # T-spin bonus (simplified detection based on piece type and clearing)
        # In a full implementation, you'd detect actual T-spin mechanics
        if res.lines_cleared > 0 and self.game.current is not None:
            if self.game.current.name == "T":
                reward += self.reward_cfg.tspin_bonus * (res.lines_cleared / 4.0)

        # Penalties
        reward -= self.reward_cfg.holes * holes
        reward -= self.reward_cfg.deep_holes_penalty * deep_holes
        reward -= self.reward_cfg.max_height * max_h
        reward -= self.reward_cfg.bumpiness * bump

        if terminated:
            reward -= self.reward_cfg.game_over

        info: dict[str, Any] = {
            "action_mask": self.action_mask(),
            "lines_cleared": res.lines_cleared,
            "score": self.game.score,
            "heights": heights.copy(),
            "combo": self._combo_counter,
        }
        return obs, float(reward), terminated, truncated, info

    def render(self) -> str:
        grid = self.game.get_board_with_active()
        rows = []
        for y in range(BOARD.height):
            row = "".join("." if v == 0 else "#" for v in grid[y])
            rows.append(row)
        return "\n".join(rows)

    def close(self) -> None:
        return
