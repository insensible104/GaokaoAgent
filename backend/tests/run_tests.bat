@echo off
setlocal

echo ==========================================
echo GaokaoAgent test runner
echo ==========================================

if not exist "run_tests.py" (
    echo [ERROR] Run this script from backend\tests.
    exit /b 1
)

python run_tests.py %*
