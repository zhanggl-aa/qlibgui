#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试训练功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qlib_gui.core.config_parser import ConfigParser

print("=" * 60)
print("快速测试配置解析")
print("=" * 60)
print()

try:
    # 测试加载 ALSTM 配置
    from qlib_gui.core.model_registry import ModelRegistry
    config_path = ModelRegistry.get_default_config_path("ALSTM", "Alpha158", "csi300")
    if config_path:
        print(f"1. 找到 ALSTM 配置: {config_path}")
        config = ConfigParser.load_from_yaml(str(config_path))
        print("2. 配置解析成功")
        print(f"   模型类名: {config['task']['model']['class']}")
        print(f"   数据集类名: {config['task']['dataset']['class']}")

        if 'fit_start_time' in config['task']['dataset']['kwargs']['handler']['kwargs']:
            print(f"   拟合开始时间: {config['task']['dataset']['kwargs']['handler']['kwargs']['fit_start_time']}")
        if 'fit_end_time' in config['task']['dataset']['kwargs']['handler']['kwargs']:
            print(f"   拟合结束时间: {config['task']['dataset']['kwargs']['handler']['kwargs']['fit_end_time']}")
        if 'start_time' in config['task']['dataset']['kwargs']['handler']['kwargs']:
            print(f"   数据开始时间: {config['task']['dataset']['kwargs']['handler']['kwargs']['start_time']}")
        if 'end_time' in config['task']['dataset']['kwargs']['handler']['kwargs']:
            print(f"   数据结束时间: {config['task']['dataset']['kwargs']['handler']['kwargs']['end_time']}")

        print("3. 配置验证通过")
    else:
        print("未找到 ALSTM 配置文件")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    print(traceback.format_exc())

print()
print("=" * 60)
print("测试手动配置构建")
print("=" * 60)
print()

try:
    # 测试手动构建配置
    test_config = ConfigParser.build_full_config(
        model_id="TestModel",
        model_class="TestModelClass",
        model_module="test.module",
        model_kwargs={"param1": 100, "param2": "value"},
        handler_class="Alpha158",
        handler_module="qlib.contrib.data.handler",
        handler_kwargs={},
        segments={
            "train": ("2008-01-01", "2014-12-31"),
            "valid": ("2015-01-01", "2016-12-31"),
            "test": ("2017-01-01", "2020-08-01"),
        },
        market="csi300",
        benchmark="SH000300",
    )

    print("1. 配置构建成功")
    print(f"2. 数据处理配置:")
    print(f"   start_time: {test_config['data_handler_config']['start_time']}")
    print(f"   end_time: {test_config['data_handler_config']['end_time']}")
    print(f"   fit_start_time: {test_config['data_handler_config']['fit_start_time']}")
    print(f"   fit_end_time: {test_config['data_handler_config']['fit_end_time']}")

    print("3. 任务配置:")
    print(f"   模型: {test_config['task']['model']}")
    print(f"   数据集: {test_config['task']['dataset']}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    print(traceback.format_exc())

print()
print("=" * 60)
print("测试完成!")
print("=" * 60)
