from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt


class TrainingPanel(QWidget):
    start_training = pyqtSignal()
    stop_training = pyqtSignal()
    load_model = pyqtSignal()
    save_model = pyqtSignal()
    speed_changed = pyqtSignal(int)
    workers_changed = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()

        self.btn_start = QPushButton("Start Training")
        self.btn_stop = QPushButton("Stop")
        self.btn_load = QPushButton("Load Model")
        self.btn_save = QPushButton("Save Model")

        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setMinimum(10)
        self.speed.setMaximum(500)
        self.speed.setValue(120)

        self.workers = QSpinBox()
        self.workers.setMinimum(1)
        self.workers.setMaximum(64)
        self.workers.setValue(4)

        self.status = QLabel("Idle")
        self.status.setStyleSheet("color: #cfd2ff;")

        self.action_label = QLabel("-")
        self.action_label.setStyleSheet("color: #cfd2ff;")

        self._build()
        self._wire()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        g_ctrl = QGroupBox("Training Controls")
        ctrl_layout = QVBoxLayout(g_ctrl)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        ctrl_layout.addLayout(btn_row)
        btn_row2 = QHBoxLayout()
        btn_row2.addWidget(self.btn_load)
        btn_row2.addWidget(self.btn_save)
        ctrl_layout.addLayout(btn_row2)

        form = QFormLayout()
        form.addRow("Speed", self.speed)
        form.addRow("Workers", self.workers)
        ctrl_layout.addLayout(form)

        g_stat = QGroupBox("Status")
        stat_layout = QFormLayout(g_stat)
        stat_layout.addRow("State", self.status)
        stat_layout.addRow("Current Action", self.action_label)

        root.addWidget(g_ctrl)
        root.addWidget(g_stat)
        root.addStretch(1)

    def _wire(self) -> None:
        self.btn_start.clicked.connect(self.start_training.emit)
        self.btn_stop.clicked.connect(self.stop_training.emit)
        self.btn_load.clicked.connect(self.load_model.emit)
        self.btn_save.clicked.connect(self.save_model.emit)
        self.speed.valueChanged.connect(self.speed_changed.emit)
        self.workers.valueChanged.connect(self.workers_changed.emit)

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def set_action(self, text: str) -> None:
        self.action_label.setText(text)
