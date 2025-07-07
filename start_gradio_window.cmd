@echo off
REM start_gradio_window.cmd

echo 🚀 Starting Hoàn Cầu AI CV Processor with Gradio...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
echo 📥 Installing/updating dependencies...
pip install -r requirements.txt

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%;%CD%\src

REM Run the Gradio application
echo 🌐 Starting Gradio interface...
python run_gradio.py

echo ✅ Application finished.
pause
