@echo off
setlocal enableextensions enabledelayedexpansion

:: Hiển thị banner màu cho giao diện dễ nhìn
color 0A
cls
echo ======================================================
echo                  RESUME AI - KHỞI ĐỘNG
echo ======================================================
:: ======================================================
:: Resume AI - Entry Script (auto launch Streamlit UI)
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
    echo [OK] Môi trường ảo đã được kích hoạt.
) else (
    echo [CẢNH BÁO] Không tìm thấy môi trường ảo tại .venv, sẽ dùng Python toàn cục.
)

:: 3) Loading animation trước khi chạy UI
set "spin=/ - \ |"
for /L %%n in (1,1,20) do (
    set /A idx=%%n %% 4
    for %%c in (!spin:~!idx!,1!) do <nul set /p "=Đang khởi động ứng dụng... %%c\r"
    ping 127.0.0.1 -n 2 > nul
)
echo.

:: 4) Khởi động Streamlit UI
streamlit run "%~dp0main_engine\app.py"

echo Ứng dụng đã thoát. Nhấn phím bất kỳ để đóng.
pause
