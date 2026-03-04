from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


@dataclass(slots=True)
class PlotPoint:
    x: int
    y: float


class LivePlots(FigureCanvas):
    def __init__(self, max_points: int = 500) -> None:
        self._max_points = int(max_points)
        self._loss = deque[PlotPoint](maxlen=self._max_points)
        self._score = deque[PlotPoint](maxlen=self._max_points)

        # Lazy initialization - figure will be created when needed
        self._fig: Figure | None = None
        self._initialized = False
        self._loss_line = None
        self._score_line = None
        self._ax_loss = None
        self._ax_score = None

        # Create a placeholder widget that shows "Loading..."
        self._placeholder = QWidget()
        layout = QVBoxLayout(self._placeholder)
        self._label = QLabel("Loading plots...")
        self._label.setStyleSheet("color: #a0a3b8; font-size: 14px;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        # Initialize the canvas with a dummy figure
        super().__init__(Figure(figsize=(5, 4), tight_layout=True))
        self.hide()

    def lazy_init(self) -> None:
        """Initialize the matplotlib figure and axes on first use."""
        if self._initialized:
            return

        self._fig = Figure(figsize=(5, 4), tight_layout=True, facecolor="#0f1016")
        super().__init__(self._fig)

        self._ax_loss = self._fig.add_subplot(2, 1, 1)
        self._ax_score = self._fig.add_subplot(2, 1, 2)

        # Style the axes
        for ax in (self._ax_loss, self._ax_score):
            ax.set_facecolor("#0f1016")
            ax.tick_params(colors="#a0a3b8")
            ax.xaxis.label.set_color("#a0a3b8")
            ax.yaxis.label.set_color("#a0a3b8")
            ax.title.set_color("#cfd2ff")
            for spine in ax.spines.values():
                spine.set_color("#2b2d3a")

        (self._loss_line,) = self._ax_loss.plot([], [], color="#1f77b4", linewidth=1.5)
        (self._score_line,) = self._ax_score.plot([], [], color="#2ca02c", linewidth=1.5)

        self._ax_loss.set_title("Loss")
        self._ax_score.set_title("Episode Score")
        self._ax_score.set_xlabel("Update")

        self._fig.tight_layout()
        self._initialized = True
        self.show()

    def reset(self) -> None:
        if not self._initialized:
            return
        self._loss.clear()
        self._score.clear()
        self._redraw()

    def add(self, update_idx: int, loss: float, score: float) -> None:
        if not self._initialized:
            self.lazy_init()
        self._loss.append(PlotPoint(update_idx, float(loss)))
        self._score.append(PlotPoint(update_idx, float(score)))
        self._redraw()

    def _redraw(self) -> None:
        if not self._initialized:
            return

        if len(self._loss) > 0:
            xs = [p.x for p in self._loss]
            ys = [p.y for p in self._loss]
            self._loss_line.set_data(xs, ys)
            self._ax_loss.relim()
            self._ax_loss.autoscale_view()
        else:
            self._loss_line.set_data([], [])

        if len(self._score) > 0:
            xs = [p.x for p in self._score]
            ys = [p.y for p in self._score]
            self._score_line.set_data(xs, ys)
            self._ax_score.relim()
            self._ax_score.autoscale_view()
        else:
            self._score_line.set_data([], [])

        self.draw_idle()

