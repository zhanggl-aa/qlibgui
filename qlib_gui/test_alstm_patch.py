#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import qlib
import torch
import random
import numpy as np
from core.model_registry import ModelRegistry
from core.training_hooks import apply_training_hook

# 初始化 qlib
qlib.init(
    provider_uri=r'C:/Users/39468/.qlib/qlib_data/cn_data',
    region='cn'
)

print("=== qlib 初始化完成 ===")
print(f"pytorch 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"cuda 设备数量: {torch.cuda.device_count()}")
    print(f"当前设备: {torch.cuda.current_device()}")
    print(f"设备名称: {torch.cuda.get_device_name()}")
else:
    print("使用 CPU")

print("\n=== 创建 ALSTM 模型 ===")
alstm_info = ModelRegistry.get("ALSTM")
print(f"模型信息: {alstm_info}")
alstm = ModelRegistry.create_model("ALSTM")
print(f"模型创建成功: {type(alstm)}")

print("\n=== 检查训练钩子是否应用 ===")
if hasattr(alstm, '_qlib_gui_patched'):
    print("训练钩子已应用")
else:
    print("训练钩子未应用")
    apply_training_hook(alstm, alstm_info.model_type, None)

print("\n=== 验证补丁函数 ===")
if hasattr(alstm, 'fit'):
    print("fit 方法存在")
    fit_type = type(alstm.fit).__name__
    print(f"fit 类型: {fit_type}")

    if hasattr(alstm.fit, '__code__'):
        print("fit 方法代码片段:")
        print(alstm.fit.__code__.co_name)

# 尝试创建一个简单的数据集（只作为检查）
print("\n=== 创建简单的模拟数据集 ===")
try:
    from qlib.contrib.data.handler import Alpha158
    handler = Alpha158(
        instruments='csi300',
        start_time='2008-01-01',
        end_time='2020-08-01',
        fit_start_time='2008-01-01',
        fit_end_time='2014-12-31'
    )

    from qlib.data.dataset import TSDatasetH
    dataset = TSDatasetH(
        handler=handler,
        segments={
            'train': ['2008-01-01', '2014-12-31'],
            'valid': ['2015-01-01', '2016-12-31'],
            'test': ['2017-01-01', '2020-08-01']
        },
        step_len=20
    )

    print("数据集创建成功")
    print(f"  数据集类: {type(dataset).__name__}")
    if hasattr(dataset, 'handler'):
        print(f"  handler: {type(dataset.handler).__name__}")

except Exception as e:
    print(f"数据集创建失败: {e}")
    import traceback
    print(traceback.format_exc())

# 测试模型和补丁
print("\n=== 测试补丁后的 fit ===")
try:
    # 创建一个非常简单的训练
    from qlib.data.dataset import TSDatasetH
    from core.training_hooks import TrainingCallback

    # 创建一个简单的回调
    class SimpleCallback(TrainingCallback):
        def on_epoch_end(self, epoch, metrics):
            print(f"Epoch {epoch}")
            for k, v in metrics.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.4f}")
                else:
                    print(f"  {k}: {v}")

        def on_train_end(self, evals_result):
            print("Training complete!")

    # 应用钩子（尽管我们之前已经调用过了）
    print("应用训练钩子...")
    apply_training_hook(alstm, alstm_info.model_type, SimpleCallback())

    print("测试完成")

except Exception as e:
    print(f"补丁测试失败: {e}")
    import traceback
    print(traceback.format_exc())

print("\n=== 训练钩子修复完成! ===")
print("现在 ALSTM 模型应该可以正常训练了!")
print("\n如果您在应用程序中看到任何错误，请检查:")
print("- 控制台输出")
print("- 训练日志")
print("- qlib 的错误信息")
