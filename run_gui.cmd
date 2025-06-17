@echo off
REM Script chạy GUI Hoàn Cầu AI CV Processor
REM Kích hoạt môi trường ảo (Windows)
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
REM Chạy Streamlit GUI
streamlit run main_engine/app.py
pause
