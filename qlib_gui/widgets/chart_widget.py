"""pyqtgraph 实时图表组件"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np
from typing import Optional


class RealtimeChart(QWidget):
    """支持实时追加数据的折线图"""

    def __init__(self, title: str = "", xlabel: str = "", ylabel: str = "",
                 parent=None, legend: bool = True):
        super().__init__(parent)
        self._curves = {}
        self._data = {}
        self._x_data = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setTitle(title, color="#2c3e50", size="12pt")
        self._plot_widget.setLabel("left", ylabel)
        self._plot_widget.setLabel("bottom", xlabel)
        self._plot_widget.setBackground("white")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.addLegend(offset=(60, 10))

        # 十字线
        self._vline = pg.InfiniteLine(angle=90, pen=pg.mkPen("#bdc3c7", style=pg.QtCore.Qt.PenStyle.DashLine))
        self._hline = pg.InfiniteLine(angle=0, pen=pg.mkPen("#bdc3c7", style=pg.QtCore.Qt.PenStyle.DashLine))
        self._plot_widget.addItem(self._vline, ignoreBounds=True)
        self._plot_widget.addItem(self._hline, ignoreBounds=True)

        # 鼠标追踪
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        layout.addWidget(self._plot_widget)

    def add_series(self, name: str, color: str = "#3498db", width: float = 2.0):
        """添加一条数据线"""
        curve = self._plot_widget.plot(
            pen=pg.mkPen(color, width=width),
            name=name,
        )
        self._curves[name] = curve
        self._data[name] = []

    def append_point(self, name: str, x, y):
        """追加一个数据点"""
        if name not in self._curves:
            return
        self._data[name].append((x, y))
        xs = [p[0] for p in self._data[name]]
        ys = [p[1] for p in self._data[name]]
        self._curves[name].setData(xs, ys)

    def set_data(self, name: str, x_data, y_data):
        """设置整条数据线"""
        if name not in self._curves:
            return
        self._data[name] = list(zip(x_data, y_data))
        self._curves[name].setData(x_data, y_data)

    def clear_all(self):
        """清空所有数据"""
        for name in self._curves:
            self._data[name] = []
            self._curves[name].setData([], [])

    def auto_range(self):
        self._plot_widget.autoRange()

    def _on_mouse_moved(self, pos):
        if self._plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
            self._vline.setPos(mouse_point.x())
            self._hline.setPos(mouse_point.y())


class ReturnChart(QWidget):
    """收益曲线图（含基准对比）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setTitle("累计收益曲线", color="#2c3e50", size="12pt")
        self._plot_widget.setLabel("left", "收益率")
        self._plot_widget.setLabel("bottom", "日期")
        self._plot_widget.setBackground("white")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.addLegend(offset=(60, 10))

        self._strategy_curve = self._plot_widget.plot(
            pen=pg.mkPen("#3498db", width=2), name="策略收益"
        )
        self._bench_curve = self._plot_widget.plot(
            pen=pg.mkPen("#e74c3c", width=2), name="基准收益"
        )
        self._excess_curve = self._plot_widget.plot(
            pen=pg.mkPen("#27ae60", width=2, style=pg.QtCore.Qt.PenStyle.DashLine), name="超额收益"
        )

        layout.addWidget(self._plot_widget)

    def set_data(self, dates, strategy_ret, bench_ret, excess_ret=None):
        import pandas as pd
        if isinstance(dates, pd.DatetimeIndex):
            x = np.arange(len(dates))
            self._plot_widget.getAxis("bottom").setTicks(
                [[(i, str(d.date())) for i, d in enumerate(dates) if i % max(1, len(dates) // 10) == 0]]
            )
        else:
            x = np.arange(len(dates))

        self._strategy_curve.setData(x, strategy_ret)
        self._bench_curve.setData(x, bench_ret)
        if excess_ret is not None:
            self._excess_curve.setData(x, excess_ret)
        self._plot_widget.autoRange()
