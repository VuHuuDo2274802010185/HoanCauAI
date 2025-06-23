@echo off
title HoanCau AI - Create Portable Windows App
echo ============================================================
echo 📦 HoanCau AI Resume Processor - Portable App Creator
echo ============================================================
echo.

REM Create portable app directory
set PORTABLE_DIR=HoanCauAI_Portable
if exist "%PORTABLE_DIR%" (
    echo 🧹 Cleaning existing portable directory...
    rmdir /s /q "%PORTABLE_DIR%"
)

mkdir "%PORTABLE_DIR%"
echo ✅ Created portable app directory: %PORTABLE_DIR%

REM Copy application files
echo 📋 Copying application files...
xcopy "src" "%PORTABLE_DIR%\src" /E /I /Q
xcopy "static" "%PORTABLE_DIR%\static" /E /I /Q
copy "requirements.txt" "%PORTABLE_DIR%\" >nul
copy "launcher.py" "%PORTABLE_DIR%\" >nul
copy ".env.example" "%PORTABLE_DIR%\.env" >nul

REM Create startup batch file
echo 📝 Creating startup script...
(
echo @echo off
echo title HoanCau AI Resume Processor
echo cd /d "%%~dp0"
echo echo ============================================================
echo echo 🚀 HoanCau AI Resume Processor - Portable Version
echo echo ============================================================
echo echo.
echo.
echo REM Check Python
echo python --version ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ Python not found. Please install Python from https://python.org
echo     echo    Make sure to check "Add Python to PATH" during installation
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ✅ Python found
echo echo 📦 Installing dependencies...
echo python -m pip install -r requirements.txt ^>nul 2^>^&1
echo.
echo echo 🚀 Starting HoanCau AI Resume Processor...
echo echo 🌐 Opening at: http://localhost:8501
echo echo 🛑 Press Ctrl+C to stop
echo echo.
echo echo ⚠️  IMPORTANT: Edit .env file with your API keys first!
echo timeout /t 3 /nobreak ^>nul
echo.
echo python launcher.py
echo.
echo pause
) > "%PORTABLE_DIR%\Start_HoanCauAI.bat"

REM Create setup instructions
echo 📄 Creating setup instructions...
(
echo # HoanCau AI Resume Processor - Portable Version
echo.
echo ## 🚀 Quick Start Guide
echo.
echo ### Prerequisites:
echo 1. **Python 3.8+** must be installed on your system
echo    - Download from: https://python.org
echo    - ⚠️ IMPORTANT: Check "Add Python to PATH" during installation
echo.
echo ### Setup Instructions:
echo.
echo 1. **Edit Configuration:**
echo    - Open `.env` file with Notepad
echo    - Replace `your_google_api_key_here` with your actual Google API key
echo    - Replace email settings with your Gmail credentials
echo.
echo 2. **Get Google API Key:**
echo    - Go to: https://makersuite.google.com/app/apikey
echo    - Create new API key
echo    - Copy and paste into `.env` file
echo.
echo 3. **Run Application:**
echo    - Double-click `Start_HoanCauAI.bat`
echo    - Wait for dependencies to install ^(first time only^)
echo    - Browser will open automatically at http://localhost:8501
echo.
echo ### Features:
echo - 🌐 Web-based interface
echo - 📧 Email CV fetching
echo - 🤖 AI-powered CV analysis
echo - 💬 Chat with AI about CV data
echo - 📊 Export results to CSV/Excel
echo.
echo ### Troubleshooting:
echo - If Python not found: Reinstall Python with "Add to PATH" option
echo - If dependencies fail: Run `pip install -r requirements.txt` manually
echo - If browser doesn't open: Manually go to http://localhost:8501
echo.
echo ### Support:
echo - GitHub: https://github.com/VuHuuDo2274802010185/HoanCauAI
echo - Email: vuhuudo2004@gmail.com
) > "%PORTABLE_DIR%\README.md"

REM Create environment file template
echo 🔧 Creating configuration template...
(
echo # HoanCau AI Resume Processor Configuration
echo # Edit this file with your actual API keys and settings
echo.
echo LLM_PROVIDER=google
echo LLM_MODEL=gemini-2.0-flash-exp
echo GOOGLE_API_KEY=your_google_api_key_here
echo.
echo EMAIL_HOST=imap.gmail.com
echo EMAIL_PORT=993
echo EMAIL_USER=your_email@gmail.com
echo EMAIL_PASS=your_app_password_here
echo.
echo # Don't change these unless you know what you're doing
echo AI_TEMPERATURE=0.3
echo AI_MAX_TOKENS=4096
echo ATTACHMENT_DIR=./attachments
echo OUTPUT_CSV=csv/cv_analysis.csv
) > "%PORTABLE_DIR%\.env"

REM Create desktop shortcut script
echo 🔗 Creating shortcut creator...
(
echo @echo off
echo set CURRENT_DIR=%%cd%%
echo set SHORTCUT_PATH=%%USERPROFILE%%\Desktop\HoanCau AI Resume Processor.lnk
echo powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%CURRENT_DIR%\Start_HoanCauAI.bat'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'HoanCau AI Resume Processor - Portable'; $Shortcut.Save()"
echo echo ✅ Desktop shortcut created!
echo pause
) > "%PORTABLE_DIR%\Create_Desktop_Shortcut.bat"

echo.
echo ✅ Portable app created successfully!
echo 📁 Location: %PORTABLE_DIR%
echo.
echo 📋 Contents:
echo    - Start_HoanCauAI.bat          (Main launcher)
echo    - README.md                    (Setup instructions)
echo    - .env                         (Configuration file)
echo    - Create_Desktop_Shortcut.bat  (Shortcut creator)
echo    - src/                         (Application source)
echo    - static/                      (Web assets)
echo.
echo 🚀 Next steps:
echo    1. Copy "%PORTABLE_DIR%" folder to target Windows computer
echo    2. Edit .env file with API keys
echo    3. Run Start_HoanCauAI.bat
echo.
echo 🎉 Your portable Windows app is ready!
echo.
pause
