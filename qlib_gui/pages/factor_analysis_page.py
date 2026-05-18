"""因子分析页面 - 进行因子表现分析和因子暴露分析"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QComboBox, QCheckBox, QSplitter, QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import pandas as pd
import numpy as np

from qlib_gui.widgets.chart_widget import RealtimeChart


class FactorAnalysisPage(QWidget):
    # 因子分析信号
    factor_analysis_requested = pyqtSignal(dict)
    factor_export_requested = pyqtSignal(str, pd.DataFrame)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_model_id = None
        self._factor_data = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("因子分析")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.addWidget(title)

        header.addWidget(QLabel("选择模型:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self._model_combo)

        header.addStretch()

        self._analyze_btn = QPushButton("分析因子")
        self._analyze_btn.setStyleSheet("""
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
        self._analyze_btn.clicked.connect(self._on_analyze_factors)
        header.addWidget(self._analyze_btn)

        self._export_btn = QPushButton("导出报告")
        self._export_btn.clicked.connect(self._on_export_report)
        header.addWidget(self._export_btn)

        layout.addLayout(header)

        # 主内容区域 - 标签页
        self._tabs = QTabWidget()

        # 标签页1: 因子重要性
        self._importance_tab = QWidget()
        importance_layout = QVBoxLayout(self._importance_tab)

        importance_chart_group = QGroupBox("因子重要性排序")
        chart_layout = QVBoxLayout(importance_chart_group)
        self._importance_chart = RealtimeChart("因子重要性", "排名", "重要性")
        self._importance_chart.add_series("因子重要性", "#3498db")
        chart_layout.addWidget(self._importance_chart)
        importance_layout.addWidget(importance_chart_group)

        importance_table_group = QGroupBox("详细数据")
        table_layout = QVBoxLayout(importance_table_group)
        self._importance_table = QTableWidget()
        self._importance_table.setAlternatingRowColors(True)
        self._importance_table.setColumnCount(4)
        self._importance_table.setHorizontalHeaderLabels(["排名", "因子名", "重要性", "累计贡献"])
        table_layout.addWidget(self._importance_table)
        importance_layout.addWidget(importance_table_group)

        self._tabs.addTab(self._importance_tab, "因子重要性")

        # 标签页2: 因子暴露
        self._exposure_tab = QWidget()
        exposure_layout = QVBoxLayout(self._exposure_tab)

        exposure_chart_group = QGroupBox("因子暴露热图")
        exposure_chart_layout = QVBoxLayout(exposure_chart_group)
        self._exposure_chart = RealtimeChart("因子暴露", "日期", "暴露值")
        self._exposure_chart.add_series("市场", "#3498db")
        self._exposure_chart.add_series("市值", "#2ecc71")
        self._exposure_chart.add_series("动量", "#e74c3c")
        self._exposure_chart.add_series("价值", "#f39c12")
        self._exposure_chart.add_series("盈利", "#9b59b6")
        exposure_chart_layout.addWidget(self._exposure_chart)
        exposure_layout.addWidget(exposure_chart_group)

        self._tabs.addTab(self._exposure_tab, "因子暴露")

        # 标签页3: 因子相关性
        self._correlation_tab = QWidget()
        correlation_layout = QVBoxLayout(self._correlation_tab)

        correlation_chart_group = QGroupBox("因子相关性矩阵")
        corr_chart_layout = QVBoxLayout(correlation_chart_group)
        self._correlation_chart = RealtimeChart("因子相关性", "因子", "相关系数")
        corr_chart_layout.addWidget(self._correlation_chart)
        correlation_layout.addWidget(correlation_chart_group)

        correlation_table_group = QGroupBox("相关系数表")
        corr_table_layout = QVBoxLayout(correlation_table_group)
        self._correlation_table = QTableWidget()
        self._correlation_table.setAlternatingRowColors(True)
        corr_table_layout.addWidget(self._correlation_table)
        correlation_layout.addWidget(correlation_table_group)

        self._tabs.addTab(self._correlation_tab, "因子相关性")

        # 标签页4: 风险因子分析
        self._risk_tab = QWidget()
        risk_layout = QVBoxLayout(self._risk_tab)

        risk_chart_group = QGroupBox("风险贡献分析")
        risk_chart_layout = QVBoxLayout(risk_chart_group)
        self._risk_chart = RealtimeChart("风险贡献", "因子", "贡献度 %")
        risk_chart_layout.addWidget(self._risk_chart)
        risk_layout.addWidget(risk_chart_group)

        risk_stats_group = QGroupBox("风险统计")
        risk_stats_layout = QVBoxLayout(risk_stats_group)
        self._risk_table = QTableWidget()
        self._risk_table.setAlternatingRowColors(True)
        self._risk_table.setColumnCount(4)
        self._risk_table.setHorizontalHeaderLabels(["因子", "波动率", "VaR(95%)", "最大回撤"])
        risk_stats_layout.addWidget(self._risk_table)
        risk_layout.addWidget(risk_stats_group)

        self._tabs.addTab(self._risk_tab, "风险因子分析")

        layout.addWidget(self._tabs)

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

    def _on_analyze_factors(self):
        if not self._current_model_id:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先选择模型")
            return

        # 发送因子分析请求
        config = {
            "model_id": self._current_model_id,
            "task": "factor_analysis"
        }
        self.factor_analysis_requested.emit(config)

    def display_factor_analysis(self, factor_data):
        """显示因子分析结果"""
        self._factor_data = factor_data

        # 因子重要性
        if "importance" in factor_data:
            importance = factor_data["importance"]
            self._display_importance(importance)

        # 因子暴露
        if "exposure" in factor_data:
            exposure = factor_data["exposure"]
            self._display_exposure(exposure)

        # 因子相关性
        if "correlation" in factor_data:
            corr = factor_data["correlation"]
            self._display_correlation(corr)

        # 风险分析
        if "risk" in factor_data:
            risk = factor_data["risk"]
            self._display_risk(risk)

    def _display_importance(self, importance):
        """显示因子重要性"""
        self._importance_table.setRowCount(len(importance))

        # 数据可视化
        x_values = list(range(len(importance)))
        y_values = list(importance.values())
        self._importance_chart.set_data("因子重要性", x_values, y_values)

        # 表格展示
        cumulative = 0.0
        for i, (factor, score) in enumerate(sorted(importance.items(), key=lambda x: -x[1])):
            cumulative += score
            self._importance_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self._importance_table.setItem(i, 1, QTableWidgetItem(factor))
            self._importance_table.setItem(i, 2, QTableWidgetItem(f"{score:.4f}"))
            self._importance_table.setItem(i, 3, QTableWidgetItem(f"{cumulative:.2%}"))

    def _display_exposure(self, exposure):
        """显示因子暴露"""
        if isinstance(exposure, pd.DataFrame):
            dates = exposure.index.tolist()
            for factor in exposure.columns:
                values = exposure[factor].tolist()
                if factor in ["市场", "市值", "动量", "价值", "盈利"]:
                    self._exposure_chart.set_data(factor, dates, values)

    def _display_correlation(self, correlation):
        """显示因子相关性"""
        if isinstance(correlation, pd.DataFrame):
            self._correlation_table.setRowCount(len(correlation))
            self._correlation_table.setColumnCount(len(correlation.columns) + 1)

            # 设置表头
            headers = [""] + list(correlation.columns)
            self._correlation_table.setHorizontalHeaderLabels(headers)

            for i, factor in enumerate(correlation.index):
                self._correlation_table.setItem(i, 0, QTableWidgetItem(factor))
                for j, col in enumerate(correlation.columns):
                    val = correlation.loc[factor, col]
                    self._correlation_table.setItem(i, j+1, QTableWidgetItem(f"{val:.4f}"))

    def _display_risk(self, risk):
        """显示风险分析"""
        self._risk_table.setRowCount(len(risk))

        for i, (factor, stats) in enumerate(risk.items()):
            self._risk_table.setItem(i, 0, QTableWidgetItem(factor))
            self._risk_table.setItem(i, 1, QTableWidgetItem(f"{stats.get('volatility', 0):.2%}"))
            self._risk_table.setItem(i, 2, QTableWidgetItem(f"{stats.get('var95', 0):.2%}"))
            self._risk_table.setItem(i, 3, QTableWidgetItem(f"{stats.get('max_drawdown', 0):.2%}"))

    def _on_export_report(self):
        """导出因子分析报告"""
        if self._factor_data is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先运行因子分析")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存因子分析报告", "", "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)"
        )

        if file_path:
            try:
                if file_path.endswith(".xlsx"):
                    import pandas as pd
                    with pd.ExcelWriter(file_path) as writer:
                        if "importance" in self._factor_data:
                            pd.DataFrame({
                                "因子": list(self._factor_data["importance"].keys()),
                                "重要性": list(self._factor_data["importance"].values())
                            }).to_excel(writer, "因子重要性", index=False)

                        if "correlation" in self._factor_data:
                            self._factor_data["correlation"].to_excel(writer, "因子相关性")

                        if "risk" in self._factor_data:
                            pd.DataFrame(self._factor_data["risk"]).T.to_excel(writer, "风险分析")

                self.factor_export_requested.emit(file_path, self._factor_data)

            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
