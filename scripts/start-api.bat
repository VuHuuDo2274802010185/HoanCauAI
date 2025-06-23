@echo off
REM start-api.bat - Windows script to start the API server

echo 🚀 Starting HoanCau AI API Server...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.10+ first.
    pause
    exit /b 1
)

REM Check Python version (simplified check)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found. Creating template...
    (
        echo # Google Gemini API
        echo GOOGLE_API_KEY=your_google_api_key_here
        echo.
        echo # OpenRouter API
        echo OPENROUTER_API_KEY=your_openrouter_api_key_here
        echo.
        echo # Email configuration ^(optional^)
        echo EMAIL_HOST=imap.gmail.com
        echo EMAIL_PORT=993
        echo EMAIL_USER=your_email@gmail.com
        echo EMAIL_PASS=your_app_password
        echo.
        echo # MCP Configuration ^(optional^)
        echo MCP_API_KEY=your_mcp_api_key_here
    ) > .env
    echo 📝 Please edit .env file with your API keys before running the server.
    echo 🔗 Get Google API key: https://makersuite.google.com/app/apikey
    echo 🔗 Get OpenRouter API key: https://openrouter.ai/keys
)

REM Start the API server
echo 🌐 Starting API server on http://localhost:8000...
echo 📖 API docs will be available at http://localhost:8000/docs
echo 🎯 Widget demo at http://localhost:8000/widget
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py

pause
