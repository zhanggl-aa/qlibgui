"""模型注册表 - 25 个 qlib benchmark 模型的统一管理"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import importlib
import yaml


BENCHMARKS_DIR = Path(__file__).resolve().parents[2] / "examples" / "benchmarks"


@dataclass
class ModelInfo:
    model_id: str
    class_name: str
    module_path: str
    category: str  # tree / neural / advanced
    model_type: str  # pytorch / lightgbm / sklearn / tensorflow
    chinese_name: str
    description: str = ""
    default_kwargs: dict = field(default_factory=dict)
    available_datasets: List[str] = field(default_factory=list)
    available_markets: List[str] = field(default_factory=list)
    special_dataset_cls: Optional[str] = None
    _cls: object = field(default=None, repr=False)


MODEL_MANIFEST = [
    # 树模型
    ModelInfo("LightGBM", "LGBModel", "qlib.contrib.model.gbdt", "tree", "lightgbm", "LightGBM"),
    ModelInfo("XGBoost", "XGBModel", "qlib.contrib.model.xgboost", "tree", "sklearn", "XGBoost"),
    ModelInfo("CatBoost", "CatBoostModel", "qlib.contrib.model.catboost_model", "tree", "sklearn", "CatBoost"),
    ModelInfo("DoubleEnsemble", "DEnsembleModel", "qlib.contrib.model.double_ensemble", "tree", "lightgbm", "DoubleEnsemble"),
    ModelInfo("Linear", "LinearModel", "qlib.contrib.model.linear", "tree", "sklearn", "线性模型"),
    # 神经网络
    ModelInfo("LSTM", "LSTM", "qlib.contrib.model.pytorch_lstm", "neural", "pytorch", "长短期记忆网络",
               default_kwargs={
                   "d_feat": 20,
                   "hidden_size": 64,
                   "num_layers": 2,
                   "dropout": 0.0,
                   "n_epochs": 200,
                   "lr": 1e-3,
                   "early_stop": 10,
                   "batch_size": 800,
                   "metric": "loss",
                   "loss": "mse",
                   "n_jobs": 10,
                   "GPU": 0,
               },
               special_dataset_cls="TSDatasetH"),
    ModelInfo("GRU", "GRU", "qlib.contrib.model.pytorch_gru", "neural", "pytorch", "门控循环单元",
               default_kwargs={
                   "d_feat": 20,
                   "hidden_size": 64,
                   "num_layers": 2,
                   "dropout": 0.0,
                   "n_epochs": 200,
                   "lr": 1e-3,
                   "early_stop": 10,
                   "batch_size": 800,
                   "metric": "loss",
                   "loss": "mse",
                   "n_jobs": 10,
                   "GPU": 0,
               },
               special_dataset_cls="TSDatasetH"),
    ModelInfo("ALSTM", "ALSTM", "qlib.contrib.model.pytorch_alstm_ts", "neural", "alstm_ts", "注意力LSTM",
               default_kwargs={
                   "d_feat": 20,  # ALSTM 模型只需要 20 个特征
                   "hidden_size": 64,
                   "num_layers": 2,
                   "dropout": 0.0,
                   "n_epochs": 200,
                   "lr": 1e-3,
                   "early_stop": 10,
                   "batch_size": 2000,
                   "metric": "loss",
                   "loss": "mse",
                   "n_jobs": 10,
                   "GPU": 0,
               },
               special_dataset_cls="TSDatasetH"),
    ModelInfo("MLP", "DNNModelPytorch", "qlib.contrib.model.pytorch_nn", "neural", "pytorch", "多层感知机",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("Transformer", "TransformerModel", "qlib.contrib.model.pytorch_transformer", "neural", "pytorch", "Transformer",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("Localformer", "LocalformerModel", "qlib.contrib.model.pytorch_localformer", "neural", "pytorch", "Localformer",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("TFT", "TFTModel", "tft", "neural", "tensorflow", "时序融合Transformer"),
    ModelInfo("TCN", "TCN", "qlib.contrib.model.pytorch_tcn", "neural", "pytorch", "时序卷积网络",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("SFM", "SFM_Model", "qlib.contrib.model.pytorch_sfm", "neural", "pytorch", "状态频域模型",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("TabNet", "TabnetModel", "qlib.contrib.model.pytorch_tabnet", "neural", "pytorch", "TabNet",
               default_kwargs={
                   "GPU": 0,
               }),
    # 高级模型
    ModelInfo("GATs", "GATs", "qlib.contrib.model.pytorch_gats", "advanced", "pytorch", "图注意力网络",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("HIST", "HIST", "qlib.contrib.model.pytorch_hist", "advanced", "pytorch", "HIST",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("IGMTF", "IGMTF", "qlib.contrib.model.pytorch_igmtf", "advanced", "pytorch", "IGMTF",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("KRNN", "KRNN", "qlib.contrib.model.pytorch_krnn", "advanced", "pytorch", "KRNN",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("Sandwich", "Sandwich", "qlib.contrib.model.pytorch_sandwich", "advanced", "pytorch", "Sandwich",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("ADARNN", "ADARNN", "qlib.contrib.model.pytorch_adarnn", "advanced", "pytorch", "ADARNN",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("ADD", "ADD", "qlib.contrib.model.pytorch_add", "advanced", "pytorch", "ADD",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("TCTS", "TCTS", "qlib.contrib.model.pytorch_tcts", "advanced", "pytorch", "TCTS",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("TRA", "TRAModel", "qlib.contrib.model.pytorch_tra", "advanced", "pytorch", "TRA", special_dataset_cls="MTSDatasetH",
               default_kwargs={
                   "GPU": 0,
               }),
    ModelInfo("GeneralPtNN", "GeneralPTNN", "qlib.contrib.model.pytorch_general_nn", "advanced", "pytorch", "通用PyTorch网络",
               default_kwargs={
                   "GPU": 0,
               }),
]

CATEGORY_NAMES = {
    "tree": "树模型",
    "neural": "神经网络",
    "advanced": "高级模型",
}


class ModelRegistry:
    _models: Dict[str, ModelInfo] = {}
    _discovered = False

    @classmethod
    def discover_all(cls) -> Dict[str, ModelInfo]:
        if cls._discovered:
            return cls._models
        for info in MODEL_MANIFEST:
            cls._models[info.model_id] = info
        cls._scan_benchmark_configs()
        cls._discovered = True
        return cls._models

    @classmethod
    def _scan_benchmark_configs(cls):
        if not BENCHMARKS_DIR.exists():
            return
        for model_dir in BENCHMARKS_DIR.iterdir():
            if not model_dir.is_dir():
                continue
            model_id = model_dir.name
            if model_id not in cls._models:
                continue
            info = cls._models[model_id]
            datasets = set()
            markets = set()
            for yaml_file in model_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    if cfg is None:
                        continue
                    # 提取数据集类型
                    handler_cfg = cfg.get("task", {}).get("dataset", {}).get("kwargs", {}).get("handler", {})
                    cls_name = handler_cfg.get("class", "")
                    if "Alpha158" in cls_name:
                        datasets.add("Alpha158")
                    elif "Alpha360" in cls_name:
                        datasets.add("Alpha360")
                    # 提取市场
                    market = cfg.get("market", "")
                    if market:
                        markets.add(market)
                    # 提取模型默认参数
                    model_kwargs = cfg.get("task", {}).get("model", {}).get("kwargs", {})
                    if model_kwargs and not info.default_kwargs:
                        info.default_kwargs = model_kwargs
                except Exception:
                    continue
            info.available_datasets = sorted(datasets) or ["Alpha158", "Alpha360"]
            info.available_markets = sorted(markets) or ["csi300", "csi500"]

    @classmethod
    def get(cls, model_id: str) -> Optional[ModelInfo]:
        if not cls._discovered:
            cls.discover_all()
        return cls._models.get(model_id)

    @classmethod
    def get_by_category(cls, category: str) -> List[ModelInfo]:
        if not cls._discovered:
            cls.discover_all()
        return [m for m in cls._models.values() if m.category == category]

    @classmethod
    def all_models(cls) -> Dict[str, ModelInfo]:
        if not cls._discovered:
            cls.discover_all()
        return cls._models

    @classmethod
    def get_model_class(cls, model_id: str):
        success, error_msg = cls.try_import_model(model_id)
        if not success:
            raise ImportError(error_msg)
        info = cls.get(model_id)
        return info._cls

    @classmethod
    def try_import_model(cls, model_id: str) -> tuple:
        """尝试导入模型类，返回 (success, error_msg)"""
        info = cls.get(model_id)
        if info is None:
            return (False, f"未知模型: {model_id}")
        if info._cls is not None:
            return (True, "")
        try:
            module = importlib.import_module(info.module_path)
            model_cls = getattr(module, info.class_name)
            info._cls = model_cls
            return (True, "")
        except (ImportError, AttributeError) as e:
            return (False, f"无法导入模型 {model_id} ({info.module_path}.{info.class_name}): {e}")

    @classmethod
    def create_model(cls, model_id: str, **kwargs):
        model_cls = cls.get_model_class(model_id)
        return model_cls(**kwargs)

    @classmethod
    def get_default_config_path(cls, model_id: str, dataset: str = "Alpha158", market: str = "csi300") -> Optional[Path]:
        model_dir = BENCHMARKS_DIR / model_id
        if not model_dir.exists():
            return None
        # 优先精确匹配
        for f in model_dir.glob("*.yaml"):
            name = f.stem.lower()
            if dataset.lower() in name and market.lower() in name:
                return f
        # 退而求其次
        for f in model_dir.glob("*.yaml"):
            name = f.stem.lower()
            if dataset.lower() in name:
                return f
        # 返回第一个
        yamls = list(model_dir.glob("*.yaml"))
        return yamls[0] if yamls else None
