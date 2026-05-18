"""YAML 配置解析器"""
import yaml
from pathlib import Path
from copy import deepcopy
from typing import Dict, Any, Optional


class ConfigParser:
    """加载、修改、序列化 qlib YAML 配置"""

    @staticmethod
    def load_from_yaml(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def save_to_yaml(config: dict, path: str):
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    @staticmethod
    def get_qlib_init(config: dict) -> dict:
        return config.get("qlib_init", {})

    @staticmethod
    def get_model_config(config: dict) -> dict:
        return config.get("task", {}).get("model", {})

    @staticmethod
    def get_dataset_config(config: dict) -> dict:
        return config.get("task", {}).get("dataset", {})

    @staticmethod
    def get_backtest_config(config: dict) -> dict:
        return config.get("port_analysis_config", {})

    @staticmethod
    def get_model_kwargs(config: dict) -> dict:
        return deepcopy(config.get("task", {}).get("model", {}).get("kwargs", {}))

    @staticmethod
    def set_model_param(config: dict, key: str, value: Any) -> dict:
        config = deepcopy(config)
        if "task" not in config:
            config["task"] = {}
        if "model" not in config["task"]:
            config["task"]["model"] = {"kwargs": {}}
        if "kwargs" not in config["task"]["model"]:
            config["task"]["model"]["kwargs"] = {}
        config["task"]["model"]["kwargs"][key] = value
        return config

    @staticmethod
    def get_handler_info(config: dict) -> dict:
        handler = config.get("task", {}).get("dataset", {}).get("kwargs", {}).get("handler", {})
        return {
            "class": handler.get("class", ""),
            "module_path": handler.get("module_path", ""),
            "kwargs": handler.get("kwargs", {}),
        }

    @staticmethod
    def get_segments(config: dict) -> dict:
        return config.get("task", {}).get("dataset", {}).get("kwargs", {}).get("segments", {})

    @staticmethod
    def get_market(config: dict) -> str:
        return config.get("market", "csi300")

    @staticmethod
    def get_benchmark(config: dict) -> str:
        return config.get("benchmark", "SH000300")

    @staticmethod
    def build_full_config(
        model_id: str,
        model_class: str,
        model_module: str,
        model_kwargs: dict,
        handler_class: str,
        handler_module: str,
        handler_kwargs: dict,
        segments: dict,
        market: str = "csi300",
        benchmark: str = "SH000300",
        provider_uri: str = "~/.qlib/qlib_data/cn_data",
        topk: int = 50,
        n_drop: int = 5,
        account: float = 100000000,
        backtest_start: str = "2017-01-01",
        backtest_end: str = "2020-08-01",
    ) -> dict:
        return {
            "qlib_init": {
                "provider_uri": provider_uri,
                "region": "cn",
            },
            "market": market,
            "benchmark": benchmark,
            "data_handler_config": {
                "start_time": segments.get("train", ("2008-01-01", "2014-12-31"))[0],
                "end_time": segments.get("test", ("2017-01-01", "2020-08-01"))[1],
                "fit_start_time": segments.get("train", ("2008-01-01", "2014-12-31"))[0],
                "fit_end_time": segments.get("train", ("2008-01-01", "2014-12-31"))[1],
                "instruments": market,
            },
            "port_analysis_config": {
                "strategy": {
                    "class": "TopkDropoutStrategy",
                    "module_path": "qlib.contrib.strategy.signal_strategy",
                    "kwargs": {
                        "signal": "<PRED>",
                        "topk": topk,
                        "n_drop": n_drop,
                    },
                },
                "backtest": {
                    "start_time": backtest_start,
                    "end_time": backtest_end,
                    "account": account,
                    "benchmark": benchmark,
                    "exchange_kwargs": {
                        "freq": "day",
                        "limit_threshold": 0.095,
                        "deal_price": "close",
                        "open_cost": 0.0005,
                        "close_cost": 0.0015,
                        "min_cost": 5,
                    },
                },
            },
            "task": {
                "model": {
                    "class": model_class,
                    "module_path": model_module,
                    "kwargs": model_kwargs,
                },
                "dataset": {
                    "class": "DatasetH",
                    "module_path": "qlib.data.dataset",
                    "kwargs": {
                        "handler": {
                            "class": handler_class,
                            "module_path": handler_module,
                            "kwargs": handler_kwargs,
                        },
                        "segments": segments,
                    },
                },
            },
        }
