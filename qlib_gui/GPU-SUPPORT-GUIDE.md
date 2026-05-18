# GPU 加速配置指南

## 当前状态
当前安装的 PyTorch 版本是 **CPU only** (`2.7.0+cpu`)，无法使用 NVIDIA GPU 进行加速训练。

## 如何启用 GPU 加速

### 步骤 1: 检查您的系统是否有 NVIDIA GPU

Windows:
1. 右键点击任务栏 → 任务管理器
2. 切换到 "性能" 选项卡
3. 如果有 NVIDIA GPU，会在左侧显示

或者使用命令:
```bash
nvidia-smi
```

### 步骤 2: 安装 CUDA 版本的 PyTorch

卸载当前的 CPU 版本，安装 CUDA 版本:

```bash
# 卸载当前的 PyTorch
pip uninstall torch torchvision torchaudio

# 安装 CUDA 11.8 版本 (推荐)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或者 CUDA 12.1 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 步骤 3: 验证 PyTorch GPU 支持

在安装完成后，运行以下代码验证:

```python
import torch
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"GPU 设备: {torch.cuda.get_device_name(0)}")
```

### 步骤 4: 模型配置

所有 PyTorch 模型现在默认设置了 `GPU: 0` (使用第一个 GPU)。

您可以在模型训练页面修改:
- `GPU`: 设置为要使用的 GPU ID (默认为 0)
- 如果设置为 -1 或没有 GPU，会自动使用 CPU

### 可用的 GPU 模型

**神经网络分类:**
- ✅ LSTM
- ✅ GRU
- ✅ ALSTM
- ✅ MLP
- ✅ Transformer
- ✅ Localformer
- ✅ TCN
- ✅ SFM
- ✅ TabNet

**高级模型:**
- ✅ GATs
- ✅ HIST
- ✅ IGMTF
- ✅ KRNN
- ✅ Sandwich
- ✅ ADARNN
- ✅ ADD
- ✅ TCTS
- ✅ TRA
- ✅ GeneralPtNN

**非 GPU 模型**
- 📝 LightGBM, XGBoost, CatBoost, Linear (不需要也不支持 GPU)

## GPU 与 CPU 性能对比

通常来说，训练速度提升:
- 小数据集 (几年数据): 2-5x 提升
- 大数据集 (10年以上): 5-15x 提升
- 模型越大，提升越明显

## 常见问题

### Q: 为什么我的 GPU 还是没有被使用？

A: 可能的原因:
1. 没有安装 CUDA 版本的 PyTorch
2. 没有 NVIDIA GPU 或 GPU 驱动未正确安装
3. 模型配置中 `GPU` 被设置为 -1

### Q: 我有多个 GPU，怎么选择？

A: 修改模型配置中的 `GPU` 参数，设置为要使用的 GPU ID (0, 1, 2 ...)

### Q: GPU 内存不足怎么办？

A: 减小 `batch_size` 参数:
- 默认: 800-2000
- 建议值 (小显存): 64, 128, 256
- 建议值 (大显存): 512, 1024, 2048+

### Q: 如何验证模型确实在使用 GPU？

训练时:
1. 打开任务管理器 → 性能 → 查看 GPU 利用率
2. 或者使用 `nvidia-smi` 命令查看 GPU 使用情况

## 关于当前应用中的设置

我已经在 `model_registry.py` 中为所有 PyTorch 模型添加了默认的 `GPU: 0` 参数。

即使没有 GPU，模型仍然可以正常训练（自动回退到 CPU）。
