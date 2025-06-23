@echo off
title HoanCau AI - Build Windows Executable
echo ============================================================
echo 🏗️  HoanCau AI Resume Processor - Windows Build
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is available
echo.

REM Install/update dependencies
echo 📦 Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Run the build script
echo 🔨 Starting build process...
python build_windows_exe.py

if %errorlevel% neq 0 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo.
echo 🎉 Build completed! Check the 'dist' folder for your executable.
echo.
pause
