@echo off
setlocal enableextensions enabledelayedexpansion

cls
echo ======================================================
echo                  RESUME AI - RUN SCRIPT
echo ======================================================
:: ======================================================
:: Resume AI - Entry Script
:: Mục đích: Kích hoạt venv, chọn chế độ CLI/SelectTop5/UI và chạy tương ứng
:: Sử dụng: run_resume_ai.bat [cli|select]
::   - cli: chạy batch/single qua CLI (main_engine/main.py)
::   - select: chọn TOP5 qua AI (main_engine/select_top5.py)
::   - (mặc định) khởi động Streamlit UI (main_engine/app.py)
:: ======================================================

:: 0) Chuyển console sang UTF-8 (hỗ trợ tiếng Việt)
chcp 65001 >nul

:: 1) Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python không được cài đặt hoặc không tìm thấy trong PATH.
    pause
    exit /b 1
)
echo [OK] Đã có Python.

:: 2) Kích hoạt virtual environment nếu có
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
    echo [OK] Virtual environment đã được kích hoạt.
) else (
    echo [WARN] Không tìm thấy virtual environment tại .venv, sử dụng Python toàn cục.
)

:: 3) Xử lý tham số đầu vào
set MODE=%1
if /I "%MODE%"=="cli" (
    echo [MODE] Chạy CLI xử lý CV...
    python "%~dp0main_engine\main.py" %*
    goto end
)
if /I "%MODE%"=="select" (
    echo [MODE] Chọn TOP 5 CV bằng AI...
    python "%~dp0main_engine\select_top5.py"
    goto end
)

:: 4) Mặc định: khởi động Streamlit UI
echo [MODE] Khởi động Streamlit UI...
streamlit run "%~dp0main_engine\app.py"

:end
pause
