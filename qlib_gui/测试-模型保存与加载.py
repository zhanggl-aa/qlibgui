#!/usr/bin/env python3
"""测试脚本 - 验证模型保存和加载"""

import sys
from pathlib import Path

# Add qlib_gui package to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

try:
    from qlib_gui.core.model_persistence import ModelPersistence
    print("✅ ModelPersistence 导入成功")

    # Initialize ModelPersistence
    print("初始化 ModelPersistence...")
    ModelPersistence._init_model_dir()

    models_dir = ModelPersistence.get_model_dir()
    print(f"模型存储目录: {models_dir}")

    # Check if directory exists
    if models_dir.exists():
        print("✅ 模型目录存在")

        # List saved models
        saved_models = ModelPersistence.list_saved()
        if saved_models:
            print(f"✅ 发现 {len(saved_models)} 个已保存的模型:")
            for model in saved_models:
                print(f"   - {model}")
        else:
            print("⚠️  模型目录中没有找到已保存的模型")
            print("提示: 训练一个模型后会自动保存到这里")
    else:
        print("⚠️  模型目录不存在（还没有训练过任何模型）")
        print("提示: 训练第一个模型后会自动创建此目录")

    # Check index file
    index_path = models_dir / "index.json"
    if index_path.exists():
        print(f"✅ 模型索引文件存在: {index_path}")
        import json
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        print(f"索引文件内容: {json.dumps(index, indent=2)}")
    else:
        print("⚠️  模型索引文件不存在（会在第一个模型保存时创建）")

    print("\n" + "="*60)
    print("测试脚本完成")
    print("="*60)

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
