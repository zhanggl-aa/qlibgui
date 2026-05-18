# GPU 设置快速开始

## 当前步骤

正在下载并安装 CUDA 11.8 版本的 PyTorch，文件大小约 2.8GB，需要几分钟。

## 安装完成后，请依次执行:

### 1. 验证安装
在命令行运行:
```bash
python verify_gpu_setup.py
```

你应该能看到类似这样的输出:
```
版本: 2.7.1+cu118
CUDA 可用: True
CUDA 版本: 11.8
GPU 数量: 1
  GPU 0: NVIDIA GeForce RTX 3060
...
```

### 2. 如果 `CUDA 可用: False`

检查是否有 NVIDIA GPU:
```bash
nvidia-smi
```

如果有 GPU 但 PyTorch 无法识别:
- 尝试重装 NVIDIA 驱动
- 或者安装不同的 CUDA 版本

### 3. 运行应用程序

验证成功后，启动应用程序:
```bash
python main.py
```

现在所有 PyTorch 模型 (LSTM, GRU, ALSTM, Transformer 等) 都会自动使用 GPU 加速训练！

## 你也可以手动重新安装 PyTorch

如果当前下载太慢或中断了:

```bash
# 卸载 (如果安装了旧版本)
pip uninstall torch torchvision torchaudio -y

# 重新安装 CUDA 11.8 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或者 CUDA 12.1 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 查看训练是否使用 GPU

在训练模型时:
1. 打开任务管理器 -> 性能 -> GPU
2. 应该能看到 GPU 使用率上升
3. 或者打开一个新的终端窗口运行:
```bash
nvidia-smi
```

## 优化训练速度

如果 GPU 显存不够，可以:
- 在模型配置页面减小 `batch_size` 参数
- 建议值: 128, 256, 512

## 常见问题

**Q: 怎么知道模型是否在使用 GPU?**

A: 查看训练日志中的设备信息，或者在任务管理器查看 GPU 利用率。

**Q: 训练更快吗?**

A: 通常会快 2-15 倍，具体取决于模型大小和数据集大小。

**Q: 现在所有模型都支持 GPU 吗?**

A: 所有 PyTorch 模型都支持 GPU。LightGBM/XGBoost/CatBoost/Linear 模型不需要 GPU。
