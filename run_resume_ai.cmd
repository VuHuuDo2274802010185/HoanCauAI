@echo off
setlocal enableextensions enabledelayedexpansion

:: Hiển thị banner màu để giao diện thân thiện hơn
color 0A
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

:menu
echo ===============================
echo 1. Mo UI Streamlit
echo 2. Chay CLI xu ly CV
echo 3. Chon TOP5 CV bang AI
echo 0. Thoat
set /p MODE="Chon che do (0-3): "
if "%MODE%"=="0" goto end
if "%MODE%"=="1" set ACTION=UI
if "%MODE%"=="2" set ACTION=CLI
if "%MODE%"=="3" set ACTION=SELECT
if not defined ACTION (
    echo [WARN] Lua chon khong hop le.
    goto menu
)
set /p CF="Thuc thi che do %ACTION%? (y/n): "
if /I not "%CF%"=="y" (
    echo Da huy. Quay lai menu.
    goto menu
)
if "%ACTION%"=="CLI" (
    python "%~dp0main_engine\main.py"
    goto menu
)
if "%ACTION%"=="SELECT" (
    python "%~dp0main_engine\select_top5.py"
    goto menu
)
:: default UI
streamlit run "%~dp0main_engine\app.py"
goto menu

:end
echo Ket thuc.
pause
