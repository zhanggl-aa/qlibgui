"""KPI 指标卡片组件"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MetricCard(QWidget):
    """单个指标卡片"""

    def __init__(self, title: str = "", value: str = "--", unit: str = "",
                 color: str = "#2c3e50", parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._unit = unit
        self._color = color
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Microsoft YaHei", 9))
        self._title_label.setStyleSheet("color: #7f8c8d;")

        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._color};")

        self._unit_label = QLabel(self._unit)
        self._unit_label.setFont(QFont("Microsoft YaHei", 9))
        self._unit_label.setStyleSheet("color: #95a5a6;")

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._unit_label)

        self.setStyleSheet("""
            MetricCard {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

    def set_value(self, value: str, color: str = None):
        self._value = value
        self._value_label.setText(value)
        if color:
            self._value_label.setStyleSheet(f"color: {color};")


class MetricRow(QWidget):
    """一行指标卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._cards = []

    def add_card(self, title: str, value: str = "--", unit: str = "",
                 color: str = "#2c3e50") -> MetricCard:
        card = MetricCard(title, value, unit, color)
        self._layout.addWidget(card)
        self._cards.append(card)
        return card

    def set_values(self, values: dict):
        for card in self._cards:
            if card._title in values:
                card.set_value(str(values[card._title]))
