"""已训练模型存储 - 支持多模型管理"""
from dataclasses import dataclass, field
from typing import Dict, Optional
import pandas as pd


@dataclass
class TrainedModel:
    model_id: str
    model: object
    dataset: object
    config: dict
    model_type: str
    evals_result: dict = field(default_factory=dict)
    pred: Optional[pd.Series] = None


class TrainedModelStore:
    """管理所有已训练完成的模型"""

    _store: Dict[str, TrainedModel] = {}

    @classmethod
    def save(cls, model_id: str, model, dataset, config: dict,
             model_type: str, evals_result: dict = None) -> TrainedModel:
        entry = TrainedModel(
            model_id=model_id,
            model=model,
            dataset=dataset,
            config=config,
            model_type=model_type,
            evals_result=evals_result or {},
        )
        cls._store[model_id] = entry
        return entry

    @classmethod
    def get(cls, model_id: str) -> Optional[TrainedModel]:
        return cls._store.get(model_id)

    @classmethod
    def all_trained(cls) -> Dict[str, TrainedModel]:
        return dict(cls._store)

    @classmethod
    def trained_ids(cls) -> list:
        return list(cls._store.keys())

    @classmethod
    def remove(cls, model_id: str):
        cls._store.pop(model_id, None)

    @classmethod
    def clear(cls):
        cls._store.clear()
