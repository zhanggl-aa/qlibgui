#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查已保存的模型"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qlib_gui.core.model_persistence import ModelPersistence
from pprint import pprint

print("=== 加载所有已保存的模型 ===")
models = ModelPersistence.load_all()
print(f"已加载 {len(models)} 个模型")

for model_id, trained_model in models.items():
    print(f"\n=== 模型: {model_id} ===")
    print(f"  模型实例: {trained_model.model}")
    print(f"  模型类型: {trained_model.model_type}")
    print(f"  数据集: {trained_model.dataset}")
    print(f"  配置:")
    pprint(trained_model.config)
    print(f"  评估结果: {trained_model.evals_result}")
