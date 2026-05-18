"""训练可视化页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSplitter, QProgressBar, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor

from qlib_gui.widgets.chart_widget import RealtimeChart


class TrainingPage(QWidget):
    backtest_requested = pyqtSignal()
    simulation_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model_id = None
        self._model_type = None
        self._train_epochs = []
        self._train_scores = []
        self._valid_scores = []
        self._train_losses = []
        self._valid_losses = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题行
        header = QHBoxLayout()
        self._title_label = QLabel("训练可视化")
        self._title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.addWidget(self._title_label)
        header.addStretch()

        self._backtest_btn = QPushButton("运行回测")
        self._backtest_btn.setEnabled(False)
        self._backtest_btn.clicked.connect(self.backtest_requested.emit)
        self._backtest_btn.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._backtest_btn)

        self._sim_btn = QPushButton("模拟炒股")
        self._sim_btn.setEnabled(False)
        self._sim_btn.clicked.connect(self.simulation_requested.emit)
        self._sim_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._sim_btn)

        self._stop_btn = QPushButton("停止训练")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        self._stop_btn.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._stop_btn)
        layout.addLayout(header)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFormat("等待开始...")
        layout.addWidget(self._progress)

        # 上部: 图表
        splitter = QSplitter(Qt.Orientation.Vertical)

        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)

        self._loss_chart = RealtimeChart("训练损失", "Epoch", "Loss")
        self._loss_chart.add_series("train_loss", "#3498db")
        self._loss_chart.add_series("val_loss", "#e74c3c")
        charts_layout.addWidget(self._loss_chart)

        self._score_chart = RealtimeChart("模型评分", "Epoch", "Score")
        self._score_chart.add_series("train_score", "#3498db")
        self._score_chart.add_series("val_score", "#e74c3c")
        charts_layout.addWidget(self._score_chart)

        splitter.addWidget(charts_widget)

        # 下部: 日志 + 信息
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 训练信息
        info_group = QGroupBox("训练信息")
        info_layout = QVBoxLayout(info_group)
        self._info_label = QLabel("等待开始训练...")
        self._info_label.setWordWrap(True)
        self._info_label.setFont(QFont("Microsoft YaHei", 10))
        info_layout.addWidget(self._info_label)
        bottom_layout.addWidget(info_group, 1)

        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout(log_group)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 9))
        self._log_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        log_layout.addWidget(self._log_text)
        bottom_layout.addWidget(log_group, 2)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 250])
        layout.addWidget(splitter)

    def start_training(self, model_id: str, model_type: str):
        """准备训练"""
        self._model_id = model_id
        self._model_type = model_type
        self._train_epochs = []
        self._train_scores = []
        self._valid_scores = []
        self._train_losses = []
        self._valid_losses = []
        self._loss_chart.clear_all()
        self._score_chart.clear_all()
        self._progress.setValue(0)
        self._progress.setFormat("训练中 0%")
        self._backtest_btn.setEnabled(False)
        self._sim_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._info_label.setText(f"正在训练模型: {model_id}\n类型: {model_type}")
        self._log_text.clear()
        self._append_log(f"开始训练模型: {model_id} ({model_type})")

    def on_epoch_completed(self, epoch: int, metrics: dict):
        """每 epoch 回调"""
        self._train_epochs.append(epoch)
        train_loss = metrics.get("train_loss", 0)
        val_loss = metrics.get("val_loss", 0)
        train_score = metrics.get("train_score", 0)
        val_score = metrics.get("val_score", 0)

        self._train_losses.append(train_loss)
        self._valid_losses.append(val_loss)
        self._train_scores.append(train_score)
        self._valid_scores.append(val_score)

        self._loss_chart.append_point("train_loss", epoch, train_loss)
        self._loss_chart.append_point("val_loss", epoch, val_loss)
        self._score_chart.append_point("train_score", epoch, train_score)
        self._score_chart.append_point("val_score", epoch, val_score)

        best_score = metrics.get("best_score", val_score)
        best_epoch = metrics.get("best_epoch", epoch)
        stop_steps = metrics.get("stop_steps", 0)

        self._info_label.setText(
            f"模型: {self._model_id}\n"
            f"当前 Epoch: {epoch}\n"
            f"训练损失: {train_loss:.6f}  验证损失: {val_loss:.6f}\n"
            f"训练评分: {train_score:.6f}  验证评分: {val_score:.6f}\n"
            f"最佳评分: {best_score:.6f} @ Epoch {best_epoch}\n"
            f"早停计数: {stop_steps}"
        )

        self._append_log(
            f"Epoch {epoch}: train_loss={train_loss:.6f}, val_loss={val_loss:.6f}, "
            f"train_score={train_score:.6f}, val_score={val_score:.6f}"
        )

    def on_progress_update(self, current: int, total: int):
        """进度更新"""
        if total > 0:
            pct = int(current / total * 100)
            self._progress.setValue(pct)
            self._progress.setFormat(f"训练中 {pct}% (Epoch {current}/{total})")

    def on_training_finished(self, evals_result: dict):
        """训练完成"""
        self._progress.setValue(100)
        self._progress.setFormat("训练完成 ✓")
        self._backtest_btn.setEnabled(True)
        self._sim_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._append_log("训练完成!")
        self._info_label.setText(
            f"模型: {self._model_id}\n"
            f"状态: 训练完成\n"
            f"总 Epoch: {len(self._train_epochs)}\n"
            f"可以运行回测或模拟炒股"
        )

    def on_training_error(self, error_msg: str):
        """训练错误"""
        self._progress.setFormat("训练失败 ✗")
        self._stop_btn.setEnabled(False)
        self._append_log(f"错误: {error_msg}")
        self._info_label.setText(f"训练失败:\n{error_msg}")

    def _append_log(self, text: str):
        self._log_text.append(text)
        self._log_text.moveCursor(QTextCursor.MoveOperation.End)
