#!/usr/bin/env python3
"""Check model files directly"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

print('=== Checking model directories ===')
models_dir = Path('E:\\trae\\o1\\ak04\\qlib0\\qlib_gui\\models')
for model_dir in models_dir.iterdir():
    if model_dir.is_dir() and model_dir.name != '__pycache__':
        print(f'\nModel: {model_dir.name}')
        print('Files:')
        for file in model_dir.iterdir():
            print(f'  - {file.name} ({file.stat().st_size} bytes)')

print('\n\n=== Trying to load model.pkl directly ===')
for model_name in ['LightGBM', 'XGBoost']:
    model_path = models_dir / model_name / 'model.pkl'
    if model_path.exists():
        print(f'\nTrying to load {model_name}:')
        try:
            import joblib
            model = joblib.load(model_path)
            print(f'Success! Model type: {type(model)}')
            if hasattr(model, '__dict__'):
                print(f'Model attributes: {list(model.__dict__.keys())}')
        except ImportError:
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                print(f'Success! Model type: {type(model)}')
                if hasattr(model, '__dict__'):
                    print(f'Model attributes: {list(model.__dict__.keys())}')
            except Exception as e:
                print(f'Error loading with pickle: {type(e).__name__}: {e}')
        except Exception as e:
            print(f'Error loading with joblib: {type(e).__name__}: {e}')
            import traceback
            print(traceback.format_exc())
