@echo off
title Smart Financial Reporting Tool (SFRT)
echo ================================================================
echo    Smart Financial Reporting Tool (SFRT) - Startup Launcher
echo ================================================================
echo.

set PYTHON_CMD="C:\Users\Harsh Verma\anaconda3\python.exe"

if not exist %PYTHON_CMD% (
    set PYTHON_CMD=python
)

echo Initializing database and starting FastAPI backend server on http://127.0.0.1:8000 ...
echo Application URL:   http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo Demo Credentials:  demo@example.com / DemoPassword123!
echo.
echo Press Ctrl+C to stop the server.
echo.

%PYTHON_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
pause
