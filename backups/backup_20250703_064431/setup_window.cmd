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
for /f "tokens=2 delims=:" %%a in ('chcp') do set "ORIG_CP=%%a"
set "ORIG_CP=%ORIG_CP: =%"
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
        call :cleanup 1
    )
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Lỗi cài đặt Python bằng winget.
        echo Vui lòng cài đặt Python thủ công tại https://www.python.org rồi chạy lại script.
        pause
        call :cleanup 1
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
echo 🔗 Đang tạo shortcut trên Desktop...

REM Lấy đường dẫn Desktop
for /f "tokens=2,*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP_PATH=%%j"

REM Kiểm tra nếu không lấy được đường dẫn từ registry
if not defined DESKTOP_PATH (
    REM Thử dùng biến môi trường USERPROFILE
    set "DESKTOP_PATH=%USERPROFILE%\Desktop"
    if not exist "!DESKTOP_PATH!" (
        echo [Lỗi] Không thể xác định đường dẫn Desktop.
        echo Vui lòng kiểm tra quyền truy cập registry hoặc tạo shortcut thủ công.
        goto :skip_shortcut
    )
)

REM Kiểm tra Desktop có tồn tại không
if not exist "%DESKTOP_PATH%" (
    echo [Lỗi] Thư mục Desktop không tồn tại: %DESKTOP_PATH%
    goto :skip_shortcut
)

REM Tạo shortcut
set "SHORTCUT_NAME=HoanCauAi.lnk"
set "SHORTCUT_PATH=%DESKTOP_PATH%\%SHORTCUT_NAME%"
set "TARGET_FILE=%~dp0start_window.cmd"

REM Kiểm tra file target có tồn tại không
if not exist "%TARGET_FILE%" (
    echo [Cảnh báo] File start_window.cmd không tồn tại. Shortcut có thể không hoạt động.
)

REM Tạo VBScript tạm thời (không ảnh hưởng encoding)
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo Set oShellLink = WshShell.CreateShortcut("%SHORTCUT_PATH%"^)
    echo oShellLink.TargetPath = "%TARGET_FILE%"
    echo oShellLink.WorkingDirectory = "%~dp0"
    echo oShellLink.Description = "Resume AI - HoanCauAi Application"
    echo.
    echo ' Xử lý icon
    echo If CreateObject("Scripting.FileSystemObject"^).FileExists("%~dp0static\logo.ico"^) Then
    echo     oShellLink.IconLocation = "%~dp0static\logo.ico"
    echo ElseIf CreateObject("Scripting.FileSystemObject"^).FileExists("%~dp0static\logo.png"^) Then
    echo     ' Dùng icon mặc định vì VBS không thể chuyển đổi PNG
    echo     oShellLink.IconLocation = "C:\Windows\System32\cmd.exe,0"
    echo Else
    echo     oShellLink.IconLocation = "C:\Windows\System32\cmd.exe,0"
    echo End If
    echo.
    echo oShellLink.Save
) > "%VBS_SCRIPT%"

REM Chạy VBScript (không ảnh hưởng encoding)
cscript //nologo "%VBS_SCRIPT%" >nul 2>&1

REM Xóa file tạm thời
del "%VBS_SCRIPT%" >nul 2>&1

REM Kiểm tra kết quả
if exist "%SHORTCUT_PATH%" (
    echo ✅ Đã tạo shortcut thành công trên Desktop.
) else (
    echo [Lỗi] Không thể tạo shortcut bằng VBScript.
    echo Đang thử tạo file batch thay thế...
    
    REM Tạo file .cmd thay thế trên Desktop
    set "BATCH_FILE=%DESKTOP_PATH%\HoanCauAi.cmd"
    (
        echo @echo off
        echo title Resume AI - HoanCauAi
        echo cd /d "%~dp0"
        echo call "%TARGET_FILE%"
        echo pause
    ) > "%BATCH_FILE%"
    
    if exist "%BATCH_FILE%" (
        echo Đã tạo file batch trên Desktop: HoanCauAi.cmd
    ) else (
        echo [Lỗi] Không thể tạo file batch trên Desktop.
    )
)

:skip_shortcut

echo Setup hoàn tất! Nhấn bất kỳ phím nào để thoát.
pause
call :cleanup 0

:cleanup
chcp %ORIG_CP% >nul
popd
exit /b %1
