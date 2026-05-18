# 检查 PyTorch 在当前环境中的状态
Write-Host "=== PyTorch 和 GPU 状态检查 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 PyTorch
Write-Host "导入 PyTorch..." -ForegroundColor Yellow
try {
    $script = @'
import torch
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"GPU 数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("未检测到 GPU")
'@
    python -c $script
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "PyTorch 没有安装！" -ForegroundColor Red
    Write-Host "请运行: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "检查 qlib 模型..." -ForegroundColor Yellow

try {
    $script = @'
import sys
sys.path.insert(0, '.')
from core.model_registry import ModelRegistry

print('创建 ALSTM 模型...')
model = ModelRegistry.create_model('ALSTM')
print(f'模型创建成功!')

if hasattr(model, 'device'):
    print(f'模型使用的设备: {model.device}')
if hasattr(model, 'use_gpu'):
    print(f'use_gpu 标志: {model.use_gpu}')
if hasattr(model, 'ALSTM_model'):
    print(f'模型参数设备: {next(model.ALSTM_model.parameters()).device}')

print()
print('创建 Transformer 模型...')
transformer = ModelRegistry.create_model('Transformer')
print(f'模型创建成功!')

if hasattr(transformer, 'device'):
    print(f'模型使用的设备: {transformer.device}')
if hasattr(transformer, 'use_gpu'):
    print(f'use_gpu 标志: {transformer.use_gpu}')

if torch.cuda.is_available():
    print()
    print('==========================')
    print('✅ 完美！GPU 已可用！')
    print('所有 PyTorch 模型都会自动使用 GPU 加速！')
    print('==========================')
'@
    python -c $script
} catch {
    Write-Host "警告: 模型检查有错误: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "现在你可以运行: python main.py" -ForegroundColor Green
