from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoardSpec:
    width: int = 10
    height: int = 20


BOARD = BoardSpec()

LINE_CLEAR_SCORES: dict[int, int] = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

PIECE_NAME_TO_ID: dict[str, int] = {"I": 1, "O": 2, "T": 3, "S": 4, "Z": 5, "J": 6, "L": 7}
PIECE_ID_TO_NAME: dict[int, str] = {v: k for k, v in PIECE_NAME_TO_ID.items()}

PIECE_COLORS_RGB: dict[str, tuple[int, int, int]] = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

