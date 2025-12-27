@echo off
REM Batch script to start LocalStack using LocalStack CLI

echo.
echo ========================================
echo Starting LocalStack...
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

REM Check if LocalStack is already running
localstack status >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] LocalStack is already running
    localstack status
    echo.
    pause
    exit /b 0
)

echo Starting LocalStack with services: s3, dynamodb, lambda, apigateway, logs
echo.

REM Start LocalStack in detached mode
localstack start -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start LocalStack
    pause
    exit /b 1
)

echo.
echo Waiting for LocalStack to be ready...
localstack wait -t 60

if %errorlevel% neq 0 (
    echo [ERROR] LocalStack failed to start properly
    echo Check logs with: localstack logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo LocalStack is ready!
echo ========================================
echo.

localstack status

echo.
echo   Endpoint: http://localhost:4566
echo   Dashboard: https://app.localstack.cloud
echo.
echo Useful commands:
echo   localstack status - Check status
echo   localstack logs   - View logs
echo   localstack stop   - Stop LocalStack
echo.

pause