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

REM Tạo shortcut bằng PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;" ^
    "try {" ^
    "    $WshShell = New-Object -ComObject WScript.Shell;" ^
    "    $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%');" ^
    "    $Shortcut.TargetPath = '%TARGET_FILE%';" ^
    "    $Shortcut.WorkingDirectory = '%~dp0';" ^
    "    $Shortcut.Description = 'Resume AI - HoanCauAi Application';" ^
    "    " ^
    "    if (Test-Path '%~dp0static\logo.ico') {" ^
    "        $Shortcut.IconLocation = '%~dp0static\logo.ico';" ^
    "        Write-Host 'Sử dụng logo.ico làm icon';" ^
    "    } elseif (Test-Path '%~dp0static\logo.png') {" ^
    "        try {" ^
    "            Add-Type -AssemblyName System.Drawing;" ^
    "            $png = [System.Drawing.Image]::FromFile('%~dp0static\logo.png');" ^
    "            $bitmap = New-Object System.Drawing.Bitmap($png, 32, 32);" ^
    "            $iconPath = '%~dp0static\logo_generated.ico';" ^
    "            $iconHandle = $bitmap.GetHicon();" ^
    "            $icon = [System.Drawing.Icon]::FromHandle($iconHandle);" ^
    "            $fileStream = [System.IO.FileStream]::new($iconPath, [System.IO.FileMode]::Create);" ^
    "            $icon.Save($fileStream);" ^
    "            $fileStream.Close();" ^
    "            $png.Dispose();" ^
    "            $bitmap.Dispose();" ^
    "            $icon.Dispose();" ^
    "            $Shortcut.IconLocation = $iconPath;" ^
    "            Write-Host 'Đã chuyển đổi logo.png thành icon';" ^
    "        } catch {" ^
    "            Write-Host 'Không thể chuyển đổi PNG sang ICO:' $_.Exception.Message;" ^
    "            $Shortcut.IconLocation = 'C:\Windows\System32\cmd.exe,0';" ^
    "            Write-Host 'Sử dụng icon mặc định';" ^
    "        }" ^
    "    } else {" ^
    "        $Shortcut.IconLocation = 'C:\Windows\System32\cmd.exe,0';" ^
    "        Write-Host 'Không tìm thấy logo, sử dụng icon mặc định';" ^
    "    }" ^
    "    " ^
    "    $Shortcut.Save();" ^
    "    Write-Host 'Đã tạo shortcut thành công: %SHORTCUT_NAME%';" ^
    "} catch {" ^
    "    Write-Host 'Lỗi tạo shortcut:' $_.Exception.Message;" ^
    "    exit 1;" ^
    "}"

set "PS_EXITCODE=%ERRORLEVEL%"

if %PS_EXITCODE% NEQ 0 (
    echo [Lỗi] Không thể tạo shortcut bằng PowerShell.
    echo Đang thử tạo file batch thay thế...
    
    REM Tạo file .cmd thay thế trên Desktop với icon
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
        
        REM Thử tạo icon cho file batch bằng Desktop.ini (nếu có thể)
        if exist "%~dp0static\logo.ico" (
            echo Đã sử dụng logo.ico cho file batch
        ) else if exist "%~dp0static\logo.png" (
            echo Logo.png được phát hiện nhưng cần chuyển đổi sang .ico để hiển thị đúng
        )
    ) else (
        echo [Lỗi] Không thể tạo file batch trên Desktop.
    )
) else (
    echo ✅ Đã tạo shortcut thành công trên Desktop với icon tùy chỉnh.
)

:skip_shortcut

echo Setup hoàn tất! Nhấn bất kỳ phím nào để thoát.
pause
call :cleanup 0

:cleanup
chcp %ORIG_CP% >nul
popd
exit /b %1
