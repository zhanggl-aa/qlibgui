"""Model Persistence Module

Saves trained models to disk and loads them back on startup.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from qlib_gui.core.model_store import TrainedModel
from qlib_gui.core.model_registry import ModelRegistry


class ModelPersistence:
    """Handles saving and loading trained models from disk"""

    # Models directory - use absolute path based on qlib_gui package location
    def __init__(self):
        self._init_model_dir()

    @classmethod
    def _init_model_dir(cls):
        """Initialize model directory with absolute path"""
        if not hasattr(cls, '_model_dir'):
            # Get qlib_gui package directory
            try:
                pkg_dir = Path(__file__).parent.parent  # qlib_gui/
            except NameError:
                pkg_dir = Path.cwd()

            # Create models directory
            cls._model_dir = pkg_dir / "models"
            cls._model_dir.mkdir(parents=True, exist_ok=True)
            print(f"[ModelPersistence] Using models directory: {cls._model_dir}")

    @classmethod
    def get_model_dir(cls) -> Path:
        """Get models directory path"""
        if not hasattr(cls, '_model_dir'):
            cls._init_model_dir()
        return cls._model_dir

    @classmethod
    def _get_model_dir(cls, model_id: str) -> Path:
        """Get directory path for a specific model"""
        return cls.get_model_dir() / model_id

    @classmethod
    def _clean_model(cls, model):
        """Clean model object to make it pickleable"""
        from qlib_gui.core.training_hooks import _PATCHED_ATTR

        # Remove any attributes that cause pickling issues
        attrs_to_remove = []
        for attr_name in dir(model):
            if attr_name.startswith('_') and ('patch' in attr_name or 'fit' in attr_name):
                attrs_to_remove.append(attr_name)
        attrs_to_remove.extend([_PATCHED_ATTR, '_original_fit'])

        for attr in attrs_to_remove:
            if hasattr(model, attr):
                try:
                    delattr(model, attr)
                except Exception:
                    pass

        # Handle special cases for lightgbm/xgboost
        if hasattr(model, 'fit'):
            # If fit is a bound method and not an instance attribute, leave it
            try:
                # Try to check if it's a dynamically added method
                import inspect
                if hasattr(model.fit, '__code__'):
                    func_name = model.fit.__code__.co_name
                    if func_name == 'patched_fit':
                        # Remove patched fit
                        if hasattr(model, '_original_fit'):
                            model.fit = model._original_fit
                            try:
                                delattr(model, '_original_fit')
                            except Exception:
                                pass
            except Exception:
                pass

        return model

    @classmethod
    def save(cls, model_id: str, model, dataset, config: dict, model_type: str, evals_result: dict = None):
        """Save model + params + metrics to models/{model_id}/"""
        try:
            print(f"[ModelPersistence] Saving model {model_id}...")

            # Initialize directory
            model_dir = cls._get_model_dir(model_id)
            model_dir.mkdir(parents=True, exist_ok=True)
            print(f"[ModelPersistence] Directory created: {model_dir}")

            # 1. Clean model before saving
            print(f"[ModelPersistence] Cleaning model for saving")
            cleaned_model = cls._clean_model(model)

            # 2. Save model object
            try:
                import joblib
                joblib.dump(cleaned_model, model_dir / "model.pkl")
                print(f"[ModelPersistence] Model saved: model.pkl")
            except ImportError:
                import pickle
                with open(model_dir / "model.pkl", "wb") as f:
                    pickle.dump(cleaned_model, f)
                print(f"[ModelPersistence] Model saved (pickle): model.pkl")

            # 3. Get model info from registry
            model_info = ModelRegistry.get(model_id)

            # 4. Save params.json
            params = {
                "model_id": model_id,
                "model_type": model_type,
                "class_name": model_info.class_name if model_info else None,
                "module_path": model_info.module_path if model_info else None,
                "saved_at": datetime.now().isoformat(),
                "training_config": config,
                "model_kwargs": config.get("model_kwargs", {})
            }
            if model_info:
                params["class_name"] = model_info.class_name
                params["module_path"] = model_info.module_path

            with open(model_dir / "params.json", "w", encoding="utf-8") as f:
                json.dump(params, f, indent=2, ensure_ascii=False)
            print(f"[ModelPersistence] Config saved: params.json")

            # 5. Save evals_result.json if available
            if evals_result is not None:
                with open(model_dir / "evals_result.json", "w", encoding="utf-8") as f:
                    json.dump(evals_result, f, indent=2, ensure_ascii=False)
                print(f"[ModelPersistence] Metrics saved: evals_result.json")

            # 6. Update models index file
            cls._update_models_index(model_id, params)

            print(f"[ModelPersistence] Success! Model {model_id} saved to {model_dir}")

        except Exception as e:
            print(f"[ModelPersistence] ERROR saving model {model_id}: {e}")
            import traceback
            print(traceback.format_exc())

    @classmethod
    def _update_models_index(cls, model_id: str, params: dict):
        """Update the models index file for quick lookup"""
        index_path = cls.get_model_dir() / "index.json"
        index = {}

        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)

        index[model_id] = {
            "saved_at": params["saved_at"],
            "model_type": params["model_type"],
            "class_name": params["class_name"],
            "module_path": params["module_path"],
            "dataset": params.get("training_config", {}).get("dataset", "Unknown"),
            "market": params.get("training_config", {}).get("market", "Unknown"),
            "version": 1.0
        }

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, model_id: str) -> Optional[TrainedModel]:
        """Load single model from models/{model_id}/"""
        model_dir = cls._get_model_dir(model_id)

        if not model_dir.exists():
            return None

        try:
            # 1. Read params.json (optional)
            params_path = model_dir / "params.json"
            params = {}
            if params_path.exists():
                with open(params_path, "r", encoding="utf-8") as f:
                    params = json.load(f)

            # 2. Load model object
            model_path = model_dir / "model.pkl"
            if not model_path.exists():
                return None

            try:
                import joblib
                model = joblib.load(model_path)
            except ImportError:
                import pickle
                with open(model_path, "rb") as f:
                    model = pickle.load(f)

            # 3. Load evals_result
            evals_result = None
            evals_path = model_dir / "evals_result.json"
            if evals_path.exists():
                with open(evals_path, "r", encoding="utf-8") as f:
                    evals_result = json.load(f)

            # 4. Rebuild dataset from training config
            config = params.get("training_config", {})
            dataset = None
            try:
                from qlib.contrib.data.handler import Alpha158, Alpha360
                from qlib.data.dataset import DatasetH

                dataset_cls = Alpha158 if config.get("dataset", "Alpha158") == "Alpha158" else Alpha360
                market = config.get("market", "csi300")
                handler = dataset_cls(
                    instruments=market,
                    start_time=config.get("start_time", "2008-01-01"),
                    end_time=config.get("end_time", "2020-12-31")
                )
                segments = {
                    "train": (config.get("start_time", "2008-01-01"), "2014-12-31"),
                    "valid": ("2015-01-01", "2016-12-31"),
                    "test": ("2017-01-01", config.get("end_time", "2020-12-31"))
                }
                dataset = DatasetH(handler=handler, segments=segments)
            except Exception as e:
                print(f"Warning: Could not rebuild dataset for {model_id}: {e}")

            # 5. Create and return TrainedModel
            return TrainedModel(
                model_id=model_id,
                model=model,
                dataset=dataset,
                config=config,
                model_type=params.get("model_type", "pytorch"),
                evals_result=evals_result
            )

        except Exception as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    @classmethod
    def load_all(cls) -> Dict[str, TrainedModel]:
        """Scan models/ and load all saved models"""
        models_dict = {}
        model_dir = cls.get_model_dir()

        print(f"[ModelPersistence] Scanning models in: {model_dir}")

        if not model_dir.exists():
            print(f"[ModelPersistence] Models directory does not exist")
            return models_dict

        # First try to load from index file for faster lookup
        index_path = model_dir / "index.json"
        index = {}
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)

                print(f"[ModelPersistence] Found {len(index)} models in index")

                for model_id in index.keys():
                    trained_model = cls.load(model_id)
                    if trained_model is not None:
                        models_dict[model_id] = trained_model
                        print(f"[ModelPersistence] Loaded model: {model_id}")
            except Exception as e:
                print(f"[ModelPersistence] Error loading index: {e}")
                import traceback
                print(traceback.format_exc())

        # Scan directory for additional models not in index
        for subdir in model_dir.iterdir():
            if subdir.is_dir() and subdir.name != "__pycache__":
                model_id = subdir.name
                if model_id not in models_dict:
                    trained_model = cls.load(model_id)
                    if trained_model is not None:
                        models_dict[model_id] = trained_model
                        print(f"[ModelPersistence] Loaded model: {model_id}")

        # Update index if there are models missing from it
        if len(models_dict) > len(index):
            print(f"[ModelPersistence] Updating index with {len(models_dict)} models")
            for model_id, trained_model in models_dict.items():
                if model_id not in index:
                    # Create minimal params for index update
                    params = {
                        "model_id": model_id,
                        "model_type": trained_model.model_type,
                        "class_name": None,
                        "module_path": None,
                        "saved_at": datetime.now().isoformat(),
                        "training_config": trained_model.config or {},
                        "model_kwargs": {}
                    }
                    cls._update_models_index(model_id, params)

        print(f"[ModelPersistence] Total loaded models: {len(models_dict)}")

        return models_dict

    @classmethod
    def list_saved(cls) -> List[str]:
        """List all saved model_ids"""
        model_dir = cls.get_model_dir()
        if not model_dir.exists():
            return []

        saved_models = []

        # First try directory scan (more reliable)
        for subdir in model_dir.iterdir():
            if subdir.is_dir() and subdir.name != "__pycache__":
                # Check if this directory contains a model file
                if (subdir / "model.pkl").exists() or (subdir / "params.json").exists():
                    if subdir.name not in saved_models:
                        saved_models.append(subdir.name)

        return saved_models

    @classmethod
    def delete(cls, model_id: str):
        """Delete a model's saved folder"""
        model_dir = cls._get_model_dir(model_id)
        if model_dir.exists():
            import shutil
            shutil.rmtree(model_dir)
            print(f"Deleted saved model: {model_id}")
