# Qlib GUI 更新文档

## 更新概述

本次更新主要实现了两个目标：
1. 使用 qlib 的标准 workflow 方式来初始化模型和数据集
2. 确保时序模型（LSTM、GRU、ALSTM 等）能够正确训练和预测

## 修改的文件

### 1. `app.py` - 主要修改

#### `_start_training` 方法更新
- 新增功能：优先加载模型的默认 YAML 配置文件
- 使用 `qlib.init.init_instance_by_config` 来初始化模型和数据集
- 向后兼容：如果找不到配置文件，仍使用传统方式
- 支持用户自定义参数覆盖配置文件中的默认值

#### `_get_pred_for_model` 方法更新
- 修复时序模型数据集重建问题
- 根据模型类型动态选择使用 `TSDatasetH` 或 `DatasetH`
- 为时序模型添加必要的特征预处理（FilterCol、RobustZScoreNorm、Fillna）和标签处理（DropnaLabel、CSRankNorm）

#### `_switch_to_simulation` 方法更新
- 与 `_get_pred_for_model` 保持一致的数据集重建逻辑
- 确保模拟炒股功能能够正确处理时序模型

### 2. `model_registry.py` - 已配置

已为以下模型添加时序模型配置：
- LSTM
- GRU  
- ALSTM
- TRA

配置包括：
- `special_dataset_cls = "TSDatasetH"`
- 默认参数包含 `d_feat=20`（对应 FilterCol 选择的 20 个特征）

### 3. 新增测试文件

#### `test_alstm_training.py`
- 测试 ALSTM 模型信息
- 测试配置文件加载
- 测试模型创建
- 测试数据集准备

#### `test_application.py`
- 测试应用程序启动
- 测试模型存储
- 测试模型注册表
- 测试配置文件读取

## 使用说明

### 训练模型

1. 启动应用程序：`python main.py`
2. 选择要训练的模型（如 ALSTM）
3. 点击"开始训练"
4. 应用程序会：
   - 自动查找模型的默认配置文件（如 `examples/benchmarks/ALSTM/workflow_config_alstm_Alpha158.yaml`）
   - 使用 qlib 的标准 workflow 初始化模型和数据集
   - 应用用户在界面上设置的参数

### 加载预训练模型

1. 应用程序启动时会自动扫描 `models/` 目录
2. 已训练的模型会自动加载
3. 如果数据集信息缺失，会根据配置自动重建

## 技术细节

### 时序模型数据集结构

```python
# TSDatasetH 需要
- step_len: 20（时间序列长度）
- handler: Alpha158 或 Alpha360，包含特殊的 processors
  - infer_processors:
    - FilterCol（选择 20 个特定特征）
    - RobustZScoreNorm（标准化）
    - Fillna（填充缺失值）
  - learn_processors:
    - DropnaLabel（删除标签缺失的样本）
    - CSRankNorm（标签排序归一化）
```

### 配置文件查找逻辑

1. 首先查找精确匹配：包含 dataset 和 market 名称
2. 然后查找匹配 dataset 的配置
3. 最后返回找到的第一个配置文件

### 向后兼容性

- 所有现有代码和功能保持不变
- 新增功能是可选的，不会破坏现有功能
- 如果找不到配置文件，会自动回退到传统方式

## 测试建议

1. 运行 `test_application.py` 验证应用程序启动正常
2. 运行 `test_alstm_training.py` 验证 ALSTM 模型基础功能
3. 在应用程序中尝试训练 LSTM、GRU、ALSTM 模型
4. 训练完成后尝试回测和模拟炒股功能
5. 关闭应用程序后重新打开，验证模型持久化功能
