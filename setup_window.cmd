@echo off
setlocal enableextensions enabledelayedexpansion
pushd %~dp0

cls
echo ======================================================
echo                 RESUME AI - SETUP SCRIPT
echo ======================================================
:: ======================================================
:: Resume AI - Setup Script
:: Mục đích: Tự động thiết lập môi trường dự án
::   1) Kiểm tra Python và virtual env
::   2) Copy .env từ .env.example nếu chưa có
::   3) Tạo và kích hoạt venv
::   4) Cài đặt dependencies
::   5) Tạo thư mục attachments, csv, log, static
:: ======================================================

:: 0) Chuyển console sang UTF-8
chcp 65001 >nul

:: 1) Kiểm tra Python
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    echo Python không được cài đặt hoặc không tìm thấy trong PATH. Đang thử cài đặt Python...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo Không tìm thấy winget để cài đặt Python tự động.
        echo Vui lòng cài đặt Python thủ công tại https://www.python.org.
        pause
        popd
        exit /b 1
    )
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Lỗi cài đặt Python bằng winget.
        echo Vui lòng cài đặt Python thủ công tại https://www.python.org rồi chạy lại script.
        pause
        popd
        exit /b 1
    )
    echo Hoàn tất cài đặt Python.
    set "PYTHON_CMD=python"
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
    echo 📦 Tạo virtual environment...
    %PYTHON_CMD% -m venv "%~dp0.venv"
    echo Đã tạo virtual environment.
) else (
    echo Virtual environment đã tồn tại.
)

:: 4) Kích hoạt virtual environment
call "%~dp0.venv\Scripts\activate.bat"
echo Đã kích hoạt virtual environment.

:: 5) Cài đặt dependencies
echo Đang cài đặt dependencies...
%PYTHON_CMD% -m pip install --upgrade uv
%PYTHON_CMD% -m uv pip install --upgrade pip
%PYTHON_CMD% -m uv pip install -r "%~dp0requirements.txt"
echo Hoàn tất cài đặt dependencies.

:: 6) Tạo thư mục attachments, csv, log, static
if not exist "%~dp0attachments" (
    mkdir "%~dp0attachments"
    echo Đã tạo thư mục attachments.
) else (
    echo Thư mục attachments đã tồn tại.
)

if not exist "%~dp0csv" (
    mkdir "%~dp0csv"
    echo Đã tạo thư mục csv.
) else (
    echo Thư mục csv đã tồn tại.
)

if not exist "%~dp0log" (
    mkdir "%~dp0log"
    echo Đã tạo thư mục log.
) else (
    echo Thư mục log đã tồn tại.
)

if not exist "%~dp0static" (
    mkdir "%~dp0static"
    echo Đã tạo thư mục static.
) else (
    echo Thư mục static đã tồn tại.
)

:: 7) Tạo shortcut "HoanCauAi.cmd" ra Desktop nếu chưa tồn tại
for /f "tokens=2,*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop') do set DESKTOP_PATH=%%j
set "SHORTCUT=%DESKTOP_PATH%\HoanCauAi.cmd.lnk"
if not exist "%SHORTCUT%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
        "$s.TargetPath='%~dp0start_window.cmd';" ^
        "$s.WorkingDirectory='%~dp0';" ^
        "$s.IconLocation='%~dp0static\\logo.png';" ^
        "$s.Save()"
)

echo Setup hoàn tất! Nhấn bất kỳ phím nào để thoát.
popd
pause
