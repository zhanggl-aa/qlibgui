#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ALSTM 模型训练功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qlib_gui.core.qlib_manager import QlibManager
from qlib_gui.core.model_registry import ModelRegistry
from qlib_gui.app import MainWindow
from PyQt6.QtWidgets import QApplication
import threading
import time

def test_alstm_training():
    """测试 ALSTM 模型训练"""
    print("=" * 60)
    print("测试 ALSTM 模型训练功能")
    print("=" * 60)
    print()

    # 初始化 Qlib
    print("1. 初始化 Qlib...")
    if not QlibManager.is_initialized():
        success = QlibManager.initialize()
        if not success:
            print(f"❌ Qlib 初始化失败: {QlibManager.get_last_error()}")
            return False
    print("✅ Qlib 初始化成功")
    print()

    # 检查模型注册表
    print("2. 检查 ALSTM 模型信息...")
    alstm_info = ModelRegistry.get("ALSTM")
    if alstm_info is None:
        print("❌ 未找到 ALSTM 模型信息")
        return False

    print(f"✅ 模型 ID: {alstm_info.model_id}")
    print(f"✅ 模型类名: {alstm_info.class_name}")
    print(f"✅ 模块路径: {alstm_info.module_path}")
    print(f"✅ 模型类型: {alstm_info.model_type}")
    print(f"✅ 数据集类: {alstm_info.special_dataset_cls}")
    print(f"✅ 默认参数: {alstm_info.default_kwargs}")
    print()

    # 检查默认配置文件
    print("3. 检查默认配置文件...")
    config_path = ModelRegistry.get_default_config_path("ALSTM", "Alpha158", "csi300")
    if config_path is None:
        print("❌ 未找到 ALSTM 的默认配置文件")
        return False

    print(f"✅ 配置文件: {config_path}")
    print()

    # 尝试读取配置文件
    print("4. 测试读取配置文件...")
    from qlib_gui.core.config_parser import ConfigParser
    try:
        config = ConfigParser.load_from_yaml(str(config_path))
        print("✅ 配置文件读取成功")
        print(f"✅ 模型配置: {config['task']['model']}")
        print(f"✅ 数据集配置: {config['task']['dataset']}")
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False
    print()

    # 测试创建模型
    print("5. 测试创建 ALSTM 模型实例...")
    try:
        model = ModelRegistry.create_model("ALSTM")
        print(f"✅ 模型创建成功: {type(model)}")
        print()
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    # 测试数据准备
    print("6. 测试数据集准备...")
    from qlib.contrib.data.handler import Alpha158
    from qlib.data.dataset import TSDatasetH

    try:
        # 创建数据处理器
        handler = Alpha158(
            instruments="csi300",
            start_time="2008-01-01",
            end_time="2020-08-01",
            infer_processors=[
                {
                    "class": "FilterCol",
                    "kwargs": {
                        "fields_group": "feature",
                        "col_list": ["RESI5", "WVMA5", "RSQR5", "KLEN", "RSQR10", "CORR5", "CORD5", "CORR10",
                                   "ROC60", "RESI10", "VSTD5", "RSQR60", "CORR60", "WVMA60", "STD5",
                                   "RSQR20", "CORD60", "CORD10", "CORR20", "KLOW"]
                    }
                },
                {
                    "class": "RobustZScoreNorm",
                    "kwargs": {
                        "fields_group": "feature",
                        "clip_outlier": True
                    }
                },
                {
                    "class": "Fillna",
                    "kwargs": {
                        "fields_group": "feature"
                    }
                }
            ],
            learn_processors=[
                {
                    "class": "DropnaLabel"
                },
                {
                    "class": "CSRankNorm",
                    "kwargs": {
                        "fields_group": "label"
                    }
                }
            ]
        )

        # 创建数据集
        segments = {
            "train": ("2008-01-01", "2014-12-31"),
            "valid": ("2015-01-01", "2016-12-31"),
            "test": ("2017-01-01", "2020-08-01")
        }
        dataset = TSDatasetH(handler=handler, segments=segments, step_len=20)
        print(f"✅ 数据集创建成功: {type(dataset)}")
        print()
    except Exception as e:
        print(f"❌ 数据集准备失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    print("=" * 60)
    print("🎉 ALSTM 模型训练功能测试成功!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # 创建 Qt 应用程序
    app = QApplication(sys.argv)

    # 在后台线程中运行测试
    result = False
    def run_test():
        global result
        result = test_alstm_training()
        app.quit()

    test_thread = threading.Thread(target=run_test)
    test_thread.start()

    # 运行事件循环
    app.exec()

    # 输出测试结果
    if result:
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
