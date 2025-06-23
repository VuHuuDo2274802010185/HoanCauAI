@echo off
title HoanCau AI - Quick Test Run
echo ============================================================
echo 🚀 HoanCau AI Resume Processor - Quick Test
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo 📦 Checking dependencies...
python -c "import streamlit, pandas, requests, dotenv; print('✅ Core dependencies OK')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Installing missing dependencies...
    python -m pip install -r requirements.txt
)

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ Created .env from template
        echo ⚠️  Please edit .env file with your API keys before running!
        echo.
        pause
    ) else (
        echo ❌ No .env.example found. Please create .env file manually.
        pause
        exit /b 1
    )
)

REM Start the application
echo 🚀 Starting HoanCau AI Resume Processor...
echo 🌐 Opening at: http://localhost:8501
echo 🛑 Press Ctrl+C to stop the application
echo.

REM Run Streamlit app
cd src\main_engine
python -m streamlit run app.py --server.port=8501 --browser.gatherUsageStats=false

pause
