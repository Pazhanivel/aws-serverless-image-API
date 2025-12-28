@echo off
REM Stop LocalStack using Docker Compose

echo Stopping LocalStack...

REM Navigate to project root
cd /d "%~dp0\.."

REM Stop LocalStack services
docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo LocalStack stopped successfully!
    echo.
    echo To remove volumes and data, run: docker-compose down -v
) else (
    echo.
    echo ERROR: Failed to stop LocalStack.
    exit /b 1
)
