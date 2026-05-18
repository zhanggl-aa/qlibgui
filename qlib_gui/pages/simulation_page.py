"""模拟炒股页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QSlider, QSpinBox, QGroupBox, QSizePolicy, QComboBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

import pandas as pd
import numpy as np

from qlib_gui.widgets.chart_widget import RealtimeChart
from qlib_gui.widgets.stock_table import StockTable
from qlib_gui.widgets.order_panel import OrderPanel
from qlib_gui.widgets.position_widget import PositionWidget
from qlib_gui.core.simulation_engine import SimulationEngine
from qlib_gui.core.realtime_simulation_engine import RealtimeSimulationEngine


class SimulationPage(QWidget):
    model_switch_requested = pyqtSignal(str)  # model_id
    simulation_requested = pyqtSignal(str)  # model_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._replay_engine = SimulationEngine(self)
        self._realtime_engine = RealtimeSimulationEngine(self)
        self._current_engine = self._replay_engine
        self._is_realtime_mode = False
        self._portfolio_values = []
        self._return_values = []
        self._dates = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题
        header = QHBoxLayout()
        title = QLabel("模拟炒股")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.addWidget(title)

        # 模式选择
        mode_group = QGroupBox("模式")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self._replay_radio = QRadioButton("回测回放")
        self._replay_radio.setChecked(True)
        self._realtime_radio = QRadioButton("实时预测")
        mode_layout.addWidget(self._replay_radio)
        mode_layout.addWidget(self._realtime_radio)
        self._mode_group = QButtonGroup()
        self._mode_group.addButton(self._replay_radio)
        self._mode_group.addButton(self._realtime_radio)
        self._mode_group.buttonClicked.connect(self._on_mode_changed)
        header.addWidget(mode_group)

        header.addWidget(QLabel("选择模型:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(160)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self._model_combo)

        header.addStretch()

        self._start_btn = QPushButton("开始模拟")
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start_simulation)
        self._start_btn.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._start_btn)

        self._date_label = QLabel("日期: --")
        self._date_label.setFont(QFont("Microsoft YaHei", 12))
        header.addWidget(self._date_label)
        layout.addLayout(header)

        # 三栏布局
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左栏: 信号 + 下单
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)

        signal_group = QGroupBox("预测信号排名")
        signal_layout = QVBoxLayout(signal_group)
        self._signal_table = StockTable("预测信号")
        signal_layout.addWidget(self._signal_table)
        left_layout.addWidget(signal_group, 3)

        self._order_panel = OrderPanel()
        left_layout.addWidget(self._order_panel, 1)

        splitter.addWidget(left)

        # 中栏: 图表
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(4, 0, 4, 0)

        self._pnl_chart = RealtimeChart("资产净值", "", "金额")
        self._pnl_chart.add_series("portfolio_value", "#3498db")
        self._pnl_chart.add_series("cash", "#27ae60")
        center_layout.addWidget(self._pnl_chart)

        self._return_chart = RealtimeChart("收益率 (%)", "", "收益率")
        self._return_chart.add_series("return_pct", "#e74c3c")
        center_layout.addWidget(self._return_chart)

        splitter.addWidget(center)

        # 右栏: 持仓 + 控制
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)

        self._position_widget = PositionWidget()
        right_layout.addWidget(self._position_widget, 3)

        # 控制面板
        ctrl_group = QGroupBox("模拟控制")
        ctrl_layout = QVBoxLayout(ctrl_group)

        # 日期滑块
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.setValue(0)
        self._slider.valueChanged.connect(self._on_slider_changed)
        ctrl_layout.addWidget(QLabel("交易进度:"))
        ctrl_layout.addWidget(self._slider)

        # 按钮行
        btn_row = QHBoxLayout()
        self._prev_btn = QPushButton("上一步")
        self._prev_btn.clicked.connect(self._on_step_backward)
        btn_row.addWidget(self._prev_btn)

        self._next_btn = QPushButton("下一步")
        self._next_btn.clicked.connect(self._on_step_forward)
        btn_row.addWidget(self._next_btn)

        ctrl_layout.addLayout(btn_row)

        # 自动播放
        auto_row = QHBoxLayout()
        self._auto_btn = QPushButton("自动播放")
        self._auto_btn.setCheckable(True)
        self._auto_btn.clicked.connect(self._on_auto_play)
        auto_row.addWidget(self._auto_btn)

        auto_row.addWidget(QLabel("间隔:"))
        self._speed_spin = QSpinBox()
        self._speed_spin.setRange(100, 5000)
        self._speed_spin.setValue(1000)
        self._speed_spin.setSingleStep(100)
        self._speed_spin.setSuffix(" ms")
        self._speed_spin.valueChanged.connect(self._on_speed_changed)
        auto_row.addWidget(self._speed_spin)
        ctrl_layout.addLayout(auto_row)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(self._on_reset)
        ctrl_layout.addWidget(self._reset_btn)

        right_layout.addWidget(ctrl_group, 1)

        splitter.addWidget(right)
        splitter.setSizes([300, 400, 300])

        layout.addWidget(splitter)

    def _connect_signals(self):
        # 回放引擎信号
        self._replay_engine.step_completed.connect(self._on_step_completed)
        self._replay_engine.simulation_finished.connect(self._on_simulation_finished)
        self._replay_engine.order_executed.connect(self._on_order_executed)
        # 实时引擎信号
        self._realtime_engine.step_completed.connect(self._on_step_completed)
        self._realtime_engine.simulation_finished.connect(self._on_simulation_finished)
        self._realtime_engine.order_executed.connect(self._on_order_executed)
        self._realtime_engine.prediction_started.connect(self._on_prediction_started)
        self._realtime_engine.prediction_completed.connect(self._on_prediction_completed)

        self._order_panel.order_submitted.connect(self._on_order_submitted)
        self._order_panel._auto_btn.clicked.connect(self._on_auto_trade)

    def initialize(self, pred: pd.Series, config: dict):
        """初始化模拟（回放模式）"""
        self._replay_engine.initialize(pred, config)
        self._slider.setRange(0, self._replay_engine.total_steps)
        self._slider.setValue(0)
        self._portfolio_values = []
        self._return_values = []
        self._dates = []
        self._pnl_chart.clear_all()
        self._return_chart.clear_all()

    def initialize_realtime(self, model, handler, segments: dict, config: dict, market: str = "csi300"):
        """初始化实时预测模拟"""
        self._realtime_engine.initialize(model, handler, segments, config, market)
        self._slider.setRange(0, self._realtime_engine.total_steps)
        self._slider.setValue(0)
        self._portfolio_values = []
        self._return_values = []
        self._dates = []
        self._pnl_chart.clear_all()
        self._return_chart.clear_all()

    def _on_step_completed(self, state: dict):
        """每步状态更新"""
        date = state.get("date")
        if date is not None:
            date_str = str(date.date()) if hasattr(date, 'date') else str(date)
            self._date_label.setText(f"日期: {date_str}")

        step = state.get("step", 0)
        self._slider.blockSignals(True)
        self._slider.setValue(step)
        self._slider.blockSignals(False)

        # 更新信号表
        signals = state.get("top_signals", pd.Series(dtype=float))
        positions = state.get("positions", {})
        self._signal_table.update_signals(signals, positions)

        # 更新持仓
        self._position_widget.update_state(state)

        # 更新图表 - 截断到当前步数防止回退后重复
        portfolio_value = state.get("portfolio_value", 0)
        cash = state.get("cash", 0)
        return_pct = state.get("return_pct", 0)

        if date is not None:
            if step <= len(self._portfolio_values):
                self._portfolio_values = self._portfolio_values[:step]
                self._return_values = self._return_values[:step]
                self._dates = self._dates[:step]
            self._portfolio_values.append(portfolio_value)
            self._return_values.append(return_pct)
            self._dates.append(date)
            x = list(range(len(self._portfolio_values)))
            self._pnl_chart.set_data("portfolio_value", x, self._portfolio_values)
            self._pnl_chart.set_data("cash", x, [cash] * len(x) if len(x) == 1 else self._portfolio_values)

            self._return_chart.set_data("return_pct", x, self._return_values)

    def _on_simulation_finished(self):
        self._auto_btn.setChecked(False)
        self._auto_btn.setText("自动播放")
        self._current_engine.stop_auto_play()

    def _on_prediction_started(self):
        """实时预测开始提示"""
        self._date_label.setText("正在预测...")

    def _on_prediction_completed(self):
        """实时预测完成"""
        pass

    def _on_mode_changed(self, button):
        """模式切换处理"""
        was_realtime = self._is_realtime_mode
        self._is_realtime_mode = (button == self._realtime_radio)
        if was_realtime == self._is_realtime_mode:
            return
        # 切换引擎
        if self._is_realtime_mode:
            self._current_engine = self._realtime_engine
        else:
            self._current_engine = self._replay_engine
        # 刷新状态
        if self._current_engine.is_initialized:
            self._slider.setRange(0, self._current_engine.total_steps)
            self._current_engine._emit_current_state()
        else:
            self._slider.setRange(0, 0)

    def _on_order_executed(self, result: dict):
        """订单执行结果"""
        if result.get("success"):
            direction = result.get("direction", "")
            stock_id = result.get("stock_id", "")
            amount = result.get("amount", 0)
            price = result.get("price", 0)
            # 刷新持仓
            if self._current_engine._current_step > 0:
                date = self._current_engine._calendar[self._current_engine._current_step - 1]
                if hasattr(self._current_engine, '_get_signals'):
                    signals = self._current_engine._get_signals(date)
                elif date in getattr(self._current_engine, '_current_preds', {}):
                    signals = self._current_engine._current_preds[date]
                else:
                    signals = pd.Series(dtype=float)
                self._position_widget.update_state(self._current_engine._build_state(date, signals))

    def _on_order_submitted(self, stock_id: str, amount: int, direction: int):
        result = self._current_engine.place_order(stock_id, amount, direction)

    def _on_auto_trade(self):
        self._current_engine.auto_trade_step()

    def _on_step_forward(self):
        self._current_engine.step_forward()

    def _on_step_backward(self):
        self._current_engine.step_backward()

    def _on_slider_changed(self, value: int):
        """滑块拖动导航到指定交易日"""
        if not self._current_engine.is_initialized:
            return
        current = self._current_engine.current_step
        if value == current:
            return
        self._current_engine.goto_step(value)

    def _on_auto_play(self, checked: bool):
        if checked:
            self._auto_btn.setText("暂停")
            self._current_engine.start_auto_play(self._speed_spin.value())
        else:
            self._auto_btn.setText("自动播放")
            self._current_engine.stop_auto_play()

    def _on_speed_changed(self, value: int):
        if self._current_engine.is_auto_playing:
            self._current_engine.stop_auto_play()
            self._current_engine.start_auto_play(value)

    def _on_reset(self):
        self._current_engine.reset()
        self._portfolio_values = []
        self._return_values = []
        self._dates = []
        self._pnl_chart.clear_all()
        self._return_chart.clear_all()
        self._slider.setValue(0)
        self._date_label.setText("日期: --")

    def update_model_list(self, trained_ids: list, current_id: str = None):
        """刷新模型选择下拉框"""
        self._model_combo.blockSignals(True)
        self._model_combo.clear()
        for mid in trained_ids:
            self._model_combo.addItem(mid)
        if current_id:
            idx = self._model_combo.findText(current_id)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
        self._model_combo.blockSignals(False)

        # 根据是否有模型来启用/禁用按钮
        self._start_btn.setEnabled(len(trained_ids) > 0)

    def _on_model_changed(self, model_id: str):
        if model_id:
            self._start_btn.setEnabled(True)
            self.model_switch_requested.emit(model_id)

    def _on_start_simulation(self):
        model_id = self._model_combo.currentText()
        if model_id:
            self.simulation_requested.emit(model_id)
