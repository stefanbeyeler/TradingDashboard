@echo off
echo ========================================
echo   Trading Dashboard - Start Script
echo ========================================
echo.

REM Check if KITradingModel is running
echo Checking if KITradingModel is running on port 8000...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] KITradingModel not detected on port 8000
    echo Please ensure KITradingModel is running for full functionality
    echo.
) else (
    echo [OK] KITradingModel is running
)

echo.
echo Choose startup mode:
echo   1. Development (separate terminals)
echo   2. Docker (docker-compose)
echo   3. Backend only
echo   4. Frontend only
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto dev
if "%choice%"=="2" goto docker
if "%choice%"=="3" goto backend
if "%choice%"=="4" goto frontend
goto end

:dev
echo.
echo Starting Development Mode...
echo.
start "Trading Dashboard - Backend" cmd /k "cd backend && if not exist venv (python -m venv venv) && venv\Scripts\activate && pip install -r requirements.txt && python run.py"
timeout /t 5 /nobreak >nul
start "Trading Dashboard - Frontend" cmd /k "cd frontend && npm install && npm run dev"
echo.
echo Backend: http://localhost:8080
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8080/api/docs
goto end

:docker
echo.
echo Starting with Docker Compose...
docker-compose up -d --build
echo.
echo Dashboard: http://localhost:3000
echo API: http://localhost:8080
echo API Docs: http://localhost:8080/api/docs
goto end

:backend
echo.
echo Starting Backend only...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
python run.py
goto end

:frontend
echo.
echo Starting Frontend only...
cd frontend
npm install
npm run dev
goto end

:end
echo.
echo ========================================
echo   Dashboard is starting...
echo ========================================
