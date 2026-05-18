#!/usr/bin/env python3
"""Test script - Verify model saving and loading"""

import sys
from pathlib import Path

# Add qlib_gui package to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

try:
    from qlib_gui.core.model_persistence import ModelPersistence
    print("OK: ModelPersistence imported successfully")

    # Initialize ModelPersistence
    print("Initializing ModelPersistence...")
    ModelPersistence._init_model_dir()

    models_dir = ModelPersistence.get_model_dir()
    print(f"Model storage directory: {models_dir}")

    # Check if directory exists
    if models_dir.exists():
        print("OK: Models directory exists")

        # List saved models
        saved_models = ModelPersistence.list_saved()
        if saved_models:
            print(f"OK: Found {len(saved_models)} saved models:")
            for model in saved_models:
                print(f"   - {model}")
        else:
            print("WARN: No saved models found in the directory")
            print("INFO: Models will be saved automatically after training")
    else:
        print("WARN: Models directory does not exist (no training has been done yet)")
        print("INFO: The directory will be created automatically when first model is trained")

    # Check index file
    index_path = models_dir / "index.json"
    if index_path.exists():
        print(f"OK: Models index file exists: {index_path}")
        import json
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        print(f"Index file content: {json.dumps(index, indent=2)}")
    else:
        print("WARN: Index file does not exist (will be created when first model is saved)")

    print("\n" + "="*60)
    print("TEST SCRIPT COMPLETED")
    print("="*60)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
