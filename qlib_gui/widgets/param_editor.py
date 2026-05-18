"""参数编辑器组件"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt


class ParamEditor(QWidget):
    """基于 QTreeWidget 的参数编辑器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["参数名", "参数值"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree)

    def load_params(self, params: dict):
        """加载参数字典"""
        self._tree.clear()
        for key, value in sorted(params.items()):
            item = QTreeWidgetItem([str(key), str(value)])
            item.setData(0, Qt.ItemDataRole.UserRole, key)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, type(value).__name__)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._tree.addTopLevelItem(item)

    def collect_params(self) -> dict:
        """收集编辑后的参数"""
        params = {}
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            key = item.data(0, Qt.ItemDataRole.UserRole)
            value_str = item.text(1)
            original_type = item.data(0, Qt.ItemDataRole.UserRole + 1)

            try:
                if original_type == "int":
                    value = int(value_str)
                elif original_type == "float":
                    value = float(value_str)
                elif original_type == "bool":
                    value = value_str.lower() in ("true", "1", "yes")
                elif original_type == "NoneType":
                    value = None
                else:
                    value = value_str
            except (ValueError, TypeError):
                value = value_str
            params[key] = value
        return params

    def clear(self):
        self._tree.clear()
