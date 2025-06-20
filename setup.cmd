@echo off
setlocal enableextensions enabledelayedexpansion

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

:: 0) Chuyển console sang UTF-8
chcp 65001 >nul

:: 1) Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python không được cài đặt hoặc không tìm thấy trong PATH. Đang thử cài đặt Python...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo Không tìm thấy winget để cài đặt Python tự động.
        echo Vui lòng cài đặt Python thủ công tại https://www.python.org.
        pause
        exit /b 1
    )
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Lỗi cài đặt Python bằng winget.
        echo Vui lòng cài đặt Python thủ công tại https://www.python.org rồi chạy lại script.
        pause
        exit /b 1
    )
    echo Hoàn tất cài đặt Python.
)
echo Đã có Python.

:: 2) Copy .env.example thành .env nếu chưa tồn tại
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo Đã tạo file .env từ .env.example. Vui lòng chỉnh sửa giá trị.
    ) else (
        echo Không tìm thấy .env.example. Hãy tạo file .env thủ công.
    )
) else (
    echo File .env đã tồn tại.
)

:: 3) Tạo virtual environment nếu chưa có
if not exist "%~dp0.venv\Scripts\activate.bat" (
powershell -NoProfile -Command "Write-Host '📦 Đang tạo môi trường ảo...' -ForegroundColor Green"
    python -m venv "%~dp0.venv"
echo Đã tạo môi trường ảo.
) else (
    echo Môi trường ảo đã tồn tại.
)

:: 4) Kích hoạt virtual environment
call "%~dp0.venv\Scripts\activate.bat"
echo Đã kích hoạt môi trường ảo.

:: 5) Cài đặt dependencies
powershell -NoProfile -Command "Write-Host 'Đang cài đặt dependencies...' -ForegroundColor Green"
pip install --upgrade uv
uv pip install --upgrade pip
uv pip install -r "%~dp0requirements.txt"
echo Hoàn tất cài đặt dependencies.

:: 6) Tạo thư mục attachments
if not exist "%~dp0attachments" (
    mkdir "%~dp0attachments"
    echo Đã tạo thư mục attachments.
) else (
    echo Thư mục attachments đã tồn tại.
)

powershell -NoProfile -Command "Write-Host 'Quá trình cài đặt hoàn tất! Nhấn phím bất kỳ để thoát.' -ForegroundColor Yellow"
pause
