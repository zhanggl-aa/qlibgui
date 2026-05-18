"""首页 - 仪表盘"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from qlib_gui.core.qlib_manager import QlibManager
from qlib_gui.core.model_registry import ModelRegistry, CATEGORY_NAMES


class HomePage(QWidget):
    goto_model = pyqtSignal()
    goto_simulation = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 欢迎标题
        title = QLabel("Qlib 量化投资平台")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        subtitle = QLabel("AI 驱动的量化研究、回测与模拟炒股平台")
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(subtitle)

        # 快捷操作
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        btn_model = QPushButton("选择模型并训练")
        btn_model.setMinimumHeight(60)
        btn_model.setFont(QFont("Microsoft YaHei", 12))
        btn_model.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_model.clicked.connect(self.goto_model.emit)
        btn_layout.addWidget(btn_model)

        btn_sim = QPushButton("模拟炒股")
        btn_sim.setMinimumHeight(60)
        btn_sim.setFont(QFont("Microsoft YaHei", 12))
        btn_sim.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        btn_sim.clicked.connect(self.goto_simulation.emit)
        btn_layout.addWidget(btn_sim)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 系统状态
        status_group = QGroupBox("系统状态")
        status_layout = QGridLayout(status_group)
        status_layout.setSpacing(12)

        self._status_labels = {}
        status_items = [
            ("qlib_status", "Qlib 状态"),
            ("data_path", "数据路径"),
            ("model_count", "已注册模型"),
            ("gpu_info", "GPU 信息"),
        ]
        for i, (key, label) in enumerate(status_items):
            lbl = QLabel(label + ":")
            lbl.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            val = QLabel("--")
            val.setFont(QFont("Microsoft YaHei", 10))
            status_layout.addWidget(lbl, i, 0)
            status_layout.addWidget(val, i, 1)
            self._status_labels[key] = val

        layout.addWidget(status_group)

        # 模型概览
        model_group = QGroupBox("模型概览")
        model_layout = QVBoxLayout(model_group)
        self._model_table = QTableWidget()
        self._model_table.setColumnCount(3)
        self._model_table.setHorizontalHeaderLabels(["分类", "模型", "类型"])
        self._model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._model_table.setAlternatingRowColors(True)
        model_layout.addWidget(self._model_table)
        layout.addWidget(model_group)

        layout.addStretch()
        self.refresh()

    def refresh(self):
        # 更新状态
        self._status_labels["qlib_status"].setText(
            "已初始化" if QlibManager.is_initialized() else "未初始化"
        )
        self._status_labels["data_path"].setText(QlibManager.get_provider_uri())

        models = ModelRegistry.discover_all()
        self._status_labels["model_count"].setText(f"{len(models)} 个")

        try:
            import torch
            if torch.cuda.is_available():
                self._status_labels["gpu_info"].setText(torch.cuda.get_device_name(0))
            else:
                self._status_labels["gpu_info"].setText("不可用（使用 CPU）")
        except ImportError:
            self._status_labels["gpu_info"].setText("未安装 PyTorch")

        # 填充模型表
        self._model_table.setRowCount(len(models))
        for row, (model_id, info) in enumerate(sorted(models.items())):
            self._model_table.setItem(row, 0, QTableWidgetItem(CATEGORY_NAMES.get(info.category, info.category)))
            self._model_table.setItem(row, 1, QTableWidgetItem(f"{info.chinese_name} ({model_id})"))
            self._model_table.setItem(row, 2, QTableWidgetItem(info.model_type))
