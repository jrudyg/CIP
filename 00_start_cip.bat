@echo off
echo ========================================
echo CIP Services Launcher
echo ========================================
echo.

:: Kill existing backend (port 5000)
echo Stopping existing backend...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Kill existing frontend (port 8501)
echo Stopping existing frontend...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Brief pause to ensure ports are released
timeout /t 2 /nobreak >nul

:: Start Backend in new window
echo Starting Backend...
start "CIP Backend" cmd /k "cd /d C:\Users\jrudy\CIP\backend && python api.py"

:: Wait for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend in new window
echo Starting Frontend...
start "CIP Frontend" cmd /k "cd /d C:\Users\jrudy\CIP\frontend && python -m streamlit run app.py"

echo.
echo ========================================
echo Services starting in separate windows
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:8501
echo ========================================
echo.
pause
