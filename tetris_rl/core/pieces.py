from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Iterable


class Tetromino(str, Enum):
    I = "I"
    O = "O"
    T = "T"
    S = "S"
    Z = "Z"
    J = "J"
    L = "L"


Rotation = int
Cell = tuple[int, int]
Kick = tuple[int, int]


@dataclass(frozen=True, slots=True)
class PieceDef:
    name: Tetromino
    cells_by_rotation: tuple[tuple[Cell, ...], tuple[Cell, ...], tuple[Cell, ...], tuple[Cell, ...]]

    def cells(self, rotation: Rotation) -> tuple[Cell, ...]:
        return self.cells_by_rotation[rotation & 3]


PIECE_DEFS: Final[dict[Tetromino, PieceDef]] = {
    Tetromino.I: PieceDef(
        Tetromino.I,
        (
            ((0, 1), (1, 1), (2, 1), (3, 1)),
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            ((0, 2), (1, 2), (2, 2), (3, 2)),
            ((1, 0), (1, 1), (1, 2), (1, 3)),
        ),
    ),
    Tetromino.O: PieceDef(
        Tetromino.O,
        (
            ((1, 0), (2, 0), (1, 1), (2, 1)),
            ((1, 0), (2, 0), (1, 1), (2, 1)),
            ((1, 0), (2, 0), (1, 1), (2, 1)),
            ((1, 0), (2, 0), (1, 1), (2, 1)),
        ),
    ),
    Tetromino.T: PieceDef(
        Tetromino.T,
        (
            ((1, 0), (0, 1), (1, 1), (2, 1)),
            ((1, 0), (1, 1), (2, 1), (1, 2)),
            ((0, 1), (1, 1), (2, 1), (1, 2)),
            ((1, 0), (0, 1), (1, 1), (1, 2)),
        ),
    ),
    Tetromino.S: PieceDef(
        Tetromino.S,
        (
            ((1, 0), (2, 0), (0, 1), (1, 1)),
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            ((1, 1), (2, 1), (0, 2), (1, 2)),
            ((0, 0), (0, 1), (1, 1), (1, 2)),
        ),
    ),
    Tetromino.Z: PieceDef(
        Tetromino.Z,
        (
            ((0, 0), (1, 0), (1, 1), (2, 1)),
            ((2, 0), (1, 1), (2, 1), (1, 2)),
            ((0, 1), (1, 1), (1, 2), (2, 2)),
            ((1, 0), (0, 1), (1, 1), (0, 2)),
        ),
    ),
    Tetromino.J: PieceDef(
        Tetromino.J,
        (
            ((0, 0), (0, 1), (1, 1), (2, 1)),
            ((1, 0), (2, 0), (1, 1), (1, 2)),
            ((0, 1), (1, 1), (2, 1), (2, 2)),
            ((1, 0), (1, 1), (0, 2), (1, 2)),
        ),
    ),
    Tetromino.L: PieceDef(
        Tetromino.L,
        (
            ((2, 0), (0, 1), (1, 1), (2, 1)),
            ((1, 0), (1, 1), (1, 2), (2, 2)),
            ((0, 1), (1, 1), (2, 1), (0, 2)),
            ((0, 0), (1, 0), (1, 1), (1, 2)),
        ),
    ),
}


def _jlstz_kicks() -> dict[tuple[int, int], tuple[Kick, ...]]:
    return {
        (0, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
        (1, 0): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
        (1, 2): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
        (2, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
        (2, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
        (3, 2): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
        (3, 0): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
        (0, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    }


def _i_kicks() -> dict[tuple[int, int], tuple[Kick, ...]]:
    return {
        (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
        (1, 0): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
        (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
        (2, 1): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
        (2, 3): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
        (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
        (3, 0): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
        (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
    }


KICK_TABLE: Final[dict[Tetromino, dict[tuple[int, int], tuple[Kick, ...]]]] = {
    Tetromino.I: _i_kicks(),
    Tetromino.O: {(0, 1): ((0, 0),), (1, 2): ((0, 0),), (2, 3): ((0, 0),), (3, 0): ((0, 0),),
                 (1, 0): ((0, 0),), (2, 1): ((0, 0),), (3, 2): ((0, 0),), (0, 3): ((0, 0),)},
    Tetromino.T: _jlstz_kicks(),
    Tetromino.S: _jlstz_kicks(),
    Tetromino.Z: _jlstz_kicks(),
    Tetromino.J: _jlstz_kicks(),
    Tetromino.L: _jlstz_kicks(),
}


def all_tetrominoes() -> tuple[Tetromino, ...]:
    return (Tetromino.I, Tetromino.O, Tetromino.T, Tetromino.S, Tetromino.Z, Tetromino.J, Tetromino.L)


def iter_cells(piece: Tetromino, rotation: Rotation, x: int, y: int) -> Iterable[tuple[int, int]]:
    for cx, cy in PIECE_DEFS[piece].cells(rotation):
        yield x + cx, y + cy

