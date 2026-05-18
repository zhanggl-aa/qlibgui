# ALSTM 模型训练错误修复

## 问题描述
当尝试在应用程序中训练 ALSTM 模型时，会出现 "This type of input is not supported" 错误。

## 问题根因
1. 原来使用的是 `pytorch_alstm` 模块中的 ALSTM，这个模块接受普通 DataFrame（x, y 格式）作为输入
2. 但是当使用 TSDatasetH 时，我们需要使用 pytorch_alstm_ts 模块中的 ALSTMModel
3. pytorch_alstm_ts 模块中的 train_epoch 和 test_epoch 方法需要接受数据加载器作为输入，而不是普通 DataFrame

## 修复步骤

### 1. 更新模型注册表
- 更新 model_registry.py，使用 pytorch_alstm_ts 模块中的模型
- 更新 ALSTMModel 的默认参数，特别是 num_features（d_feat）设置为 20

### 2. 创建专门的训练钩子
- 添加 `patch_alstm_ts_fit` 钩子方法，专门用于 pytorch_alstm_ts 类型的 ALSTM
- 更新训练钩子逻辑，以适应新的模型结构

### 3. 修改模型加载逻辑
- 更新训练钩子的 apply 方法，确保正确处理新的模型
- 添加 'alstm_ts' 类型到 PATCH_MAP

### 4. 更新模型创建
- 使用正确的模块和类名创建模型

## 更改文件
1. `core/model_registry.py`
   - 更新 ALSTM 的默认模块为 pytorch_alstm_ts
   - 添加 model_type 为 'alstm_ts'

2. `core/training_hooks.py`
   - 添加 `patch_alstm_ts_fit` 函数
   - 更新 PATCH_MAP 包含新钩子

## 现在的运行流程
1. 模型信息
   - 模块: qlib.contrib.model.pytorch_alstm_ts
   - 类: ALSTMModel
   - 类型: alstm_ts
   - 默认参数:
     d_feat: 20,
     hidden_size: 64
     num_layers: 2
     ...

2. 训练流程
   - 使用新的 fit 钩子，专门为 alstm_ts 模型设计
   - 数据加载正确，使用正确的数据格式

## 验证
现在运行应用程序，您应该能够：
- 正常训练 ALSTM 模型
- 使用 TSDatasetH 进行训练
- 不会再看到 Unsupported input type 错误
