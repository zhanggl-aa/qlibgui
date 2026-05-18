"""导航侧边栏"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


NAV_ITEMS = [
    ("home", "首页"),
    ("model", "模型选择"),
    ("training", "训练"),
    ("backtest", "回测"),
    ("simulation", "模拟炒股"),
    ("experiment", "实验记录"),
    ("factor_analysis", "因子分析"),
    ("portfolio_optimization", "组合优化"),
]


class Sidebar(QWidget):
    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self._buttons = {}
        self._current = "home"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        title = QLabel("Qlib 量化平台")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 8px;")
        layout.addWidget(title)

        layout.addSpacing(16)

        for page_id, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName(page_id)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setFont(QFont("Microsoft YaHei", 11))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self._status_label = QLabel("状态: 就绪")
        self._status_label.setFont(QFont("Microsoft YaHei", 9))
        self._status_label.setStyleSheet("color: #7f8c8d; padding: 4px;")
        layout.addWidget(self._status_label)

        self._update_style()

    def _on_click(self, page_id: str):
        self.set_current_page(page_id)
        self.page_changed.emit(page_id)

    def set_current_page(self, page_id: str):
        self._current = page_id
        for pid, btn in self._buttons.items():
            btn.setChecked(pid == page_id)

    def set_status(self, text: str):
        self._status_label.setText(f"状态: {text}")

    def _update_style(self):
        self.setStyleSheet("""
            Sidebar {
                background-color: #ecf0f1;
                border-right: 1px solid #bdc3c7;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                text-align: left;
                color: #2c3e50;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
        """)

    def set_page_enabled(self, page_id: str, enabled: bool):
        btn = self._buttons.get(page_id)
        if btn:
            btn.setEnabled(enabled)
            btn.setStyleSheet(
                "" if enabled else "color: #bdc3c7; background-color: transparent;"
            )
