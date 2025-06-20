@echo off
:: 0) Switch console to UTF-8
chcp 65001 >nul
setlocal enableextensions enabledelayedexpansion
:: Ensure PowerShell also uses UTF-8 for Vietnamese text
powershell -NoProfile -Command "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8"

:: Thiết lập màu sắc và tiêu đề cho giao diện thân thiện hơn
color 0E
cls
powershell -NoProfile -Command "Write-Host '=====================================================' -ForegroundColor Cyan"
powershell -NoProfile -Command "$t='RESUME AI - CÀI ĐẶT'; $c=@('Red','Yellow','Green','Cyan','Magenta','Blue','White'); for($i=0;$i -lt $t.Length;$i++){Write-Host -NoNewline $t[$i] -ForegroundColor $c[$i % $c.Count]} ; Write-Host ''"
powershell -NoProfile -Command "Write-Host '=====================================================' -ForegroundColor Cyan"
color 07
:: ======================================================
:: Resume AI - Setup Script
:: Mục đích: Tự động thiết lập môi trường dự án
::   1) Kiểm tra Python và virtual env
::   2) Copy .env từ .env.example nếu chưa có
::   3) Tạo và kích hoạt venv
::   4) Cài đặt dependencies
::   5) Tạo thư mục attachments
:: ======================================================

:: 1) Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Write-Host 'Python không được cài đặt hoặc không tìm thấy trong PATH. Đang thử cài đặt Python...' -ForegroundColor Red"
    where winget >nul 2>&1
    if errorlevel 1 (
        powershell -NoProfile -Command "Write-Host 'Không tìm thấy winget để cài đặt Python tự động.' -ForegroundColor Yellow"
        powershell -NoProfile -Command "Write-Host 'Vui lòng cài đặt Python thủ công tại https://www.python.org.'"
        pause
        exit /b 1
    )
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        powershell -NoProfile -Command "Write-Host 'Lỗi cài đặt Python bằng winget.' -ForegroundColor Red"
        powershell -NoProfile -Command "Write-Host 'Vui lòng cài đặt Python thủ công tại https://www.python.org rồi chạy lại script.'"
        pause
        exit /b 1
    )
    powershell -NoProfile -Command "Write-Host 'Hoàn tất cài đặt Python.' -ForegroundColor Green"
)
powershell -NoProfile -Command "Write-Host 'Đã có Python.' -ForegroundColor Green"

:: 2) Copy .env.example thành .env nếu chưa tồn tại
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >nul
        powershell -NoProfile -Command "Write-Host 'Đã tạo file .env từ .env.example. Vui lòng chỉnh sửa giá trị.'"
    ) else (
        powershell -NoProfile -Command "Write-Host 'Không tìm thấy .env.example. Hãy tạo file .env thủ công.' -ForegroundColor Yellow"
    )
) else (
    powershell -NoProfile -Command "Write-Host 'File .env đã tồn tại.'"
)

:: 3) Tạo virtual environment nếu chưa có
if not exist "%~dp0.venv\Scripts\activate.bat" (
powershell -NoProfile -Command "Write-Host '📦 Đang tạo môi trường ảo...' -ForegroundColor Green"
    python -m venv "%~dp0.venv"
powershell -NoProfile -Command "Write-Host 'Đã tạo môi trường ảo.' -ForegroundColor Green"
) else (
    powershell -NoProfile -Command "Write-Host 'Môi trường ảo đã tồn tại.'"
)

:: 4) Kích hoạt virtual environment
call "%~dp0.venv\Scripts\activate.bat"
powershell -NoProfile -Command "Write-Host 'Đã kích hoạt môi trường ảo.' -ForegroundColor Green"

:: 5) Cài đặt dependencies
powershell -NoProfile -Command "Write-Host 'Đang cài đặt dependencies...' -ForegroundColor Green"
pip install --upgrade uv
uv pip install --upgrade pip
uv pip install -r "%~dp0requirements.txt"
powershell -NoProfile -Command "Write-Host 'Hoàn tất cài đặt dependencies.' -ForegroundColor Green"

:: 6) Tạo thư mục attachments
if not exist "%~dp0attachments" (
    mkdir "%~dp0attachments"
    powershell -NoProfile -Command "Write-Host 'Đã tạo thư mục attachments.'"
) else (
    powershell -NoProfile -Command "Write-Host 'Thư mục attachments đã tồn tại.'"
)

powershell -NoProfile -Command "Write-Host 'Quá trình cài đặt hoàn tất! Nhấn phím bất kỳ để thoát.' -ForegroundColor Yellow"
pause
color 07
