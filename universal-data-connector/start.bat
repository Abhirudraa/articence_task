@echo off
REM Quick start script for Universal Data Connector with bonus features (Windows)

echo.
echo 🚀 Universal Data Connector - Bonus Features
echo ================================================
echo.

REM Check if Docker is available
where docker >nul 2>nul
if %errorlevel% equ 0 (
    echo ✓ Docker found
    
    REM Check if Docker Compose is available
    where docker-compose >nul 2>nul
    if %errorlevel% equ 0 (
        echo ✓ Docker Compose found
        echo.
        echo Starting services with Docker Compose...
        echo   - API server (port 8000)
        echo   - Redis cache (port 6379)
        echo.
        docker-compose up --build
    ) else (
        echo ✗ Docker Compose not found
        echo.
        echo Running locally instead...
        call :runLocal
    )
) else (
    echo ✗ Docker not found
    echo.
    echo Running locally...
    call :runLocal
)

goto:eof

:runLocal
    REM Check if Python is available
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        echo ✓ Python found
        echo.
        
        echo Installing dependencies...
        pip install -r requirements.txt
        echo.
        
        echo Starting Redis (Docker)...
        docker run -d -p 6379:6379 redis:latest >nul 2>nul
        if %errorlevel% equ 0 (
            echo ✓ Redis started
        ) else (
            echo ⚠️  Note: Redis not available, cache disabled
        )
        echo.
        
        echo Starting API server...
        echo Visit: http://localhost:8000/ui/index.html
        echo.
        python -m uvicorn app.main:app --reload
    ) else (
        echo ✗ Python not found
        echo Please install Python 3.11 or higher from https://www.python.org
    )
goto:eof
