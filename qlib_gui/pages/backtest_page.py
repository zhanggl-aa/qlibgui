"""回测结果页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSplitter, QSizePolicy, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

import pandas as pd
import numpy as np

from qlib_gui.widgets.chart_widget import RealtimeChart, ReturnChart
from qlib_gui.widgets.metric_card import MetricCard, MetricRow


class BacktestPage(QWidget):
    simulation_requested = pyqtSignal()
    model_switch_requested = pyqtSignal(str)  # model_id
    backtest_requested = pyqtSignal(str)  # model_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._report = None
        self._positions = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("回测分析")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.addWidget(title)

        header.addWidget(QLabel("选择模型:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(160)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self._model_combo)

        header.addStretch()

        self._run_btn = QPushButton("开始回测")
        self._run_btn.setEnabled(False)
        self._run_btn.clicked.connect(self._on_start_backtest)
        self._run_btn.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._run_btn)

        self._sim_btn = QPushButton("进入模拟炒股")
        self._sim_btn.setEnabled(False)
        self._sim_btn.clicked.connect(self.simulation_requested.emit)
        self._sim_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        header.addWidget(self._sim_btn)
        layout.addLayout(header)

        # Tab 页
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Tab 1: 收益曲线
        self._return_tab = QWidget()
        ret_layout = QVBoxLayout(self._return_tab)
        self._return_chart = ReturnChart()
        ret_layout.addWidget(self._return_chart)
        self._tabs.addTab(self._return_tab, "收益曲线")

        # Tab 2: 风险分析
        self._risk_tab = QWidget()
        risk_layout = QVBoxLayout(self._risk_tab)

        self._metric_row = MetricRow()
        self._metric_row.add_card("年化收益", "--", "%", "#2c3e50")
        self._metric_row.add_card("波动率", "--", "%", "#7f8c8d")
        self._metric_row.add_card("信息比率", "--", "", "#2c3e50")
        self._metric_row.add_card("最大回撤", "--", "%", "#e74c3c")
        self._metric_row.add_card("换手率", "--", "%", "#7f8c8d")
        risk_layout.addWidget(self._metric_row)

        # IC 曲线
        self._ic_chart = RealtimeChart("IC 分析", "日期", "IC")
        self._ic_chart.add_series("IC", "#3498db")
        self._ic_chart.add_series("Rank IC", "#e74c3c")
        risk_layout.addWidget(self._ic_chart)

        risk_layout.addStretch()
        self._tabs.addTab(self._risk_tab, "风险分析")

        # Tab 3: 持仓明细
        self._position_tab = QWidget()
        pos_layout = QVBoxLayout(self._position_tab)
        self._pos_table = QTableWidget()
        self._pos_table.setColumnCount(5)
        self._pos_table.setHorizontalHeaderLabels(["日期", "股票数", "总资产", "现金", "收益率"])
        self._pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._pos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._pos_table.setAlternatingRowColors(True)
        pos_layout.addWidget(self._pos_table)
        self._tabs.addTab(self._position_tab, "持仓明细")

        # Tab 4: 交易记录
        self._trade_tab = QWidget()
        trade_layout = QVBoxLayout(self._trade_tab)
        self._trade_table = QTableWidget()
        self._trade_table.setColumnCount(6)
        self._trade_table.setHorizontalHeaderLabels(["日期", "股票代码", "方向", "数量", "价格", "成本"])
        self._trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._trade_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._trade_table.setAlternatingRowColors(True)
        trade_layout.addWidget(self._trade_table)
        self._tabs.addTab(self._trade_tab, "交易记录")

    def display_results(self, report_normal: pd.DataFrame, positions_normal):
        """展示回测结果"""
        self._report = report_normal
        self._positions = positions_normal
        self._sim_btn.setEnabled(True)

        if report_normal is None or report_normal.empty:
            return

        # 收益曲线
        try:
            dates = report_normal.index
            if "return" in report_normal.columns:
                strategy_ret = report_normal["return"].cumsum()
            else:
                strategy_ret = pd.Series(0, index=dates)

            if "bench" in report_normal.columns:
                bench_ret = report_normal["bench"].cumsum()
            else:
                bench_ret = pd.Series(0, index=dates)

            excess_ret = strategy_ret - bench_ret
            self._return_chart.set_data(dates, strategy_ret.values, bench_ret.values, excess_ret.values)
        except Exception:
            pass

        # 风险指标
        try:
            from qlib.contrib.evaluate import risk_analysis
            if "return" in report_normal.columns:
                risk = risk_analysis(report_normal["return"])
                cards = self._metric_row._cards
                if len(cards) >= 5:
                    cards[0].set_value(f"{risk.loc['annualized_return', 'risk'] * 100:.2f}")
                    cards[1].set_value(f"{risk.loc['std', 'risk'] * 100:.2f}")
                    cards[2].set_value(f"{risk.loc['information_ratio', 'risk']:.4f}")
                    cards[3].set_value(f"{risk.loc['max_drawdown', 'risk'] * 100:.2f}")
                    turnover = report_normal.get("turnover", pd.Series(0))
                    cards[4].set_value(f"{turnover.mean() * 100:.2f}" if not turnover.empty else "--")
        except Exception:
            pass

        # 持仓明细
        try:
            if isinstance(positions_normal, dict):
                self._pos_table.setRowCount(min(len(positions_normal), 500))
                for row, (date, pos) in enumerate(list(positions_normal.items())[:500]):
                    if isinstance(pos, dict):
                        stock_count = len(pos)
                    else:
                        stock_count = getattr(pos, "count", 0)

                    self._pos_table.setItem(row, 0, QTableWidgetItem(str(date.date() if hasattr(date, 'date') else date)))
                    self._pos_table.setItem(row, 1, QTableWidgetItem(str(stock_count)))

                    if "account" in report_normal.columns:
                        val = report_normal.loc[date, "account"] if date in report_normal.index else "--"
                        self._pos_table.setItem(row, 2, QTableWidgetItem(f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)))

                    if "return" in report_normal.columns and date in report_normal.index:
                        ret = report_normal.loc[date, "return"]
                        self._pos_table.setItem(row, 4, QTableWidgetItem(f"{ret*100:.2f}%"))
        except Exception:
            pass

        # 交易记录 - 从 positions_normal 推导交易
        try:
            if isinstance(positions_normal, dict) and len(positions_normal) > 0:
                sorted_dates = sorted(positions_normal.keys())
                prev_stock_amounts = {}
                trades = []
                for date in sorted_dates:
                    cur_pos = positions_normal[date]
                    cur_stock_amounts = {}
                    if isinstance(cur_pos, dict):
                        cur_stock_amounts = {k: v for k, v in cur_pos.items()
                                             if isinstance(v, (int, float))}
                    elif hasattr(cur_pos, "stock_amount"):
                        cur_stock_amounts = dict(cur_pos.stock_amount)

                    all_stocks = set(prev_stock_amounts.keys()) | set(cur_stock_amounts.keys())
                    for stock_id in all_stocks:
                        prev_amt = prev_stock_amounts.get(stock_id, 0)
                        cur_amt = cur_stock_amounts.get(stock_id, 0)
                        delta = cur_amt - prev_amt
                        if delta != 0:
                            direction = "买入" if delta > 0 else "卖出"
                            trades.append({
                                "date": date,
                                "stock_id": stock_id,
                                "direction": direction,
                                "quantity": abs(delta),
                            })
                    prev_stock_amounts = cur_stock_amounts

                self._trade_table.setRowCount(min(len(trades), 500))
                for row, trade in enumerate(trades[:500]):
                    date = trade["date"]
                    self._trade_table.setItem(row, 0, QTableWidgetItem(
                        str(date.date() if hasattr(date, 'date') else date)))
                    self._trade_table.setItem(row, 1, QTableWidgetItem(str(trade["stock_id"])))
                    self._trade_table.setItem(row, 2, QTableWidgetItem(trade["direction"]))
                    self._trade_table.setItem(row, 3, QTableWidgetItem(str(trade["quantity"])))
                    self._trade_table.setItem(row, 4, QTableWidgetItem("--"))
                    # 成本
                    if date in report_normal.index and "cost" in report_normal.columns:
                        cost = report_normal.loc[date, "cost"]
                        self._trade_table.setItem(row, 5, QTableWidgetItem(
                            f"{cost:,.0f}" if isinstance(cost, (int, float)) else "--"))
                    else:
                        self._trade_table.setItem(row, 5, QTableWidgetItem("--"))
        except Exception:
            pass

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
        self._run_btn.setEnabled(len(trained_ids) > 0)

    def _on_model_changed(self, model_id: str):
        if model_id:
            self._run_btn.setEnabled(True)
            self.model_switch_requested.emit(model_id)

    def _on_start_backtest(self):
        model_id = self._model_combo.currentText()
        if model_id:
            self.backtest_requested.emit(model_id)
