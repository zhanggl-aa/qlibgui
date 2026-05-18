"""Qlib 量化投资平台 - 入口"""
import sys
import os
import traceback

# 确保项目根目录在 sys.path 中
_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_this_dir)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from qlib_gui.app import MainWindow


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """全局未捕获异常处理器"""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[FATAL] Unhandled exception:\n{tb_text}")

    try:
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication.instance()
        if app is not None:
            QMessageBox.critical(
                None, "程序错误",
                f"发生未捕获的异常:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"详细信息请查看控制台输出。"
            )
    except Exception:
        pass

    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    sys.excepthook = _global_exception_handler

    app = QApplication(sys.argv)

    # 全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 全局样式
    app.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QMenuBar { background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; padding: 2px; }
        QMenuBar::item:selected { background-color: #e9ecef; }
        QStatusBar { background-color: #f8f9fa; border-top: 1px solid #dee2e6; }
        QTabWidget::pane { border: 1px solid #dee2e6; border-radius: 4px; }
        QTabBar::tab { padding: 8px 16px; border: 1px solid #dee2e6; border-bottom: none;
                       border-top-left-radius: 4px; border-top-right-radius: 4px; background-color: #f8f9fa; }
        QTabBar::tab:selected { background-color: white; border-bottom: 2px solid #3498db; }
        QPushButton { padding: 6px 16px; border: 1px solid #dee2e6; border-radius: 4px; background-color: white; }
        QPushButton:hover { background-color: #e9ecef; }
        QPushButton:pressed { background-color: #dee2e6; }
        QPushButton:disabled { color: #adb5bd; background-color: #f8f9fa; }
        QGroupBox { font-weight: bold; border: 1px solid #dee2e6; border-radius: 6px;
                    margin-top: 12px; padding-top: 16px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; }
        QTableWidget { border: 1px solid #dee2e6; gridline-color: #e9ecef;
                       selection-background-color: #3498db; selection-color: white; }
        QTableWidget::item { padding: 4px; }
        QHeaderView::section { background-color: #f8f9fa; border: 1px solid #dee2e6;
                               padding: 6px; font-weight: bold; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #3498db; }
        QProgressBar { border: 1px solid #dee2e6; border-radius: 4px; text-align: center; height: 20px; }
        QProgressBar::chunk { background-color: #3498db; border-radius: 3px; }
        QScrollBar:vertical { width: 10px; }
        QScrollBar::handle:vertical { background: #ced4da; border-radius: 5px; min-height: 30px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
