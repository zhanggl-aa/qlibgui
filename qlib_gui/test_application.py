#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试应用程序启动和基础功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from qlib_gui.app import MainWindow

def test_application():
    """测试应用程序"""
    print("=" * 60)
    print("测试 Qlib GUI 应用程序")
    print("=" * 60)
    print()

    # 创建应用程序
    print("1. 创建 Qt 应用程序...")
    app = QApplication(sys.argv)
    print("✅ Qt 应用程序创建成功")
    print()

    # 创建主窗口
    print("2. 创建主窗口...")
    window = MainWindow()
    print("✅ 主窗口创建成功")
    print()

    # 显示窗口
    print("3. 显示主窗口...")
    window.show()
    print("✅ 主窗口显示成功")
    print()

    # 检查模型存储
    print("4. 检查模型存储...")
    from qlib_gui.core.model_store import TrainedModelStore
    trained_models = TrainedModelStore.trained_ids()
    print(f"✅ 已训练模型: {trained_models}")
    print()

    # 检查模型注册表
    print("5. 检查模型注册表...")
    from qlib_gui.core.model_registry import ModelRegistry
    all_models = ModelRegistry.all_models()
    print(f"✅ 模型总数: {len(all_models)}")
    if "ALSTM" in all_models:
        print(f"✅ ALSTM 模型信息: {all_models['ALSTM']}")
    print()

    # 检查配置文件
    print("6. 检查 ALSTM 配置文件...")
    config_path = ModelRegistry.get_default_config_path("ALSTM", "Alpha158", "csi300")
    if config_path:
        print(f"✅ 配置文件: {config_path}")
        from qlib_gui.core.config_parser import ConfigParser
        config = ConfigParser.load_from_yaml(str(config_path))
        print(f"✅ 配置模型: {config['task']['model']['class']}")
        print(f"✅ 配置数据集: {config['task']['dataset']['class']}")
        if 'step_len' in config['task']['dataset']['kwargs']:
            print(f"✅ 时间序列长度: {config['task']['dataset']['kwargs']['step_len']}")
    else:
        print("❌ 未找到配置文件")
    print()

    print("=" * 60)
    print("🎉 应用程序测试通过!")
    print("=" * 60)
    print()
    print("窗口已打开，您可以测试应用程序功能...")
    print("按 Ctrl+C 关闭程序。")

    # 运行事件循环
    try:
        app.exec()
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
        sys.exit(0)

if __name__ == "__main__":
    test_application()
