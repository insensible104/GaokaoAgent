# GaokaoAgent - UV 环境测试脚本

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host "  GaokaoAgent - UV Environment Setup" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host ""

# 1. 检查 UV 版本
Write-Host "Step 1: Checking UV version..." -ForegroundColor Green
uv --version

# 2. 同步依赖
Write-Host "`nStep 2: Syncing dependencies with UV..." -ForegroundColor Green
Write-Host "(This may take a few minutes for first-time setup)" -ForegroundColor Yellow
cd backend
uv sync

# 3. 运行简化测试
Write-Host "`nStep 3: Running simplified tests..." -ForegroundColor Green
uv run test_simple.py

# 4. 可选：运行完整测试
Write-Host "`n" -NoNewline
$response = Read-Host "Do you want to run the full test? (y/n)"
if ($response -eq 'y') {
    Write-Host "Running full GaokaoAgent test..." -ForegroundColor Green
    uv run test_gaokao_agent.py
}

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the API server:" -ForegroundColor Yellow
Write-Host "  cd backend/src" -ForegroundColor White
Write-Host "  uv run python main.py" -ForegroundColor White
Write-Host ""

