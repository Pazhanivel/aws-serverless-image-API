@echo off
REM Batch script to stop LocalStack using LocalStack CLI

echo.
echo ========================================
echo Stopping LocalStack...
echo ========================================
echo.

REM Check if LocalStack CLI is installed
localstack --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] LocalStack CLI is not installed.
    echo Install it with: pip install localstack
    pause
    exit /b 1
)

REM Check if LocalStack is running
localstack status >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] LocalStack is not running
    pause
    exit /b 0
)

echo Stopping LocalStack...
localstack stop

if %errorlevel% equ 0 (
    echo [SUCCESS] LocalStack stopped
) else (
    echo [ERROR] Failed to stop LocalStack
    pause
    exit /b 1
)

echo.
echo ========================================
echo LocalStack Stopped!
echo ========================================
echo.

pause