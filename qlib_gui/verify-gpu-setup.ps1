# GPU 验证脚本
Write-Host "=== PyTorch 和 GPU 状态验证 ===" -ForegroundColor Cyan

# 检查 PyTorch 版本
$python = if (Get-Command "python.exe" -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command "python3.exe" -ErrorAction SilentlyContinue) { "python3" } else { Write-Host "未找到 Python 可执行文件!" -ForegroundColor Red; exit 1 }

Write-Host "使用 Python: $python" -ForegroundColor Yellow
Write-Host ""

# 检查 PyTorch
$script = @"
import torch
import sys
print("--- PyTorch 信息 ---")
print(f"版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"GPU 数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    print(f"当前 GPU: {torch.cuda.current_device()}")
else:
    print("未检测到 CUDA 支持")
    print("如果您有 NVIDIA GPU，请:")
    print("1. 检查 NVIDIA 显卡驱动")
    print("2. 重新安装 CUDA 版本的 PyTorch")

print()
print("--- 创建一个 PyTorch 张量并尝试移动到 GPU ---")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"使用设备: {device}")

# 测试一个简单的张量操作
x = torch.randn(1000, 1000, device=device)
y = torch.randn(1000, 1000, device=device)
z = x @ y
print(f"矩阵乘法完成，输出形状: {z.shape}")
print(f"测试成功!")

print()
print("--- 检查 qlib 模型 ---")
sys.path.insert(0, '.')
from core.model_registry import ModelRegistry

try:
    print("创建 ALSTM 模型...")
    model = ModelRegistry.create_model("ALSTM")
    print(f"模型创建成功!")

    if hasattr(model, 'device'):
        print(f"模型使用的设备: {model.device}")
    if hasattr(model, 'use_gpu'):
        print(f"use_gpu 标志: {model.use_gpu}")
    if hasattr(model, 'ALSTM_model'):
        print(f"模型参数设备: {next(model.ALSTM_model.parameters()).device}")

    print()
    print("创建 Transformer 模型...")
    transformer = ModelRegistry.create_model("Transformer")
    print(f"模型创建成功!")

    if hasattr(transformer, 'device'):
        print(f"模型使用的设备: {transformer.device}")
    if hasattr(transformer, 'use_gpu'):
        print(f"use_gpu 标志: {transformer.use_gpu}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== 验证完成 ===")
"@

&$python -c $script

Write-Host ""
Write-Host "提示: 如果显示 'CUDA 可用: True'，那么就可以使用 GPU 加速训练了!" -ForegroundColor Green
