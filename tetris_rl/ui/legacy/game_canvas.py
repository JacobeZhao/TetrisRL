from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from tetris_rl.core.constants import BOARD, PIECE_COLORS_RGB, PIECE_ID_TO_NAME
from tetris_rl.core.pieces import PIECE_DEFS, Tetromino


def _color_for_cell(v: int) -> QColor:
    if v == 0:
        return QColor(20, 20, 24)
    name = PIECE_ID_TO_NAME.get(int(v), "T")
    rgb = PIECE_COLORS_RGB.get(name, (200, 200, 200))
    return QColor(*rgb)


class GameCanvas(QWidget):
    def __init__(self, cell_px: int = 24) -> None:
        super().__init__()
        self.cell_px = int(cell_px)
        self._grid: list[list[int]] = [[0 for _ in range(BOARD.width)] for _ in range(BOARD.height)]
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(self.cell_px * BOARD.width, self.cell_px * BOARD.height)

    def set_grid(self, grid: list[list[int]]) -> None:
        self._grid = [row[:] for row in grid]
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(12, 12, 16))

        grid_pen = QPen(QColor(35, 35, 42))
        grid_pen.setWidth(1)
        border_pen = QPen(QColor(220, 220, 230))
        border_pen.setWidth(2)

        for y in range(BOARD.height):
            for x in range(BOARD.width):
                v = self._grid[y][x]
                color = _color_for_cell(v)
                px = x * self.cell_px
                py = y * self.cell_px
                p.fillRect(px, py, self.cell_px, self.cell_px, color)
                p.setPen(grid_pen)
                p.drawRect(px, py, self.cell_px, self.cell_px)
                if v != 0:
                    p.setPen(QPen(color.lighter(130), 2))
                    p.drawRect(px + 1, py + 1, self.cell_px - 2, self.cell_px - 2)

        p.setPen(border_pen)
        p.drawRect(0, 0, self.cell_px * BOARD.width, self.cell_px * BOARD.height)


class NextPieceWidget(QWidget):
    def __init__(self, cell_px: int = 20) -> None:
        super().__init__()
        self.cell_px = int(cell_px)
        self._piece: Optional[Tetromino] = None
        self.setMinimumSize(self.cell_px * 6, self.cell_px * 6)

    def set_piece(self, piece: Tetromino | None) -> None:
        self._piece = piece
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(12, 12, 16))
        if self._piece is None:
            return

        cells = PIECE_DEFS[self._piece].cells(0)
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = (max_x - min_x + 1) * self.cell_px
        h = (max_y - min_y + 1) * self.cell_px
        ox = (self.width() - w) // 2
        oy = (self.height() - h) // 2

        base = QColor(*PIECE_COLORS_RGB[self._piece.value])
        grid_pen = QPen(QColor(35, 35, 42))
        grid_pen.setWidth(1)

        for cx, cy in cells:
            x = ox + (cx - min_x) * self.cell_px
            y = oy + (cy - min_y) * self.cell_px
            p.fillRect(x, y, self.cell_px, self.cell_px, base)
            p.setPen(grid_pen)
            p.drawRect(x, y, self.cell_px, self.cell_px)
            p.setPen(QPen(base.lighter(130), 2))
            p.drawRect(x + 1, y + 1, self.cell_px - 2, self.cell_px - 2)

