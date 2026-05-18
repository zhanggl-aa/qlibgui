#!/usr/bin/env python3
"""Debug model loading errors"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from qlib_gui.core.model_persistence import ModelPersistence
import traceback

print('=== Loading LightGBM ===')
try:
    lightgbm_model = ModelPersistence.load('LightGBM')
    print('Success:', lightgbm_model is not None)
    if lightgbm_model:
        print(f'Model type: {lightgbm_model.model_type}')
except Exception as e:
    print('Error:', type(e).__name__, str(e))
    print('Traceback:', traceback.format_exc())

print('\n=== Loading XGBoost ===')
try:
    xgboost_model = ModelPersistence.load('XGBoost')
    print('Success:', xgboost_model is not None)
    if xgboost_model:
        print(f'Model type: {xgboost_model.model_type}')
except Exception as e:
    print('Error:', type(e).__name__, str(e))
    print('Traceback:', traceback.format_exc())
