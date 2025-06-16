@echo off
setlocal enableextensions enabledelayedexpansion
:: ======================================================
:: Resume AI - Run Streamlit Script
:: Mục đích: Kích hoạt virtual environment và khởi động Streamlit UI
:: ======================================================

:: 0) Chuyển console sang UTF-8
chcp 65001 >nul

:: 1) Kiểm tra Python có sẵn
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được cài đặt hoặc không tìm thấy trong PATH.
    pause
    exit /b 1
)
echo Tìm thấy Python.

:: 2) Kích hoạt virtual environment (nếu có)
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
    echo Đã kích hoạt virtual environment.
) else (
    echo Không tìm thấy virtual environment tại .venv. Sử dụng Python toàn cục.
)

:: 3) Chạy Streamlit UI
echo Khởi động Streamlit UI...
streamlit run "%~dp0app.py" --server.port 8501 --server.headless true

:: Giữ cửa sổ sau khi kết thúc
pause
