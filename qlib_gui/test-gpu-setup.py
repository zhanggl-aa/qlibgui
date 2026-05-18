#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '.')
from core.model_registry import ModelRegistry

print("=== GPU Support Check ===")
all_models = list(ModelRegistry.all_models().values())

gpu_models = []
non_gpu_models = []

for model in all_models:
    if model.model_type in ('pytorch', 'alstm_ts'):
        if 'GPU' in model.default_kwargs:
            gpu_models.append(model)
        else:
            non_gpu_models.append(model)

print("Models with GPU support (PyTorch):")
for m in gpu_models:
    print(f"  - {m.model_id} (GPU: {m.default_kwargs.get('GPU')})")

print("\nTotal PyTorch models with GPU: ", len(gpu_models))
print("Total PyTorch models without: ", len(non_gpu_models))

if non_gpu_models:
    print("\nModels without GPU parameter (maybe not PyTorch):")
    for m in non_gpu_models:
        print(f"  - {m.model_id} (model_type: {m.model_type})")

print("\n=== Test Creating a GPU Model ===")
try:
    model = ModelRegistry.create_model("Transformer")
    print("Created Transformer model")
    if hasattr(model, 'device'):
        print(f"  Model device: {model.device}")
    if hasattr(model, 'use_gpu'):
        print(f"  Use GPU: {model.use_gpu}")
except Exception as e:
    print(f"Error: {e}")

print("\nDone!")
