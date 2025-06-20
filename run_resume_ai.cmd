@echo off
:: 0) Chuyển console sang UTF-8 (hỗ trợ tiếng Việt)
chcp 65001 >nul
setlocal enableextensions enabledelayedexpansion
:: Đảm bảo PowerShell cũng dùng UTF-8 để hiển thị tiếng Việt
powershell -NoProfile -Command "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8"

:: Hiển thị banner nhiều màu
color 0E
cls
powershell -NoProfile -Command "Write-Host '=====================================================' -ForegroundColor Cyan"
powershell -NoProfile -Command "$t='RESUME AI - KHỞI ĐỘNG'; $c=@('Red','Yellow','Green','Cyan','Magenta','Blue','White'); for($i=0;$i -lt $t.Length;$i++){Write-Host -NoNewline $t[$i] -ForegroundColor $c[$i % $c.Count]} ; Write-Host ''"
powershell -NoProfile -Command "Write-Host '=====================================================' -ForegroundColor Cyan"
color 07
:: ======================================================
:: Resume AI - Entry Script (auto launch Streamlit UI)
:: ======================================================

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
color 0A
set "spin=- \ | /"
for /L %%n in (1,1,8) do (
    set /A idx=%%n %% 4
    for %%c in (!spin:~!idx!,1!) do <nul set /p "=Đang khởi động ứng dụng... %%c\r"
    ping 127.0.0.1 -n 1 > nul
)
echo.
color 07

:: 4) Khởi động Streamlit UI
streamlit run "%~dp0main_engine\app.py"
color 07

powershell -NoProfile -Command "Write-Host 'Ứng dụng đã thoát. Nhấn phím bất kỳ để đóng.' -ForegroundColor Yellow"
pause
