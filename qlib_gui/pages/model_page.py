"""模型选择页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QListWidget, QListWidgetItem, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QSpinBox, QDoubleSpinBox,
    QScrollArea, QDialog, QTextEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from qlib_gui.core.model_registry import ModelRegistry, CATEGORY_NAMES
from qlib_gui.core.config_parser import ConfigParser


class ModelPage(QWidget):
    model_selected = pyqtSignal(str)
    training_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_model_id = None
        self._current_config = {}
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 左侧: 模型列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)

        lbl = QLabel("选择模型")
        lbl.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        left_layout.addWidget(lbl)

        self._model_list = QListWidget()
        self._model_list.currentItemChanged.connect(self._on_model_changed)
        left_layout.addWidget(self._model_list)

        splitter.addWidget(left)

        # 右侧: 配置面板
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(16)

        # 模型信息
        self._info_group = QGroupBox("模型信息")
        info_layout = QVBoxLayout(self._info_group)
        self._info_label = QLabel("请从左侧选择一个模型")
        self._info_label.setWordWrap(True)
        self._info_label.setFont(QFont("Microsoft YaHei", 10))
        info_layout.addWidget(self._info_label)
        right_layout.addWidget(self._info_group)

        # 数据集选择
        self._dataset_group = QGroupBox("数据集配置")
        ds_layout = QVBoxLayout(self._dataset_group)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("特征集:"))
        self._dataset_combo = QComboBox()
        self._dataset_combo.addItems(["Alpha158", "Alpha360"])
        h1.addWidget(self._dataset_combo)
        ds_layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("市场:"))
        self._market_combo = QComboBox()
        self._market_combo.addItems(["csi300", "csi500"])
        h2.addWidget(self._market_combo)
        ds_layout.addLayout(h2)

        right_layout.addWidget(self._dataset_group)

        # 参数编辑器
        self._param_group = QGroupBox("模型参数")
        param_layout = QVBoxLayout(self._param_group)
        self._param_tree = QTreeWidget()
        self._param_tree.setHeaderLabels(["参数名", "参数值"])
        self._param_tree.setColumnWidth(0, 200)
        self._param_tree.setAlternatingRowColors(True)
        param_layout.addWidget(self._param_tree)
        right_layout.addWidget(self._param_group)

        # 回测配置
        self._bt_group = QGroupBox("回测配置")
        bt_layout = QVBoxLayout(self._bt_group)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("TopK:"))
        self._topk_spin = QSpinBox()
        self._topk_spin.setRange(1, 200)
        self._topk_spin.setValue(50)
        h3.addWidget(self._topk_spin)
        h3.addWidget(QLabel("N_drop:"))
        self._ndrop_spin = QSpinBox()
        self._ndrop_spin.setRange(1, 50)
        self._ndrop_spin.setValue(5)
        h3.addWidget(self._ndrop_spin)
        bt_layout.addLayout(h3)

        h4 = QHBoxLayout()
        h4.addWidget(QLabel("初始资金:"))
        self._account_spin = QDoubleSpinBox()
        self._account_spin.setRange(100000, 1e10)
        self._account_spin.setValue(100000000)
        self._account_spin.setDecimals(0)
        self._account_spin.setSingleStep(1000000)
        h4.addWidget(self._account_spin)
        bt_layout.addLayout(h4)

        right_layout.addWidget(self._bt_group)

        # 按钮
        btn_layout = QHBoxLayout()
        self._yaml_btn = QPushButton("预览 YAML")
        self._yaml_btn.clicked.connect(self._show_yaml_preview)
        btn_layout.addWidget(self._yaml_btn)

        self._train_btn = QPushButton("开始训练")
        self._train_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self._train_btn.clicked.connect(self._on_start_training)
        btn_layout.addWidget(self._train_btn)
        right_layout.addLayout(btn_layout)

        right_layout.addStretch()
        right_scroll.setWidget(right_widget)
        splitter.addWidget(right_scroll)

        splitter.setSizes([250, 700])

        self._populate_model_list()

    def _populate_model_list(self):
        models = ModelRegistry.discover_all()
        for category in ["tree", "neural", "advanced"]:
            cat_models = ModelRegistry.get_by_category(category)
            if not cat_models:
                continue
            cat_name = CATEGORY_NAMES.get(category, category)
            for info in sorted(cat_models, key=lambda x: x.model_id):
                item = QListWidgetItem(f"[{cat_name}] {info.chinese_name} ({info.model_id})")
                item.setData(Qt.ItemDataRole.UserRole, info.model_id)
                self._model_list.addItem(item)

    def _on_model_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            return
        model_id = current.data(Qt.ItemDataRole.UserRole)
        self._current_model_id = model_id
        info = ModelRegistry.get(model_id)

        self._info_label.setText(
            f"<b>{info.chinese_name}</b> ({info.model_id})<br>"
            f"类名: {info.class_name}<br>"
            f"模块: {info.module_path}<br>"
            f"类型: {info.model_type}<br>"
            f"可用数据集: {', '.join(info.available_datasets)}<br>"
            f"可用市场: {', '.join(info.available_markets)}"
        )

        # 更新数据集/市场选项
        self._dataset_combo.clear()
        self._dataset_combo.addItems(info.available_datasets or ["Alpha158", "Alpha360"])
        self._market_combo.clear()
        self._market_combo.addItems(info.available_markets or ["csi300", "csi500"])

        # 加载参数
        self._load_params(info)

        # 加载默认配置
        config_path = ModelRegistry.get_default_config_path(model_id)
        if config_path:
            self._current_config = ConfigParser.load_from_yaml(str(config_path))
        else:
            self._current_config = {}

        self.model_selected.emit(model_id)

    def _load_params(self, info: 'ModelInfo'):
        self._param_tree.clear()
        kwargs = info.default_kwargs
        if not kwargs:
            return

        for key, value in sorted(kwargs.items()):
            item = QTreeWidgetItem([str(key), str(value)])
            item.setData(0, Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._param_tree.addTopLevelItem(item)

    def _collect_params(self) -> dict:
        params = {}
        for i in range(self._param_tree.topLevelItemCount()):
            item = self._param_tree.topLevelItem(i)
            key = item.data(0, Qt.ItemDataRole.UserRole)
            value_str = item.text(1)
            # 尝试类型转换
            try:
                if "." in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                if value_str.lower() == "true":
                    value = True
                elif value_str.lower() == "false":
                    value = False
                elif value_str.lower() == "none":
                    value = None
                else:
                    value = value_str
            params[key] = value
        return params

    def _show_yaml_preview(self):
        if not self._current_model_id:
            QMessageBox.information(self, "提示", "请先选择一个模型")
            return

        import yaml
        info = ModelRegistry.get(self._current_model_id)

        # 如果有默认配置，显示默认配置；否则动态构建
        if self._current_config:
            config = self._current_config
        else:
            # 根据数据集选择 handler
            dataset_choice = self._dataset_combo.currentText()
            if dataset_choice == "Alpha158":
                handler_class = "Alpha158"
            else:
                handler_class = "Alpha360"

            # 构建完整配置
            config = ConfigParser.build_full_config(
                model_id=self._current_model_id,
                model_class=info.class_name,
                model_module=info.module_path,
                model_kwargs=self._collect_params(),
                handler_class=handler_class,
                handler_module="qlib.contrib.data.handler",
                handler_kwargs={
                    "start_time": "2008-01-01",
                    "end_time": "2020-08-01",
                    "fit_start_time": "2008-01-01",
                    "fit_end_time": "2014-12-31",
                    "instruments": self._market_combo.currentText(),
                },
                segments={
                    "train": ["2008-01-01", "2014-12-31"],
                    "valid": ["2015-01-01", "2016-12-31"],
                    "test": ["2017-01-01", "2020-08-01"],
                },
                market=self._market_combo.currentText(),
                benchmark="SH000300",
                topk=self._topk_spin.value(),
                n_drop=self._ndrop_spin.value(),
                account=self._account_spin.value(),
            )

        text = yaml.dump(config, allow_unicode=True, default_flow_style=False)
        dlg = QDialog(self)
        dlg.setWindowTitle("YAML 配置预览")
        dlg.resize(600, 500)
        layout = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setFont(QFont("Consolas", 10))
        te.setPlainText(text)
        layout.addWidget(te)
        dlg.exec()

    def _on_start_training(self):
        if not self._current_model_id:
            QMessageBox.warning(self, "提示", "请先选择一个模型")
            return

        info = ModelRegistry.get(self._current_model_id)
        config = {
            "model_id": self._current_model_id,
            "model_kwargs": self._collect_params(),
            "dataset": self._dataset_combo.currentText(),
            "market": self._market_combo.currentText(),
            "topk": self._topk_spin.value(),
            "n_drop": self._ndrop_spin.value(),
            "account": self._account_spin.value(),
            "start_time": "2008-01-01",
            "end_time": "2020-08-01",
        }
        self.training_requested.emit(config)
