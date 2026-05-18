"""持仓组合展示组件"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class PositionWidget(QWidget):
    """持仓展示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 账户摘要
        summary_group = QGroupBox("账户摘要")
        summary_layout = QGridLayout(summary_group)

        self._labels = {}
        items = [
            ("total", "总资产", 0, 0),
            ("cash", "可用现金", 0, 1),
            ("stock_value", "持仓市值", 1, 0),
            ("return_pct", "总收益率", 1, 1),
            ("positions_count", "持仓数量", 2, 0),
        ]
        for key, label, row, col in items:
            lbl = QLabel(label + ":")
            lbl.setFont(QFont("Microsoft YaHei", 9))
            val = QLabel("--")
            val.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
            summary_layout.addWidget(lbl, row, col * 2)
            summary_layout.addWidget(val, row, col * 2 + 1)
            self._labels[key] = val

        layout.addWidget(summary_group)

        # 持仓列表
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["股票代码", "数量", "成本价", "当前价"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def update_state(self, state: dict):
        """更新持仓状态"""
        # 更新摘要
        portfolio_value = state.get("portfolio_value", 0)
        cash = state.get("cash", 0)
        stock_value = state.get("stock_value", 0)
        return_pct = state.get("return_pct", 0)
        positions_count = state.get("positions_count", 0)

        self._labels["total"].setText(f"{portfolio_value:,.0f}")
        self._labels["cash"].setText(f"{cash:,.0f}")
        self._labels["stock_value"].setText(f"{stock_value:,.0f}")

        ret_text = f"{return_pct:.2f}%"
        color = "#e74c3c" if return_pct >= 0 else "#27ae60"
        self._labels["return_pct"].setText(ret_text)
        self._labels["return_pct"].setStyleSheet(f"color: {color};")
        self._labels["positions_count"].setText(str(positions_count))

        # 更新持仓表
        positions = state.get("positions", {})
        self._table.setRowCount(len(positions))
        for row, (stock_id, pos) in enumerate(positions.items()):
            self._table.setItem(row, 0, QTableWidgetItem(str(stock_id)))
            self._table.setItem(row, 1, QTableWidgetItem(str(pos.get("amount", 0))))
            self._table.setItem(row, 2, QTableWidgetItem(f"{pos.get('cost_price', 0):.2f}"))
            self._table.setItem(row, 3, QTableWidgetItem(f"{pos.get('current_price', 0):.2f}"))
