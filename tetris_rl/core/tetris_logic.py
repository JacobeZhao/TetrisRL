from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Iterable, Optional

from tetris_rl.core.constants import BOARD, LINE_CLEAR_SCORES, PIECE_NAME_TO_ID
from tetris_rl.core.pieces import KICK_TABLE, Tetromino, all_tetrominoes, iter_cells


@dataclass(slots=True)
class ActivePiece:
    name: Tetromino
    rotation: int
    x: int
    y: int


@dataclass(slots=True)
class LockResult:
    lines_cleared: int
    score_delta: int
    game_over: bool


class TetrisGame:
    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        self._seed = seed
        self.board: list[list[int]] = [[0 for _ in range(BOARD.width)] for _ in range(BOARD.height)]
        self.score: int = 0
        self.lines: int = 0
        self.episode: int = 0
        self.step_count: int = 0
        self.game_over: bool = False
        self.current: ActivePiece | None = None
        self.next_piece: Tetromino = self._random_piece()
        self._spawn_next()

    def clone(self) -> TetrisGame:
        return copy.deepcopy(self)

    def seed(self, seed: int) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

    def reset(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            self.seed(seed)
        self.board = [[0 for _ in range(BOARD.width)] for _ in range(BOARD.height)]
        self.score = 0
        self.lines = 0
        self.step_count = 0
        self.game_over = False
        self.episode += 1
        self.current = None
        self.next_piece = self._random_piece()
        self._spawn_next()

    def _random_piece(self) -> Tetromino:
        return self._rng.choice(all_tetrominoes())

    def _spawn_next(self) -> None:
        self.current = ActivePiece(self.next_piece, 0, 3, -2)
        self.next_piece = self._random_piece()
        if self._collides(self.current):
            self.game_over = True

    def _cells_of_active(self, piece: ActivePiece) -> Iterable[tuple[int, int]]:
        return iter_cells(piece.name, piece.rotation, piece.x, piece.y)

    def _collides(self, piece: ActivePiece) -> bool:
        for x, y in self._cells_of_active(piece):
            if x < 0 or x >= BOARD.width:
                return True
            if y >= BOARD.height:
                return True
            if y >= 0 and self.board[y][x] != 0:
                return True
        return False

    def try_move(self, dx: int, dy: int) -> bool:
        if self.current is None or self.game_over:
            return False
        candidate = ActivePiece(self.current.name, self.current.rotation, self.current.x + dx, self.current.y + dy)
        if self._collides(candidate):
            return False
        self.current = candidate
        return True

    def try_rotate(self, direction: int) -> bool:
        if self.current is None or self.game_over:
            return False
        old_rot = self.current.rotation & 3
        new_rot = (old_rot + direction) & 3
        kicks = KICK_TABLE[self.current.name].get((old_rot, new_rot), ((0, 0),))
        for kx, ky in kicks:
            candidate = ActivePiece(self.current.name, new_rot, self.current.x + kx, self.current.y + ky)
            if not self._collides(candidate):
                self.current = candidate
                return True
        return False

    def soft_drop(self) -> bool:
        if self.current is None or self.game_over:
            return False
        moved = self.try_move(0, 1)
        if moved:
            self.step_count += 1
            return True
        self.lock_piece()
        self.step_count += 1
        return False

    def hard_drop(self) -> LockResult:
        if self.current is None or self.game_over:
            return LockResult(0, 0, self.game_over)
        while self.try_move(0, 1):
            self.step_count += 1
        res = self.lock_piece()
        self.step_count += 1
        return res

    def lock_piece(self) -> LockResult:
        if self.current is None:
            return LockResult(0, 0, self.game_over)
        pid = PIECE_NAME_TO_ID[self.current.name.value]
        for x, y in self._cells_of_active(self.current):
            if y < 0:
                self.game_over = True
                return LockResult(0, 0, True)
            self.board[y][x] = pid

        cleared = self._clear_lines()
        score_delta = LINE_CLEAR_SCORES.get(cleared, 0)
        self.lines += cleared
        self.score += score_delta
        self._spawn_next()
        return LockResult(cleared, score_delta, self.game_over)

    def _clear_lines(self) -> int:
        new_rows: list[list[int]] = []
        cleared = 0
        for row in self.board:
            if all(v != 0 for v in row):
                cleared += 1
            else:
                new_rows.append(row)
        if cleared == 0:
            return 0
        while len(new_rows) < BOARD.height:
            new_rows.insert(0, [0 for _ in range(BOARD.width)])
        self.board = new_rows
        return cleared

    def get_board_with_active(self) -> list[list[int]]:
        grid = [row[:] for row in self.board]
        if self.current is None:
            return grid
        pid = PIECE_NAME_TO_ID[self.current.name.value]
        for x, y in self._cells_of_active(self.current):
            if 0 <= y < BOARD.height and 0 <= x < BOARD.width:
                grid[y][x] = pid
        return grid

    def legal_final_placements(self) -> list[tuple[int, int, int]]:
        if self.current is None or self.game_over:
            return []
        placements: list[tuple[int, int, int]] = []
        piece = self.current.name
        tried: set[tuple[int, int]] = set()
        for rot in range(4):
            min_x = -2
            max_x = BOARD.width + 2
            for x in range(min_x, max_x):
                key = (rot, x)
                if key in tried:
                    continue
                tried.add(key)
                y = -2
                candidate = ActivePiece(piece, rot, x, y)
                if self._collides(candidate):
                    while y < 2 and self._collides(candidate):
                        y += 1
                        candidate = ActivePiece(piece, rot, x, y)
                    if self._collides(candidate):
                        continue
                while True:
                    below = ActivePiece(piece, rot, x, candidate.y + 1)
                    if self._collides(below):
                        break
                    candidate = below
                if candidate.y < -1:
                    continue
                if not self._collides(candidate):
                    placements.append((rot, x, candidate.y))
        uniq: dict[tuple[int, int, int], None] = {}
        for p in placements:
            uniq[p] = None
        return list(uniq.keys())

    def apply_final_placement(self, rot: int, x: int) -> LockResult:
        if self.current is None or self.game_over:
            return LockResult(0, 0, self.game_over)
        piece = self.current.name
        y = -2
        candidate = ActivePiece(piece, rot & 3, x, y)
        if self._collides(candidate):
            while y < 2 and self._collides(candidate):
                y += 1
                candidate = ActivePiece(piece, rot & 3, x, y)
            if self._collides(candidate):
                self.game_over = True
                return LockResult(0, 0, True)
        while True:
            below = ActivePiece(piece, rot & 3, x, candidate.y + 1)
            if self._collides(below):
                break
            candidate = below
        self.current = candidate
        return self.lock_piece()

