#!/usr/bin/env python3
"""Check if existing models can be loaded"""

import sys
from pathlib import Path

# Add qlib_gui package to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

try:
    from qlib_gui.core.model_persistence import ModelPersistence

    print("Loading LightGBM...")
    lightgbm_model = ModelPersistence.load('LightGBM')
    print(f"LightGBM loaded: {lightgbm_model is not None}")

    print("\nLoading XGBoost...")
    xgboost_model = ModelPersistence.load('XGBoost')
    print(f"XGBoost loaded: {xgboost_model is not None}")

    print("\nListing saved models:", ModelPersistence.list_saved())

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
