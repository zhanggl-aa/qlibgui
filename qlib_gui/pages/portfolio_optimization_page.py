"""投资组合优化页面 - 基于现代投资组合理论进行资产配置优化"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import pandas as pd
import numpy as np

from qlib_gui.widgets.chart_widget import RealtimeChart


class PortfolioOptimizationPage(QWidget):
    # 信号
    optimization_requested = pyqtSignal(dict)
    portfolio_export_requested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_model_id = None
        self._optimization_result = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("投资组合优化")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.addWidget(title)

        header.addWidget(QLabel("模型:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self._model_combo)

        header.addStretch()

        self._optimize_btn = QPushButton("优化组合")
        self._optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        self._optimize_btn.clicked.connect(self._on_optimize)
        header.addWidget(self._optimize_btn)

        self._export_btn = QPushButton("导出组合")
        self._export_btn.clicked.connect(self._on_export_portfolio)
        header.addWidget(self._export_btn)

        layout.addLayout(header)

        # 主内容 - 左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧: 配置参数
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 优化目标配置
        objective_group = QGroupBox("优化目标")
        objective_layout = QVBoxLayout(objective_group)

        self._objective_combo = QComboBox()
        self._objective_combo.addItems([
            "最小方差组合",
            "最大夏普比率",
            "最大化收益",
            "效用函数",
            "风险平价"
        ])
        objective_layout.addWidget(self._objective_combo)

        left_layout.addWidget(objective_group)

        # 约束条件配置
        constraints_group = QGroupBox("约束条件")
        constraints_layout = QVBoxLayout(constraints_group)

        # 单个资产最大权重
        max_weight_layout = QHBoxLayout()
        max_weight_layout.addWidget(QLabel("单资产最大权重:"))
        self._max_weight_spin = QDoubleSpinBox()
        self._max_weight_spin.setRange(0.01, 1.0)
        self._max_weight_spin.setValue(0.1)
        self._max_weight_spin.setDecimals(2)
        self._max_weight_spin.setSingleStep(0.01)
        max_weight_layout.addWidget(self._max_weight_spin)
        constraints_layout.addLayout(max_weight_layout)

        # 单个资产最小权重
        min_weight_layout = QHBoxLayout()
        min_weight_layout.addWidget(QLabel("单资产最小权重:"))
        self._min_weight_spin = QDoubleSpinBox()
        self._min_weight_spin.setRange(0, 0.5)
        self._min_weight_spin.setValue(0)
        self._min_weight_spin.setDecimals(2)
        self._min_weight_spin.setSingleStep(0.01)
        min_weight_layout.addWidget(self._min_weight_spin)
        constraints_layout.addLayout(min_weight_layout)

        # 目标收益率
        target_return_layout = QHBoxLayout()
        target_return_layout.addWidget(QLabel("目标收益率:"))
        self._target_return_spin = QDoubleSpinBox()
        self._target_return_spin.setRange(-0.5, 1.0)
        self._target_return_spin.setValue(0.15)
        self._target_return_spin.setDecimals(4)
        self._target_return_spin.setSingleStep(0.01)
        target_return_layout.addWidget(self._target_return_spin)
        constraints_layout.addLayout(target_return_layout)

        # 最大波动率约束
        max_vol_layout = QHBoxLayout()
        max_vol_layout.addWidget(QLabel("最大波动率:"))
        self._max_vol_spin = QDoubleSpinBox()
        self._max_vol_spin.setRange(0.01, 1.0)
        self._max_vol_spin.setValue(0.25)
        self._max_vol_spin.setDecimals(4)
        self._max_vol_spin.setSingleStep(0.01)
        max_vol_layout.addWidget(self._max_vol_spin)
        constraints_layout.addLayout(max_vol_layout)

        left_layout.addWidget(constraints_group)

        # 股票池配置
        universe_group = QGroupBox("股票池")
        universe_layout = QVBoxLayout(universe_group)

        self._universe_combo = QComboBox()
        self._universe_combo.addItems(["CSI300", "CSI500", "CSI800", "全市场"])
        universe_layout.addWidget(self._universe_combo)

        universe_layout.addWidget(QLabel("选择股票数量:"))
        self._stock_count_spin = QSpinBox()
        self._stock_count_spin.setRange(10, 500)
        self._stock_count_spin.setValue(50)
        universe_layout.addWidget(self._stock_count_spin)

        left_layout.addWidget(universe_group)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # 右侧: 优化结果
        right_widget = QTabWidget()

        # 标签页1: 组合权重
        weights_tab = QWidget()
        weights_layout = QVBoxLayout(weights_tab)

        weights_chart_group = QGroupBox("组合权重")
        weights_chart_layout = QVBoxLayout(weights_chart_group)
        self._weights_chart = RealtimeChart("组合权重", "股票", "权重 %")
        weights_chart_layout.addWidget(self._weights_chart)
        weights_layout.addWidget(weights_chart_group)

        weights_table_group = QGroupBox("详细权重")
        weights_table_layout = QVBoxLayout(weights_table_group)
        self._weights_table = QTableWidget()
        self._weights_table.setAlternatingRowColors(True)
        self._weights_table.setColumnCount(4)
        self._weights_table.setHorizontalHeaderLabels(["股票代码", "权重", "预期收益", "预期风险"])
        weights_table_layout.addWidget(self._weights_table)
        weights_layout.addWidget(weights_table_group)

        right_widget.addTab(weights_tab, "组合权重")

        # 标签页2: 有效前沿
        frontier_tab = QWidget()
        frontier_layout = QVBoxLayout(frontier_tab)

        frontier_chart_group = QGroupBox("有效前沿")
        frontier_chart_layout = QVBoxLayout(frontier_chart_group)
        self._frontier_chart = RealtimeChart("有效前沿", "风险(波动率)", "收益")
        self._frontier_chart.add_series("有效前沿", "#3498db")
        self._frontier_chart.add_series("当前组合", "#e74c3c")
        frontier_chart_layout.addWidget(self._frontier_chart)
        frontier_layout.addWidget(frontier_chart_group)

        frontier_stats_group = QGroupBox("组合统计")
        frontier_stats_layout = QVBoxLayout(frontier_stats_group)
        self._frontier_stats = QTableWidget()
        self._frontier_stats.setAlternatingRowColors(True)
        self._frontier_stats.setColumnCount(2)
        self._frontier_stats.setHorizontalHeaderLabels(["指标", "数值"])
        frontier_stats_layout.addWidget(self._frontier_stats)
        frontier_layout.addWidget(frontier_stats_group)

        right_widget.addTab(frontier_tab, "有效前沿")

        # 标签页3: 回测表现
        backtest_tab = QWidget()
        backtest_layout = QVBoxLayout(backtest_tab)

        backtest_chart_group = QGroupBox("组合回测表现")
        backtest_chart_layout = QVBoxLayout(backtest_chart_group)
        self._portfolio_chart = RealtimeChart("组合表现", "日期", "净值")
        self._portfolio_chart.add_series("优化组合", "#3498db")
        self._portfolio_chart.add_series("基准(CSI300)", "#2ecc71")
        backtest_chart_layout.addWidget(self._portfolio_chart)
        backtest_layout.addWidget(backtest_chart_group)

        right_widget.addTab(backtest_tab, "回测表现")

        # 标签页4: 风险分析
        risk_tab = QWidget()
        risk_layout = QVBoxLayout(risk_tab)

        risk_chart_group = QGroupBox("风险分解")
        risk_chart_layout = QVBoxLayout(risk_chart_group)
        self._risk_chart = RealtimeChart("风险分解", "风险因子", "贡献度 %")
        risk_chart_layout.addWidget(self._risk_chart)
        risk_layout.addWidget(risk_chart_group)

        right_widget.addTab(risk_tab, "风险分析")

        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def update_model_list(self, model_ids, current_model_id=None):
        """更新模型下拉框"""
        self._model_combo.blockSignals(True)
        self._model_combo.clear()
        self._model_combo.addItems(model_ids)
        if current_model_id:
            idx = self._model_combo.findText(current_model_id)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
        self._model_combo.blockSignals(False)

    def _on_model_changed(self, model_id):
        self._current_model_id = model_id

    def _on_optimize(self):
        """执行优化"""
        if not self._current_model_id:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先选择模型")
            return

        config = {
            "model_id": self._current_model_id,
            "objective": self._objective_combo.currentText(),
            "max_weight": self._max_weight_spin.value(),
            "min_weight": self._min_weight_spin.value(),
            "target_return": self._target_return_spin.value(),
            "max_volatility": self._max_vol_spin.value(),
            "stock_count": self._stock_count_spin.value(),
            "universe": self._universe_combo.currentText()
        }

        self.optimization_requested.emit(config)

    def display_optimization_result(self, result):
        """显示优化结果"""
        self._optimization_result = result

        # 组合权重
        if "weights" in result:
            self._display_weights(result["weights"])

        # 有效前沿
        if "frontier" in result:
            self._display_frontier(result["frontier"])

        # 回测表现
        if "backtest" in result:
            self._display_backtest(result["backtest"])

        # 风险分析
        if "risk_decomposition" in result:
            self._display_risk(result["risk_decomposition"])

        # 统计数据
        if "stats" in result:
            self._display_stats(result["stats"])

    def _display_weights(self, weights):
        """显示组合权重"""
        self._weights_table.setRowCount(len(weights))

        # 图表数据
        labels = list(weights.keys())[:30]
        values = [w * 100 for w in list(weights.values())[:30]]
        self._weights_chart.set_data("组合权重", list(range(len(labels))), values)
        self._weights_chart.x_labels = labels

        # 表格数据
        for i, (stock, weight) in enumerate(weights.items()):
            self._weights_table.setItem(i, 0, QTableWidgetItem(stock))
            self._weights_table.setItem(i, 1, QTableWidgetItem(f"{weight:.2%}"))
            # 预期收益和风险可以在后续添加
            self._weights_table.setItem(i, 2, QTableWidgetItem("-"))
            self._weights_table.setItem(i, 3, QTableWidgetItem("-"))

    def _display_frontier(self, frontier):
        """显示有效前沿"""
        risks = frontier.get("risks", [])
        returns = frontier.get("returns", [])

        self._frontier_chart.set_data("有效前沿", risks, returns)

        # 最优组合点
        if "optimal" in frontier:
            optimal = frontier["optimal"]
            self._frontier_chart.set_data("当前组合", [optimal["risk"]], [optimal["return"]])

    def _display_backtest(self, backtest):
        """显示回测表现"""
        dates = backtest.get("dates", [])
        portfolio_values = backtest.get("portfolio", [])
        benchmark_values = backtest.get("benchmark", [])

        if dates and portfolio_values:
            self._portfolio_chart.set_data("优化组合", dates, portfolio_values)
        if dates and benchmark_values:
            self._portfolio_chart.set_data("基准(CSI300)", dates, benchmark_values)

    def _display_risk(self, risk_decomp):
        """显示风险分解"""
        factors = list(risk_decomp.keys())
        contributions = [v * 100 for v in risk_decomp.values()]
        self._risk_chart.set_data("风险贡献", list(range(len(factors))), contributions)
        self._risk_chart.x_labels = factors

    def _display_stats(self, stats):
        """显示统计数据"""
        self._frontier_stats.setRowCount(len(stats))

        for i, (key, value) in enumerate(stats.items()):
            self._frontier_stats.setItem(i, 0, QTableWidgetItem(key))
            if isinstance(value, float):
                if abs(value) > 1:
                    self._frontier_stats.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                else:
                    self._frontier_stats.setItem(i, 1, QTableWidgetItem(f"{value:.2%}"))
            else:
                self._frontier_stats.setItem(i, 1, QTableWidgetItem(str(value)))

    def _on_export_portfolio(self):
        """导出投资组合"""
        if self._optimization_result is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先生成优化组合")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存投资组合", "", "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)"
        )

        if file_path:
            try:
                self.portfolio_export_requested.emit(file_path, self._optimization_result)

                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "成功", "投资组合已成功导出！")

            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
