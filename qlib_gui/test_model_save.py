#!/usr/bin/env python3
"""Test model saving and loading functionality"""

import sys
from pathlib import Path

# Add qlib_gui package to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

try:
    from qlib_gui.core.model_persistence import ModelPersistence
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor

    print("[OK] ModelPersistence imported successfully")

    # Initialize ModelPersistence
    print("Initializing ModelPersistence...")
    ModelPersistence._init_model_dir()

    models_dir = ModelPersistence.get_model_dir()
    print(f"Model storage directory: {models_dir}")

    # Create a simple test model
    print("\nCreating test model...")
    test_model = RandomForestRegressor(n_estimators=10)

    # Create dummy data for testing
    X = np.random.rand(100, 10)
    y = np.random.rand(100)
    test_model.fit(X, y)

    print("[OK] Test model created and trained")

    # Save the model
    model_id = "TestModel"
    print(f"\nSaving model '{model_id}'...")
    config = {
        "model_id": model_id,
        "dataset": "Alpha158",
        "market": "csi300",
        "start_time": "2008-01-01",
        "end_time": "2020-12-31",
        "model_kwargs": {"n_estimators": 10}
    }

    evals_result = {
        "train": {"loss": [0.1, 0.05, 0.02]},
        "valid": {"loss": [0.15, 0.1, 0.08]}
    }

    ModelPersistence.save(
        model_id=model_id,
        model=test_model,
        dataset=None,
        config=config,
        model_type="sklearn",
        evals_result=evals_result
    )

    print("[OK] Model saved successfully")

    # List saved models
    print("\nSaved models:")
    saved_models = ModelPersistence.list_saved()
    for model in saved_models:
        print(f"  - {model}")

    # Load the model back
    print(f"\nLoading model '{model_id}'...")
    loaded_model = ModelPersistence.load(model_id)
    if loaded_model:
        print("[OK] Model loaded successfully")
        print(f"  Model type: {loaded_model.model_type}")
        print(f"  Model ID: {loaded_model.model_id}")
        print(f"  Has evals_result: {loaded_model.evals_result is not None}")

        # Verify the model still works
        test_pred = loaded_model.model.predict(X[:5])
        print(f"  Model prediction test: {test_pred}")
        print("[OK] Model works correctly after loading")
    else:
        print("[FAIL] Failed to load model")

    print("\n" + "="*60)
    print("TEST SCRIPT COMPLETED")
    print("="*60)

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
