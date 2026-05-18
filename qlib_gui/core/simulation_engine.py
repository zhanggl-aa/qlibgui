"""模拟交易引擎 - 逐步回放，支持手动/自动下单"""
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import pandas as pd
import numpy as np
from typing import Optional, List, Dict


class SimulationEngine(QObject):
    """逐步模拟交易引擎，运行在主线程"""

    step_completed = pyqtSignal(dict)      # 每步状态
    simulation_finished = pyqtSignal()     # 模拟结束
    simulation_error = pyqtSignal(str)     # 错误
    order_executed = pyqtSignal(dict)      # 订单执行结果

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pred: Optional[pd.Series] = None
        self._calendar: List = []
        self._current_step: int = 0
        self._portfolio_value: float = 0
        self._cash: float = 0
        self._positions: Dict[str, dict] = {}  # stock_id -> {amount, cost_price}
        self._history: List[dict] = []
        self._config: dict = {}
        self._initialized = False
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self.step_forward)

    def initialize(self, pred: pd.Series, config: dict):
        """初始化模拟引擎

        Args:
            pred: 模型预测结果，multi-index (datetime, instrument)
            config: 回测配置 (account, benchmark, exchange_kwargs, topk, n_drop)
        """
        self._pred = pred
        self._config = config
        self._current_step = 0
        self._history = []
        self._positions = {}

        account_value = config.get("account", 100000000)
        self._cash = float(account_value)
        self._portfolio_value = float(account_value)

        # 提取交易日历
        if isinstance(pred.index, pd.MultiIndex):
            dates = pred.index.get_level_values("datetime").unique().sort_values()
            self._calendar = list(dates)
        else:
            self._calendar = []

        self._initialized = True

        # 发送初始状态
        self._emit_current_state()

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def total_steps(self) -> int:
        return len(self._calendar)

    @property
    def current_step(self) -> int:
        return self._current_step

    @property
    def current_date(self):
        if self._current_step > 0 and self._current_step <= len(self._calendar):
            return self._calendar[self._current_step - 1]
        return None

    def step_forward(self) -> dict:
        """推进一个交易日"""
        if not self._initialized or self._current_step >= len(self._calendar):
            self.simulation_finished.emit()
            return {}

        current_date = self._calendar[self._current_step]
        self._current_step += 1

        # 获取当日信号
        signals = self._get_signals(current_date)

        # 更新持仓市值
        self._update_portfolio_value(current_date)

        state = self._build_state(current_date, signals)
        self._history.append(state)

        self.step_completed.emit(state)

        if self._current_step >= len(self._calendar):
            self.simulation_finished.emit()

        return state

    def step_backward(self) -> bool:
        """后退一步（仅视图，不撤销交易）"""
        if self._current_step > 1:
            self._current_step -= 1
            self._emit_current_state()
            return True
        return False

    def goto_step(self, target_step: int) -> dict:
        """跳转到指定步骤"""
        if not self._initialized:
            return {}
        target_step = max(0, min(target_step, len(self._calendar)))

        if target_step == self._current_step:
            return {}

        if target_step < self._current_step:
            # 回退：从历史记录恢复状态
            self._rebuild_state_to_step(target_step)
            self._emit_current_state()
            return self._history[target_step - 1] if target_step > 0 and target_step <= len(self._history) else {}
        else:
            # 前进：逐步推进
            state = {}
            while self._current_step < target_step:
                state = self.step_forward()
            return state

    def _rebuild_state_to_step(self, target_step: int):
        """从历史记录恢复到指定步骤的状态"""
        if target_step > 0 and target_step <= len(self._history):
            state = self._history[target_step - 1]
            self._positions = {k: dict(v) for k, v in state.get("positions", {}).items()}
            self._portfolio_value = state.get("portfolio_value", self._portfolio_value)
            self._cash = state.get("cash", self._cash)
            self._current_step = target_step
        elif target_step == 0:
            account_value = self._config.get("account", 100000000)
            self._cash = float(account_value)
            self._portfolio_value = float(account_value)
            self._positions = {}
            self._current_step = 0

    def _get_signals(self, date) -> pd.Series:
        """获取某日的预测信号"""
        if self._pred is None:
            return pd.Series(dtype=float)
        try:
            signals = self._pred.loc(axis=0)[date]
            if isinstance(signals, pd.DataFrame):
                signals = signals.iloc[:, 0] if signals.shape[1] > 0 else signals.iloc[:, 0]
            return signals.sort_values(ascending=False)
        except KeyError:
            return pd.Series(dtype=float)

    def _update_portfolio_value(self, date):
        """根据当日收盘价更新持仓市值"""
        if not self._positions:
            return
        try:
            from qlib.data import D
        except ImportError:
            return
        stock_value = 0
        for stock_id, pos in self._positions.items():
            try:
                price_data = D.features([stock_id], ["$close"], date, date)
                if not price_data.empty:
                    price = price_data.iloc[0, 0]
                    if not np.isnan(price) and price > 0:
                        stock_value += pos["amount"] * price
                        pos["current_price"] = price
                    elif "current_price" in pos:
                        stock_value += pos["amount"] * pos["current_price"]
            except (KeyError, IndexError, ValueError):
                if "current_price" in pos:
                    stock_value += pos["amount"] * pos["current_price"]
        self._portfolio_value = self._cash + stock_value

    def _build_state(self, date, signals: pd.Series) -> dict:
        """构建当前状态"""
        topk = self._config.get("topk", 50)
        stock_value = self._portfolio_value - self._cash
        account_value = float(self._config.get("account", 100000000))
        return_pct = (self._portfolio_value / account_value - 1) * 100 if account_value > 0 else 0.0

        return {
            "date": date,
            "step": self._current_step,
            "total_steps": len(self._calendar),
            "signals": signals,
            "top_signals": signals.head(topk) if len(signals) > 0 else signals,
            "portfolio_value": self._portfolio_value,
            "cash": self._cash,
            "stock_value": stock_value,
            "positions": dict(self._positions),
            "return_pct": return_pct,
            "positions_count": len(self._positions),
        }

    def _emit_current_state(self):
        """发送当前状态（不推进日期）"""
        if self._current_step == 0:
            self.step_completed.emit({
                "date": None,
                "step": 0,
                "total_steps": len(self._calendar),
                "signals": pd.Series(dtype=float),
                "top_signals": pd.Series(dtype=float),
                "portfolio_value": self._portfolio_value,
                "cash": self._cash,
                "stock_value": 0,
                "positions": {},
                "return_pct": 0,
                "positions_count": 0,
            })
        else:
            date = self._calendar[min(self._current_step - 1, len(self._calendar) - 1)]
            signals = self._get_signals(date)
            state = self._build_state(date, signals)
            self.step_completed.emit(state)

    def place_order(self, stock_id: str, amount: int, direction: int) -> dict:
        """手动下单

        Args:
            stock_id: 股票代码
            amount: 数量（正数）
            direction: 1=买入, -1=卖出

        Returns:
            执行结果 dict
        """
        if not self._initialized or self._current_step == 0:
            return {"success": False, "reason": "模拟未初始化"}

        if self._current_step > len(self._calendar):
            return {"success": False, "reason": "模拟已结束"}

        current_date = self._calendar[self._current_step - 1]

        try:
            from qlib.data import D
            price_data = D.features([stock_id], ["$close"], current_date, current_date)
            if price_data.empty:
                return {"success": False, "reason": f"无法获取 {stock_id} 的价格数据"}
            price = float(price_data.iloc[0, 0])
            if np.isnan(price) or price <= 0:
                return {"success": False, "reason": f"{stock_id} 停牌或价格无效"}
        except Exception as e:
            return {"success": False, "reason": f"获取价格失败: {e}"}

        open_cost = self._config.get("exchange_kwargs", {}).get("open_cost", 0.0005)
        close_cost = self._config.get("exchange_kwargs", {}).get("close_cost", 0.0015)
        min_cost = self._config.get("exchange_kwargs", {}).get("min_cost", 5)

        if direction == 1:  # 买入
            trade_value = amount * price
            cost = max(trade_value * open_cost, min_cost)
            total_need = trade_value + cost
            if total_need > self._cash:
                # 调整数量
                max_amount = int(self._cash * 0.95 / (price * (1 + open_cost)))
                max_amount = max_amount // 100 * 100  # A股100股整数倍
                if max_amount <= 0:
                    return {"success": False, "reason": "可用现金不足"}
                amount = max_amount
                trade_value = amount * price
                cost = max(trade_value * open_cost, min_cost)
                total_need = trade_value + cost

            self._cash -= total_need
            if stock_id in self._positions:
                old = self._positions[stock_id]
                total_amount = old["amount"] + amount
                old_cost = old["cost_price"] * old["amount"]
                self._positions[stock_id] = {
                    "amount": total_amount,
                    "cost_price": (old_cost + trade_value) / total_amount,
                    "current_price": price,
                }
            else:
                self._positions[stock_id] = {
                    "amount": amount,
                    "cost_price": price,
                    "current_price": price,
                }

            result = {
                "success": True,
                "stock_id": stock_id,
                "direction": "买入",
                "amount": amount,
                "price": price,
                "value": trade_value,
                "cost": cost,
            }

        elif direction == -1:  # 卖出
            if stock_id not in self._positions:
                return {"success": False, "reason": f"未持有 {stock_id}"}

            held = self._positions[stock_id]
            if amount > held["amount"]:
                amount = held["amount"]

            trade_value = amount * price
            cost = max(trade_value * close_cost, min_cost)
            self._cash += trade_value - cost

            held["amount"] -= amount
            if held["amount"] <= 0:
                del self._positions[stock_id]

            result = {
                "success": True,
                "stock_id": stock_id,
                "direction": "卖出",
                "amount": amount,
                "price": price,
                "value": trade_value,
                "cost": cost,
            }
        else:
            return {"success": False, "reason": "无效的交易方向"}

        self.order_executed.emit(result)
        self._emit_current_state()
        return result

    def auto_trade_step(self) -> List[dict]:
        """自动执行 TopkDropoutStrategy 策略"""
        if not self._initialized or self._current_step == 0:
            return []

        topk = self._config.get("topk", 50)
        n_drop = self._config.get("n_drop", 5)

        # 先推进到新的一天
        state = self.step_forward()
        if not state:
            return []

        signals = state.get("signals", pd.Series(dtype=float))
        if signals.empty:
            return []

        # 目标持仓
        target_stocks = set(signals.head(topk).index.tolist())
        current_stocks = set(self._positions.keys())

        results = []

        # 卖出不在目标中的股票
        sells = current_stocks - target_stocks
        for stock_id in sells:
            amount = self._positions[stock_id]["amount"]
            result = self.place_order(stock_id, amount, -1)
            results.append(result)

        # 买入新股票
        buys = target_stocks - current_stocks
        if buys:
            buy_budget = self._cash * 0.9 / max(len(buys), 1)
            for stock_id in buys:
                try:
                    from qlib.data import D
                    current_date = self._calendar[self._current_step - 1]
                    price_data = D.features([stock_id], ["$close"], current_date, current_date)
                    if not price_data.empty:
                        price = float(price_data.iloc[0, 0])
                        if price > 0:
                            amount = int(buy_budget / price)
                            amount = amount // 100 * 100
                            if amount > 0:
                                result = self.place_order(stock_id, amount, 1)
                                results.append(result)
                except Exception:
                    pass

        return results

    def start_auto_play(self, interval_ms: int = 1000):
        """开始自动播放"""
        self._auto_timer.start(interval_ms)

    def stop_auto_play(self):
        """停止自动播放"""
        self._auto_timer.stop()

    @property
    def is_auto_playing(self) -> bool:
        return self._auto_timer.isActive()

    def reset(self):
        """重置模拟"""
        self.stop_auto_play()
        self._current_step = 0
        self._positions = {}
        self._history = []
        account_value = self._config.get("account", 100000000)
        self._cash = float(account_value)
        self._portfolio_value = float(account_value)
        self._emit_current_state()

    def get_history(self) -> List[dict]:
        """获取历史状态"""
        return self._history
