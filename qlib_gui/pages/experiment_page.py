"""实验历史页"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from qlib_gui.widgets.chart_widget import RealtimeChart


class ExperimentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("实验记录")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 实验列表
        list_group = QGroupBox("历史实验")
        list_layout = QVBoxLayout(list_group)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh)
        btn_row.addWidget(refresh_btn)

        compare_btn = QPushButton("对比选中实验")
        compare_btn.clicked.connect(self._compare)
        btn_row.addWidget(compare_btn)

        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)

        self._exp_table = QTableWidget()
        self._exp_table.setColumnCount(6)
        self._exp_table.setHorizontalHeaderLabels(["实验名称", "记录ID", "模型", "数据集", "最佳评分", "创建时间"])
        self._exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._exp_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._exp_table.setAlternatingRowColors(True)
        self._exp_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._exp_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_layout.addWidget(self._exp_table)

        layout.addWidget(list_group)

        # 对比图表
        self._compare_chart = RealtimeChart("实验对比 - 验证评分", "Epoch", "Score")
        layout.addWidget(self._compare_chart)

        self._refresh()

    def _refresh(self):
        """刷新实验列表"""
        self._exp_table.setRowCount(0)
        try:
            from qlib.workflow import R
            from qlib.workflow.recorder import Recorder

            exp_manager = R.session
            if exp_manager is None:
                return

            experiments = exp_manager.list_experiments()
            row = 0
            for exp_name, exp in experiments.items():
                try:
                    recorders = exp.list_recorders()
                    for rec_id, rec in recorders.items():
                        self._exp_table.insertRow(row)
                        self._exp_table.setItem(row, 0, QTableWidgetItem(str(exp_name)))
                        self._exp_table.setItem(row, 1, QTableWidgetItem(str(rec_id)))
                        params = rec.load_object("params") if rec.exists("params") else {}
                        self._exp_table.setItem(row, 2, QTableWidgetItem(str(params.get("model_id", "--"))))
                        self._exp_table.setItem(row, 3, QTableWidgetItem(str(params.get("dataset", "--"))))
                        # 提取最佳评分
                        best_score_str = "--"
                        try:
                            if rec.exists("evals_result"):
                                evals_result = rec.load_object("evals_result")
                                if isinstance(evals_result, dict):
                                    valid_scores = evals_result.get("valid", [])
                                    if valid_scores:
                                        best_score_str = f"{max(valid_scores):.6f}"
                            if best_score_str == "--" and rec.exists("metric"):
                                metric = rec.load_object("metric")
                                if isinstance(metric, dict):
                                    for key in ["ic", "1d_ic", "val_score", "best_score"]:
                                        if key in metric and isinstance(metric[key], (int, float)):
                                            best_score_str = f"{metric[key]:.6f}"
                                            break
                        except Exception:
                            pass
                        self._exp_table.setItem(row, 4, QTableWidgetItem(best_score_str))
                        self._exp_table.setItem(row, 5, QTableWidgetItem(str(rec.datetime) if hasattr(rec, 'datetime') else "--"))
                        row += 1
                except Exception:
                    continue
        except Exception:
            pass

    def _compare(self):
        """对比选中实验"""
        selected = self._exp_table.selectionModel().selectedRows()
        if len(selected) < 2:
            QMessageBox.information(self, "提示", "请至少选择两个实验进行对比")
            return

        self._compare_chart.clear_all()
        colors = ["#3498db", "#e74c3c", "#27ae60", "#f39c12", "#9b59b6", "#1abc9c"]

        for i, idx in enumerate(selected):
            row = idx.row()
            exp_name = self._exp_table.item(row, 0).text()
            rec_id = self._exp_table.item(row, 1).text()
            color = colors[i % len(colors)]
            series_name = f"{exp_name}/{rec_id[:6]}"

            self._compare_chart.add_series(series_name, color)

            try:
                from qlib.workflow import R
                exp = R.session.get_exp(experiment_name=exp_name)
                if exp is None:
                    continue
                rec = exp.get_recorder(recorder_id=rec_id)
                if rec is None:
                    continue

                evals_result = rec.load_object("evals_result") if rec.exists("evals_result") else None
                if evals_result and isinstance(evals_result, dict):
                    valid_scores = evals_result.get("valid", [])
                    if valid_scores:
                        x = list(range(len(valid_scores)))
                        self._compare_chart.set_data(series_name, x, valid_scores)
            except Exception:
                continue

    def _delete_selected(self):
        """删除选中实验"""
        selected = self._exp_table.selectionModel().selectedRows()
        if not selected:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {len(selected)} 个实验记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from qlib.workflow import R
                for idx in selected:
                    row = idx.row()
                    exp_name = self._exp_table.item(row, 0).text()
                    rec_id = self._exp_table.item(row, 1).text()
                    try:
                        exp = R.session.get_exp(experiment_name=exp_name)
                        if exp is not None:
                            rec = exp.get_recorder(recorder_id=rec_id)
                            if rec is not None:
                                rec.rm()
                    except Exception:
                        continue
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "删除失败", str(e))
