"""下单面板组件"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class OrderPanel(QWidget):
    """下单面板"""

    order_submitted = pyqtSignal(str, int, int)  # stock_id, amount, direction

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("手动下单")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # 股票代码
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("股票代码:"))
        self._stock_input = QLineEdit()
        self._stock_input.setPlaceholderText("如 SH600000")
        h1.addWidget(self._stock_input)
        layout.addLayout(h1)

        # 数量
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("数量(股):"))
        self._amount_spin = QSpinBox()
        self._amount_spin.setRange(100, 10000000)
        self._amount_spin.setValue(100)
        self._amount_spin.setSingleStep(100)
        h2.addWidget(self._amount_spin)
        layout.addLayout(h2)

        # 方向
        h3 = QHBoxLayout()
        self._btn_group = QButtonGroup(self)
        self._buy_radio = QRadioButton("买入")
        self._sell_radio = QRadioButton("卖出")
        self._buy_radio.setChecked(True)
        self._btn_group.addButton(self._buy_radio, 1)
        self._btn_group.addButton(self._sell_radio, -1)
        h3.addWidget(self._buy_radio)
        h3.addWidget(self._sell_radio)
        layout.addLayout(h3)

        # 下单按钮
        self._submit_btn = QPushButton("下单")
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self._submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(self._submit_btn)

        # 自动交易按钮
        self._auto_btn = QPushButton("自动交易一步")
        self._auto_btn.setStyleSheet("""
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
        layout.addWidget(self._auto_btn)

    def _on_submit(self):
        stock_id = self._stock_input.text().strip()
        if not stock_id:
            return
        amount = self._amount_spin.value()
        direction = self._btn_group.checkedId()
        self.order_submitted.emit(stock_id, amount, direction)

    def set_stock(self, stock_id: str):
        self._stock_input.setText(stock_id)
