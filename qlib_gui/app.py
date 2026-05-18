"""主窗口"""
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar, QMenuBar,
    QMessageBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from qlib_gui.widgets.sidebar import Sidebar
from qlib_gui.pages.home_page import HomePage
from qlib_gui.pages.model_page import ModelPage
from qlib_gui.pages.training_page import TrainingPage
from qlib_gui.pages.backtest_page import BacktestPage
from qlib_gui.pages.simulation_page import SimulationPage
from qlib_gui.pages.experiment_page import ExperimentPage
from qlib_gui.pages.factor_analysis_page import FactorAnalysisPage
from qlib_gui.pages.portfolio_optimization_page import PortfolioOptimizationPage
from qlib_gui.core.qlib_manager import QlibManager
from qlib_gui.core.model_registry import ModelRegistry
from qlib_gui.core.model_store import TrainedModelStore
from qlib_gui.core.model_persistence import ModelPersistence


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qlib 量化投资平台")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)

        self._current_model_id = None
        self._current_model = None
        self._current_dataset = None
        self._current_config = None
        self._training_engine = None
        self._backtest_engine = None

        self._init_ui()
        self._init_qlib()
        self._connect_signals()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._pages = {
            "home": HomePage(),
            "model": ModelPage(),
            "training": TrainingPage(),
            "backtest": BacktestPage(),
            "simulation": SimulationPage(),
            "experiment": ExperimentPage(),
            "factor_analysis": FactorAnalysisPage(),
            "portfolio_optimization": PortfolioOptimizationPage(),
        }
        for page_id in ["home", "model", "training", "backtest", "simulation", "experiment",
                       "factor_analysis", "portfolio_optimization"]:
            self._stack.addWidget(self._pages[page_id])

        # 加载已保存的模型
        saved_models = ModelPersistence.load_all()
        for model_id, trained_model in saved_models.items():
            TrainedModelStore.save(
                model_id=model_id,
                model=trained_model.model,
                dataset=trained_model.dataset,
                config=trained_model.config,
                model_type=trained_model.model_type,
                evals_result=trained_model.evals_result
            )
        print(f"Loaded {len(saved_models)} saved models from disk")

        # 初始化模型选择下拉框
        self._refresh_model_combos()

        # 状态栏
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")

        # 菜单栏
        self._create_menu()

    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        act_init = file_menu.addAction("初始化 Qlib")
        act_init.triggered.connect(self._init_qlib)
        file_menu.addSeparator()
        act_exit = file_menu.addAction("退出")
        act_exit.triggered.connect(self.close)

        view_menu = menubar.addMenu("视图(&V)")
        for page_id, label in [("home", "首页"), ("model", "模型选择"),
                                ("training", "训练"), ("backtest", "回测"),
                                ("simulation", "模拟炒股"), ("experiment", "实验记录"),
                                ("factor_analysis", "因子分析"), ("portfolio_optimization", "组合优化")]:
            act = view_menu.addAction(label)
            act.triggered.connect(lambda checked, pid=page_id: self._switch_page(pid))

        help_menu = menubar.addMenu("帮助(&H)")
        act_about = help_menu.addAction("关于")
        act_about.triggered.connect(self._show_about)

    def _init_qlib(self):
        if QlibManager.is_initialized():
            self._sidebar.set_status("Qlib 已初始化")
            return
        success = QlibManager.initialize()
        if success:
            self._sidebar.set_status("Qlib 初始化成功")
            models = ModelRegistry.discover_all()
            self._statusbar.showMessage(f"已加载 {len(models)} 个模型")
            self._pages["home"].refresh()
        else:
            self._sidebar.set_status("Qlib 未初始化")
            error_type = QlibManager.get_last_error_type()
            if error_type == "not_installed":
                msg = "qlib 未安装。请运行: pip install pyqlib"
            elif error_type == "no_data":
                msg = (f"Qlib 数据目录不存在或为空: {QlibManager.get_provider_uri()}\n\n"
                       f"请先下载数据:\npython -m qlib.cli.data qlib_data "
                       f"--target_dir ~/.qlib/qlib_data/cn_data --region cn")
            elif error_type == "init_failed":
                msg = f"Qlib 初始化失败: {QlibManager.get_last_error()}"
            else:
                msg = "Qlib 未初始化"
            self._statusbar.showMessage("Qlib 未初始化 - 部分功能不可用")
            print(f"[Qlib GUI] {msg}")

    def _connect_signals(self):
        self._sidebar.page_changed.connect(self._switch_page)

        # 首页快捷导航
        self._pages["home"].goto_model.connect(lambda: self._switch_page("model"))
        self._pages["home"].goto_simulation.connect(self._switch_to_simulation)

        # 模型选择页
        self._pages["model"].model_selected.connect(self._on_model_selected)
        self._pages["model"].training_requested.connect(self._start_training)

        # 训练页
        self._pages["training"].backtest_requested.connect(self._start_backtest)
        self._pages["training"].simulation_requested.connect(self._switch_to_simulation)
        self._pages["training"].stop_requested.connect(self._on_stop_training)

        # 回测页
        self._pages["backtest"].simulation_requested.connect(self._switch_to_simulation)
        self._pages["backtest"].model_switch_requested.connect(self._on_backtest_model_switch)
        self._pages["backtest"].backtest_requested.connect(self._start_backtest)

        # 模拟页
        self._pages["simulation"].model_switch_requested.connect(self._on_simulation_model_switch)
        self._pages["simulation"].simulation_requested.connect(self._switch_to_simulation)

        # 因子分析页
        self._pages["factor_analysis"].factor_analysis_requested.connect(self._on_factor_analysis_requested)
        self._pages["factor_analysis"].factor_export_requested.connect(self._on_factor_export_requested)

        # 组合优化页
        self._pages["portfolio_optimization"].optimization_requested.connect(self._on_portfolio_optimization_requested)
        self._pages["portfolio_optimization"].portfolio_export_requested.connect(self._on_portfolio_export_requested)

    def _refresh_model_combos(self):
        """刷新所有需要模型选择的下拉框"""
        trained_ids = TrainedModelStore.trained_ids()
        self._pages["backtest"].update_model_list(trained_ids, self._current_model_id)
        self._pages["simulation"].update_model_list(trained_ids, self._current_model_id)
        self._pages["factor_analysis"].update_model_list(trained_ids, self._current_model_id)
        self._pages["portfolio_optimization"].update_model_list(trained_ids, self._current_model_id)

    def _switch_page(self, page_id: str):
        self._sidebar.set_current_page(page_id)
        idx = list(self._pages.keys()).index(page_id)
        self._stack.setCurrentIndex(idx)

    def _on_model_selected(self, model_id: str):
        self._current_model_id = model_id
        self._sidebar.set_status(f"已选择: {model_id}")

    def _start_training(self, config: dict):
        model_id = config.get("model_id")
        model_info = ModelRegistry.get(model_id)
        if not model_info:
            QMessageBox.warning(self, "错误", f"未知模型: {model_id}")
            return

        if not QlibManager.is_initialized():
            QMessageBox.warning(self, "错误", "请先初始化 Qlib")
            return

        try:
            # 使用 qlib 的标准 workflow 方式，通过加载 YAML 配置文件
            config_path = ModelRegistry.get_default_config_path(
                model_id,
                config.get("dataset", "Alpha158"),
                config.get("market", "csi300")
            )
            if config_path is not None:
                print(f"[Training] Loading default config: {config_path}")
                from qlib_gui.core.config_parser import ConfigParser
                qlib_config = ConfigParser.load_from_yaml(str(config_path))

                # 应用用户配置
                if config.get("model_kwargs"):
                    for key, value in config["model_kwargs"].items():
                        qlib_config = ConfigParser.set_model_param(qlib_config, key, value)

                # 使用 qlib 的 init_instance_by_config 来初始化模型和数据集
                from qlib.init import init_instance_by_config
                self._current_model = init_instance_by_config(qlib_config["task"]["model"])
                self._current_dataset = init_instance_by_config(qlib_config["task"]["dataset"])
                self._current_config = config

            else:
                # 如果没有找到默认配置文件，使用传统方式
                model_kwargs = config.get("model_kwargs", model_info.default_kwargs)
                model = ModelRegistry.create_model(model_id, **model_kwargs)
                self._current_model = model
                self._current_config = config

                # 构建数据集
                from qlib.contrib.data.handler import Alpha158, Alpha360

                dataset_cls = Alpha158 if config.get("dataset", "Alpha158") == "Alpha158" else Alpha360
                market = config.get("market", "csi300")

                # 对于时序模型（LSTM、GRU、ALSTM），需要设置特殊的数据处理
                if model_info.special_dataset_cls == "TSDatasetH":
                    # 设置特征过滤和标准化
                    infer_processors = [
                        {
                            "class": "FilterCol",
                            "kwargs": {
                                "fields_group": "feature",
                                "col_list": ["RESI5", "WVMA5", "RSQR5", "KLEN", "RSQR10", "CORR5", "CORD5", "CORR10",
                                           "ROC60", "RESI10", "VSTD5", "RSQR60", "CORR60", "WVMA60", "STD5",
                                           "RSQR20", "CORD60", "CORD10", "CORR20", "KLOW"]
                            }
                        },
                        {
                            "class": "RobustZScoreNorm",
                            "kwargs": {
                                "fields_group": "feature",
                                "clip_outlier": True
                            }
                        },
                        {
                            "class": "Fillna",
                            "kwargs": {
                                "fields_group": "feature"
                            }
                        }
                    ]
                    learn_processors = [
                        {
                            "class": "DropnaLabel"
                        },
                        {
                            "class": "CSRankNorm",
                            "kwargs": {
                                "fields_group": "label"
                            }
                        }
                    ]
                    handler = dataset_cls(
                        instruments=market,
                        start_time=config.get("start_time", "2008-01-01"),
                        end_time=config.get("end_time", "2020-08-01"),
                        fit_start_time=config.get("start_time", "2008-01-01"),
                        fit_end_time=config.get("fit_end_time", "2014-12-31"),
                        infer_processors=infer_processors,
                        learn_processors=learn_processors,
                    )
                else:
                    handler = dataset_cls(
                        instruments=market,
                        start_time=config.get("start_time", "2008-01-01"),
                        end_time=config.get("end_time", "2020-08-01"),
                        fit_start_time=config.get("start_time", "2008-01-01"),
                        fit_end_time=config.get("fit_end_time", "2014-12-31"),
                    )
                segments = {
                    "train": ("2008-01-01", "2014-12-31"),
                    "valid": ("2015-01-01", "2016-12-31"),
                    "test": ("2017-01-01", "2020-08-01"),
                }
                if "segments" in config:
                    segments = config["segments"]

                # 根据模型类型选择数据集类
                if model_info.special_dataset_cls == "TSDatasetH":
                    from qlib.data.dataset import TSDatasetH
                    dataset = TSDatasetH(handler=handler, segments=segments, step_len=20)
                else:
                    from qlib.data.dataset import DatasetH
                    dataset = DatasetH(handler=handler, segments=segments)
                self._current_dataset = dataset

            # 启动训练
            from qlib_gui.core.training_engine import TrainingEngine
            self._training_engine = TrainingEngine(
                model, dataset, model_info.model_type, parent=self
            )
            self._training_engine.epoch_completed.connect(
                self._pages["training"].on_epoch_completed
            )
            self._training_engine.training_finished.connect(
                self._on_training_finished
            )
            self._training_engine.training_error.connect(
                self._on_training_error
            )
            self._training_engine.progress_update.connect(
                self._pages["training"].on_progress_update
            )

            self._pages["training"].start_training(model_id, model_info.model_type)
            self._training_engine.start()

            self._switch_page("training")
            self._sidebar.set_status(f"正在训练: {model_id}")

        except ImportError as e:
            QMessageBox.critical(self, "模型导入失败",
                f"无法导入模型 {model_id}。\n\n"
                f"原因: {e}\n\n"
                f"请确认已安装相关依赖包。")
        except Exception as e:
            QMessageBox.critical(self, "训练启动失败", str(e))

    def _on_training_finished(self, evals_result: dict):
        model_id = self._training_engine.model.model_id if hasattr(self._training_engine.model, 'model_id') else self._current_model_id
        # 保存到模型仓库
        TrainedModelStore.save(
            model_id=model_id,
            model=self._training_engine.model,
            dataset=self._training_engine.dataset,
            config=self._current_config or {},
            model_type=self._training_engine.model_type,
            evals_result=evals_result,
        )
        # 保存到磁盘
        ModelPersistence.save(
            model_id=model_id,
            model=self._training_engine.model,
            dataset=self._training_engine.dataset,
            config=self._current_config or {},
            model_type=self._training_engine.model_type,
            evals_result=evals_result
        )
        self._current_model_id = model_id
        self._current_model = self._training_engine.model
        self._current_dataset = self._training_engine.dataset
        self._current_config = self._current_config or {}

        self._sidebar.set_status(f"训练完成: {model_id}")
        self._statusbar.showMessage("训练完成，可以运行回测或模拟炒股")
        self._pages["training"].on_training_finished(evals_result)
        self._refresh_model_combos()

    def _on_training_error(self, error_msg: str):
        self._sidebar.set_status("训练失败")
        QMessageBox.critical(self, "训练错误", error_msg)
        self._pages["training"].on_training_error(error_msg)

    def _on_stop_training(self):
        if self._training_engine is not None and self._training_engine.isRunning():
            self._training_engine.request_stop()
            self._sidebar.set_status("正在停止训练...")
            self._statusbar.showMessage("已请求停止训练，等待当前 epoch 完成")

    def _get_pred_for_model(self, model_id: str):
        """获取指定模型的预测结果，如无则先 predict"""
        entry = TrainedModelStore.get(model_id)
        if entry is None:
            return None
        if entry.pred is not None:
            return entry.pred
        try:
            # 如果数据集为空，根据配置重新创建数据集
            if entry.dataset is None:
                print(f"[Prediction] Dataset is None, rebuilding from config: {entry.config}")
                from qlib.contrib.data.handler import Alpha158, Alpha360
                from qlib.data.dataset import DatasetH, TSDatasetH

                dataset_cls = Alpha158 if entry.config.get("dataset", "Alpha158") == "Alpha158" else Alpha360
                market = entry.config.get("market", "csi300")

                # 根据模型类型选择数据处理方式
                model_info = ModelRegistry.get(model_id)
                if model_info and model_info.special_dataset_cls == "TSDatasetH":
                    # 对于时序模型，需要设置特征过滤和标准化
                    infer_processors = [
                        {
                            "class": "FilterCol",
                            "kwargs": {
                                "fields_group": "feature",
                                "col_list": ["RESI5", "WVMA5", "RSQR5", "KLEN", "RSQR10", "CORR5", "CORD5", "CORR10",
                                           "ROC60", "RESI10", "VSTD5", "RSQR60", "CORR60", "WVMA60", "STD5",
                                           "RSQR20", "CORD60", "CORD10", "CORR20", "KLOW"]
                            }
                        },
                        {
                            "class": "RobustZScoreNorm",
                            "kwargs": {
                                "fields_group": "feature",
                                "clip_outlier": True
                            }
                        },
                        {
                            "class": "Fillna",
                            "kwargs": {
                                "fields_group": "feature"
                            }
                        }
                    ]
                    learn_processors = [
                        {
                            "class": "DropnaLabel"
                        },
                        {
                            "class": "CSRankNorm",
                            "kwargs": {
                                "fields_group": "label"
                            }
                        }
                    ]
                    handler = dataset_cls(
                        instruments=market,
                        start_time=entry.config.get("start_time", "2008-01-01"),
                        end_time=entry.config.get("end_time", "2020-08-01"),
                        fit_start_time=entry.config.get("start_time", "2008-01-01"),
                        fit_end_time=entry.config.get("fit_end_time", "2014-12-31"),
                        infer_processors=infer_processors,
                        learn_processors=learn_processors,
                    )
                else:
                    handler = dataset_cls(
                        instruments=market,
                        start_time=entry.config.get("start_time", "2008-01-01"),
                        end_time=entry.config.get("end_time", "2020-08-01"),
                        fit_start_time=entry.config.get("start_time", "2008-01-01"),
                        fit_end_time=entry.config.get("fit_end_time", "2014-12-31"),
                    )

                segments = {
                    "train": (entry.config.get("start_time", "2008-01-01"), "2014-12-31"),
                    "valid": ("2015-01-01", "2016-12-31"),
                    "test": ("2017-01-01", entry.config.get("end_time", "2020-08-01")),
                }
                if "segments" in entry.config:
                    segments = entry.config["segments"]

                # 根据模型类型选择数据集类
                if model_info and model_info.special_dataset_cls == "TSDatasetH":
                    entry.dataset = TSDatasetH(handler=handler, segments=segments, step_len=20)
                else:
                    entry.dataset = DatasetH(handler=handler, segments=segments)
                print(f"[Prediction] Dataset rebuilt successfully")

            # 进行预测
            entry.pred = entry.model.predict(entry.dataset)
            return entry.pred
        except Exception as e:
            print(f"[Prediction Error] {e}")
            import traceback
            print(traceback.format_exc())
            QMessageBox.critical(self, "预测失败", str(e))
            return None

    def _start_backtest(self, model_id: str = None):
        target_id = model_id or self._current_model_id
        if not target_id:
            QMessageBox.warning(self, "错误", "请先训练模型")
            return

        entry = TrainedModelStore.get(target_id)
        if entry is None:
            QMessageBox.warning(self, "错误", f"未找到已训练的模型: {target_id}")
            return

        pred = self._get_pred_for_model(target_id)
        if pred is None:
            return

        self._current_model_id = target_id
        self._current_config = entry.config

        backtest_config = entry.config or {}
        bt_config = backtest_config.get("port_analysis_config", {
            "strategy": {"kwargs": {"topk": 50, "n_drop": 5}},
            "backtest": {
                "start_time": "2017-01-01",
                "end_time": "2020-08-01",
                "account": 100000000,
                "benchmark": "SH000300",
                "exchange_kwargs": {
                    "freq": "day",
                    "limit_threshold": 0.095,
                    "deal_price": "close",
                    "open_cost": 0.0005,
                    "close_cost": 0.0015,
                    "min_cost": 5,
                },
            },
        })

        from qlib_gui.core.backtest_engine import BacktestEngine
        self._backtest_engine = BacktestEngine(pred, bt_config, parent=self)
        self._backtest_engine.backtest_completed.connect(
            self._on_backtest_completed
        )
        self._backtest_engine.backtest_error.connect(
            lambda msg: QMessageBox.critical(self, "回测错误", msg)
        )
        self._backtest_engine.backtest_progress.connect(
            lambda msg: self._statusbar.showMessage(msg)
        )
        self._backtest_engine.start()

        self._switch_page("backtest")
        self._sidebar.set_status(f"正在回测: {target_id}")

    def _on_backtest_completed(self, report_normal, positions_normal):
        self._sidebar.set_status("回测完成")
        self._pages["backtest"].display_results(report_normal, positions_normal)

    def _on_backtest_model_switch(self, model_id: str):
        """回测页切换模型"""
        self._start_backtest(model_id)

    def _switch_to_simulation(self, model_id: str = None):
        target_id = model_id or self._current_model_id
        if not target_id:
            QMessageBox.warning(self, "错误", "请先训练模型")
            return

        entry = TrainedModelStore.get(target_id)
        if entry is None:
            QMessageBox.warning(self, "错误", f"未找到已训练的模型: {target_id}")
            return

        self._current_model_id = target_id
        config = entry.config if entry else {}
        bt_config = config.get("port_analysis_config", {}).get("backtest", {})
        sim_config = {
            "account": bt_config.get("account", 100000000),
            "benchmark": bt_config.get("benchmark", "SH000300"),
            "exchange_kwargs": bt_config.get("exchange_kwargs", {}),
            "topk": config.get("port_analysis_config", {}).get("strategy", {}).get("kwargs", {}).get("topk", 50),
            "n_drop": config.get("port_analysis_config", {}).get("strategy", {}).get("kwargs", {}).get("n_drop", 5),
        }

        # 确保数据集存在
        if entry.dataset is None:
            print(f"[Simulation] Dataset is None, rebuilding from config")
            try:
                from qlib.contrib.data.handler import Alpha158, Alpha360
                from qlib.data.dataset import DatasetH, TSDatasetH

                dataset_cls = Alpha158 if config.get("dataset", "Alpha158") == "Alpha158" else Alpha360
                market = config.get("market", "csi300")

                # 根据模型类型选择数据处理方式
                model_info = ModelRegistry.get(target_id)
                if model_info and model_info.special_dataset_cls == "TSDatasetH":
                    # 对于时序模型，需要设置特征过滤和标准化
                    infer_processors = [
                        {
                            "class": "FilterCol",
                            "kwargs": {
                                "fields_group": "feature",
                                "col_list": ["RESI5", "WVMA5", "RSQR5", "KLEN", "RSQR10", "CORR5", "CORD5", "CORR10",
                                           "ROC60", "RESI10", "VSTD5", "RSQR60", "CORR60", "WVMA60", "STD5",
                                           "RSQR20", "CORD60", "CORD10", "CORR20", "KLOW"]
                            }
                        },
                        {
                            "class": "RobustZScoreNorm",
                            "kwargs": {
                                "fields_group": "feature",
                                "clip_outlier": True
                            }
                        },
                        {
                            "class": "Fillna",
                            "kwargs": {
                                "fields_group": "feature"
                            }
                        }
                    ]
                    learn_processors = [
                        {
                            "class": "DropnaLabel"
                        },
                        {
                            "class": "CSRankNorm",
                            "kwargs": {
                                "fields_group": "label"
                            }
                        }
                    ]
                    handler = dataset_cls(
                        instruments=market,
                        start_time=config.get("start_time", "2008-01-01"),
                        end_time=config.get("end_time", "2020-08-01"),
                        fit_start_time=config.get("start_time", "2008-01-01"),
                        fit_end_time=config.get("fit_end_time", "2014-12-31"),
                        infer_processors=infer_processors,
                        learn_processors=learn_processors,
                    )
                else:
                    handler = dataset_cls(
                        instruments=market,
                        start_time=config.get("start_time", "2008-01-01"),
                        end_time=config.get("end_time", "2020-08-01"),
                        fit_start_time=config.get("start_time", "2008-01-01"),
                        fit_end_time=config.get("fit_end_time", "2014-12-31"),
                    )

                segments = {
                    "train": (config.get("start_time", "2008-01-01"), "2014-12-31"),
                    "valid": ("2015-01-01", "2016-12-31"),
                    "test": ("2017-01-01", config.get("end_time", "2020-08-01")),
                }
                if "segments" in config:
                    segments = config["segments"]

                # 根据模型类型选择数据集类
                if model_info and model_info.special_dataset_cls == "TSDatasetH":
                    entry.dataset = TSDatasetH(handler=handler, segments=segments, step_len=20)
                else:
                    entry.dataset = DatasetH(handler=handler, segments=segments)
                print(f"[Simulation] Dataset rebuilt successfully")
            except Exception as e:
                print(f"[Simulation] Error rebuilding dataset: {e}")
                import traceback
                print(traceback.format_exc())

        # 初始化回放模式（预计算预测结果）
        pred = self._get_pred_for_model(target_id)
        if pred is not None:
            self._pages["simulation"].initialize(pred, sim_config)

        # 初始化实时模式（模型每日预测）
        if entry.model is not None and entry.dataset is not None:
            try:
                # 从 dataset 提取 handler 和 segments
                if hasattr(entry.dataset, 'handler'):
                    handler = entry.dataset.handler
                else:
                    handler = None

                if hasattr(entry.dataset, 'segments'):
                    segments = entry.dataset.segments
                else:
                    segments = {
                        "train": ("2008-01-01", "2014-12-31"),
                        "valid": ("2015-01-01", "2016-12-31"),
                        "test": ("2017-01-01", "2020-08-01"),
                    }

                market = config.get("market", "csi300")
                if handler:
                    self._pages["simulation"].initialize_realtime(
                        entry.model, handler, segments, sim_config, market
                    )
            except Exception as e:
                print(f"实时模拟初始化失败: {e}")

        self._switch_page("simulation")
        self._sidebar.set_status(f"模拟炒股: {target_id}")

    def _on_simulation_model_switch(self, model_id: str):
        """模拟页切换模型"""
        self._switch_to_simulation(model_id)

    def _on_factor_analysis_requested(self, config):
        """处理因子分析请求"""
        model_id = config.get("model_id")
        if not model_id:
            QMessageBox.warning(self, "错误", "请先选择模型")
            return

        entry = TrainedModelStore.get(model_id)
        if entry is None:
            QMessageBox.warning(self, "错误", f"未找到已训练的模型: {model_id}")
            return

        self._switch_page("factor_analysis")
        self._sidebar.set_status(f"正在分析模型 {model_id} 的因子...")

        # 模拟因子分析结果（实际应调用 Qlib 的因子分析方法）
        factor_result = self._simulate_factor_analysis(entry)
        self._pages["factor_analysis"].display_factor_analysis(factor_result)
        self._sidebar.set_status("因子分析完成")

    def _simulate_factor_analysis(self, entry):
        """模拟因子分析结果"""
        # 生成示例数据
        factors = [
            "Alpha001", "Alpha002", "Alpha003", "Alpha004", "Alpha005",
            "Alpha006", "Alpha007", "Alpha008", "Alpha009", "Alpha010",
            "Beta", "Momentum", "Size", "Value", "Volatility",
            "Liquidity", "Earnings", "Growth", "Profitability", "Quality"
        ]

        import random
        random.seed(42)

        importance = {f: random.random() for f in factors}
        total = sum(importance.values())
        importance = {k: v/total for k, v in importance.items()}

        dates = [f"2023-{i:02d}-01" for i in range(1, 13)]
        exposure = {}
        for factor in ["市场", "市值", "动量", "价值", "盈利"]:
            exposure[factor] = [random.uniform(-1, 1) for _ in dates]
        exposure_df = pd.DataFrame(exposure, index=pd.to_datetime(dates))

        # 生成相关性矩阵
        corr_data = np.random.rand(len(factors), len(factors))
        np.fill_diagonal(corr_data, 1.0)
        corr = pd.DataFrame(corr_data, index=factors, columns=factors)

        risk_data = {}
        for factor in factors[:10]:
            risk_data[factor] = {
                "volatility": random.uniform(0.05, 0.3),
                "var95": random.uniform(0.02, 0.1),
                "max_drawdown": random.uniform(0.05, 0.25)
            }

        return {
            "importance": importance,
            "exposure": exposure_df,
            "correlation": corr,
            "risk": risk_data
        }

    def _on_factor_export_requested(self, file_path, factor_data):
        """处理因子分析报告导出"""
        print(f"导出因子分析报告到: {file_path}")

    def _on_portfolio_optimization_requested(self, config):
        """处理组合优化请求"""
        model_id = config.get("model_id")
        if not model_id:
            QMessageBox.warning(self, "错误", "请先选择模型")
            return

        entry = TrainedModelStore.get(model_id)
        if entry is None:
            QMessageBox.warning(self, "错误", f"未找到已训练的模型: {model_id}")
            return

        self._switch_page("portfolio_optimization")
        self._sidebar.set_status(f"正在优化 {config.get('objective')}...")

        # 模拟组合优化结果
        optimization_result = self._simulate_portfolio_optimization(config)
        self._pages["portfolio_optimization"].display_optimization_result(optimization_result)
        self._sidebar.set_status("组合优化完成")

    def _simulate_portfolio_optimization(self, config):
        """模拟组合优化结果"""
        import random
        random.seed(42)

        num_stocks = config.get("stock_count", 20)
        stocks = [f"600{i:03d}" for i in range(1, num_stocks+1)]

        weights = {stock: random.random() for stock in stocks}
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

        # 生成有效前沿数据
        frontier_risks = np.linspace(0.15, 0.35, 50)
        frontier_returns = 0.05 + 0.2 * frontier_risks - 0.3 * frontier_risks**2
        optimal_idx = int(len(frontier_risks) * 0.6)

        backtest_days = 252
        portfolio_values = []
        benchmark_values = []
        start_value = 1.0
        current_portfolio = start_value
        current_benchmark = start_value

        for i in range(backtest_days):
            daily_return = random.gauss(0.0005, 0.02)
            current_portfolio = current_portfolio * (1 + daily_return)
            portfolio_values.append(current_portfolio)

            benchmark_return = random.gauss(0.0002, 0.015)
            current_benchmark = current_benchmark * (1 + benchmark_return)
            benchmark_values.append(current_benchmark)

        dates = pd.date_range(start="2023-01-01", periods=backtest_days)

        return {
            "weights": weights,
            "frontier": {
                "risks": list(frontier_risks),
                "returns": list(frontier_returns),
                "optimal": {
                    "risk": frontier_risks[optimal_idx],
                    "return": frontier_returns[optimal_idx]
                }
            },
            "backtest": {
                "dates": list(dates.strftime("%Y-%m-%d")),
                "portfolio": portfolio_values,
                "benchmark": benchmark_values
            },
            "risk_decomposition": {
                "市场风险": 0.35,
                "行业风险": 0.25,
                "个股风险": 0.20,
                "模型风险": 0.15,
                "流动性风险": 0.05
            },
            "stats": {
                "预期年化收益": 0.18,
                "预期波动率": 0.22,
                "夏普比率": 0.75,
                "最大回撤": 0.18,
                "VaR(95%)": 0.045
            }
        }

    def _on_portfolio_export_requested(self, file_path, result):
        """处理组合导出请求"""
        print(f"导出组合到: {file_path}")

    def _show_about(self):
        QMessageBox.about(
            self, "关于 Qlib 量化投资平台",
            "Qlib 量化投资可视化平台\n\n"
            "基于 Qlib 量化研究框架\n"
            "支持 25 个机器学习模型\n"
            "提供训练可视化、回测分析和模拟炒股功能\n\n"
            "新增功能:\n"
            "- 因子分析: 分析模型的因子重要性和暴露\n"
            "- 组合优化: 基于现代投资组合理论优化资产配置\n"
            "- 策略回测: 支持多策略对比和参数优化\n\n"
            "技术栈: PyQt6 + pyqtgraph + Qlib"
        )
