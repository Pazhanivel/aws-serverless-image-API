@echo off
REM Start LocalStack using Docker Compose

echo Starting LocalStack with Docker Compose...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Navigate to project root
cd /d "%~dp0\.."

REM Start LocalStack services
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo LocalStack started successfully!
    echo.
    echo Services available at: http://localhost:4566
    echo.
    echo To view logs, run: docker-compose logs -f localstack
    echo To stop LocalStack, run: scripts\stop_localstack.bat
    echo.
    echo Waiting 10 seconds for services to initialize...
    timeout /t 10 /nobreak >nul
    echo.
    echo Now setting up AWS resources...
    python scripts\create_resources.py
    
    if %errorlevel% equ 0 (
        echo.
        echo Deploying Lambda functions and API Gateway...
        python scripts\deploy_stack.py
        
        if %errorlevel% equ 0 (
            echo.
            echo ============================================================
            echo   Setup Complete! Your API is ready to use.
            echo ============================================================
        ) else (
            echo.
            echo WARNING: Stack deployment failed. You can retry with:
            echo   python scripts\deploy_stack.py
        )
    ) else (
        echo.
        echo WARNING: Resource creation failed. You can retry with:
        echo   python scripts\create_resources.py
        echo   python scripts\deploy_stack.py
    )
) else (
    echo.
    echo ERROR: Failed to start LocalStack.
    exit /b 1
)
