"""股票信号/持仓表格组件"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import pandas as pd


class StockTable(QWidget):
    """股票列表表格"""

    def __init__(self, title: str = "股票列表", parent=None):
        super().__init__(parent)
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["排名", "股票代码", "预测分数", "涨跌幅", "持仓量"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

    def update_signals(self, signals: pd.Series, positions: dict = None):
        """更新信号列表"""
        if positions is None:
            positions = {}
        self._table.setRowCount(min(len(signals), 100))

        for row, (stock_id, score) in enumerate(signals.head(100).items()):
            self._table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self._table.setItem(row, 1, QTableWidgetItem(str(stock_id)))

            score_item = QTableWidgetItem(f"{score:.4f}")
            if score > 0:
                score_item.setForeground(QColor("#e74c3c"))
            else:
                score_item.setForeground(QColor("#27ae60"))
            self._table.setItem(row, 2, score_item)

            self._table.setItem(row, 3, QTableWidgetItem("--"))

            held = positions.get(stock_id, {})
            amount = held.get("amount", 0)
            self._table.setItem(row, 4, QTableWidgetItem(str(amount) if amount > 0 else ""))

    def update_positions(self, positions: dict):
        """更新持仓列表"""
        self._table.setRowCount(len(positions))
        for row, (stock_id, pos) in enumerate(positions.items()):
            self._table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self._table.setItem(row, 1, QTableWidgetItem(str(stock_id)))
            self._table.setItem(row, 2, QTableWidgetItem("--"))
            self._table.setItem(row, 3, QTableWidgetItem("--"))
            self._table.setItem(row, 4, QTableWidgetItem(str(pos.get("amount", 0))))

    def clear(self):
        self._table.setRowCount(0)
