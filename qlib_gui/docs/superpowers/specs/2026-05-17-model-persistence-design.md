# Model Persistence Design

## Problem

TrainedModelStore is in-memory only. When the app restarts, all trained models are lost and must be retrained.

## Solution

Add a `ModelPersistence` module that saves trained models to disk and loads them on startup, filling TrainedModelStore so the rest of the app works unchanged.

## Directory Structure

```
models/
├── lstm/
│   ├── model.pkl              # Serialized model object (joblib)
│   ├── params.json            # Model parameters and training config
│   └── evals_result.json      # Training metrics history
├── lightgbm/
│   ├── model.pkl
│   ├── params.json
│   └── evals_result.json
└── ...
```

Root is `models/` under the project directory. Each model gets its own folder named by `model_id`. Re-training overwrites existing files.

## params.json Schema

```json
{
  "model_id": "lstm",
  "model_type": "pytorch",
  "class_name": "LSTM",
  "module_path": "qlib.contrib.model.pytorch_lstm_ts",
  "saved_at": "2026-05-17T14:30:00",
  "training_config": {
    "dataset": "Alpha158",
    "market": "csi300",
    "start_time": "2008-01-01",
    "end_time": "2020-12-31",
    "fit_start_time": "2008-01-01",
    "fit_end_time": "2014-12-31"
  },
  "model_kwargs": {
    "d_feat": 158,
    "hidden_size": 64,
    "num_layers": 2
  }
}
```

## Serialization

All model types use `joblib.dump(model)` / `joblib.load(path)` for the full model object. This avoids needing to reconstruct model architecture on load.

| model_type | save | load |
|---|---|---|
| pytorch | joblib.dump | joblib.load |
| lightgbm | joblib.dump | joblib.load |
| sklearn | joblib.dump | joblib.load |

## Dataset Handling

Dataset objects are NOT serialized (too large). On load, dataset is rebuilt from `training_config` using ModelRegistry and config_parser logic.

## New Module: core/model_persistence.py

```python
class ModelPersistence:
    MODEL_DIR = "models"

    @classmethod
    def save(cls, model_id, model, dataset, config, model_type, evals_result=None):
        """Save model + params + metrics to models/{model_id}/"""

    @classmethod
    def load(cls, model_id) -> Optional[TrainedModel]:
        """Load single model from models/{model_id}/"""

    @classmethod
    def load_all(cls) -> Dict[str, TrainedModel]:
        """Scan models/ and load all saved models"""

    @classmethod
    def list_saved(cls) -> List[str]:
        """List all saved model_ids"""

    @classmethod
    def delete(cls, model_id):
        """Delete a model's saved folder"""
```

### save() flow
1. Create `models/{model_id}/` directory
2. `joblib.dump(model, path/model.pkl)`
3. Write `params.json` with model_id, model_type, class_name, module_path, saved_at, training_config, model_kwargs
4. Write `evals_result.json` if evals_result is provided

### load() flow
1. Read `params.json` for model_type and training_config
2. `joblib.load(path/model.pkl)`
3. Rebuild dataset from training_config via ModelRegistry + config_parser
4. Assemble TrainedModel and return

### load_all() flow
1. Scan `models/` for subdirectories
2. For each, call `load()`
3. Skip and warn on failure (corrupt files, missing dependencies)
4. Return dict of model_id -> TrainedModel

## Integration Points

### After training (MainWindow._on_training_finished)
```python
# Existing
TrainedModelStore.save(model_id, model, dataset, config, model_type, evals_result)
# New — add right after
ModelPersistence.save(model_id, model, dataset, config, model_type, evals_result)
```

### On startup (MainWindow.__init__)
```python
# Add at end of __init__
saved_models = ModelPersistence.load_all()
for mid, trained_model in saved_models.items():
    TrainedModelStore._store[mid] = trained_model
self._refresh_model_combos()
```

### Error handling
- Load failures: skip the model, print warning to console, continue loading others
- Save failures: log error but don't block training completion (in-memory store still works)

## What Does NOT Change
- `training_hooks.py` — existing temporary save logic stays
- `TrainingPage` — no UI changes
- `BacktestPage` / `SimulationPage` — data source unchanged (TrainedModelStore)
- `TrainedModelStore` — remains the in-memory cache, just gets populated on startup

## Dependencies
- `joblib` — already commonly available with sklearn; add to requirements if missing
