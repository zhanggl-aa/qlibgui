"""回测引擎 - 在 QThread 中运行回测"""
from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd


class BacktestEngine(QThread):
    """后台回测线程"""

    backtest_completed = pyqtSignal(object, object)  # (report_normal, positions_normal)
    backtest_error = pyqtSignal(str)
    backtest_progress = pyqtSignal(str)

    def __init__(self, pred, backtest_config: dict, parent=None):
        super().__init__(parent)
        self.pred = pred
        self.backtest_config = backtest_config

    def run(self):
        try:
            self.backtest_progress.emit("正在初始化回测...")

            from qlib.contrib.evaluate import backtest_daily

            strategy_config = self.backtest_config.get("strategy", {})
            bt_config = self.backtest_config.get("backtest", {})

            topk = strategy_config.get("kwargs", {}).get("topk", 50)
            n_drop = strategy_config.get("kwargs", {}).get("n_drop", 5)

            self.backtest_progress.emit("正在运行回测...")

            report_normal, positions_normal = backtest_daily(
                start_time=bt_config.get("start_time", "2017-01-01"),
                end_time=bt_config.get("end_time", "2020-08-01"),
                account=bt_config.get("account", 100000000),
                benchmark=bt_config.get("benchmark", "SH000300"),
                exchange_kwargs=bt_config.get("exchange_kwargs", {}),
                strategy={
                    "class": "TopkDropoutStrategy",
                    "module_path": "qlib.contrib.strategy.signal_strategy",
                    "kwargs": {
                        "signal": self.pred,
                        "topk": topk,
                        "n_drop": n_drop,
                    },
                },
            )

            self.backtest_progress.emit("回测完成")
            self.backtest_completed.emit(report_normal, positions_normal)

        except Exception as e:
            self.backtest_error.emit(str(e))
