@echo off
REM build-electron.bat - Windows script to build Electron app

echo 🚀 Building HoanCau AI Desktop App...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
npm install

REM Install Electron and build tools if not installed
if not exist "node_modules\electron" (
    echo ⚡ Installing Electron...
    npm install electron --save-dev
)

if not exist "node_modules\electron-builder" (
    echo 🔨 Installing Electron Builder...
    npm install electron-builder --save-dev
)

REM Create Python distribution directory
echo 🐍 Preparing Python environment...
if not exist "python-dist" (
    mkdir python-dist
    echo Creating Python distribution directory...
)

REM Build the application
echo 🔨 Building Electron application...

REM Ask user which platform to build for
echo Select build target:
echo 1) Windows (win)
echo 2) macOS (mac)
echo 3) Linux (linux)  
echo 4) All platforms
echo 5) Current platform only

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Building for Windows...
    npm run build-win
) else if "%choice%"=="2" (
    echo Building for macOS...
    npm run build-mac
) else if "%choice%"=="3" (
    echo Building for Linux...
    npm run build-linux
) else if "%choice%"=="4" (
    echo Building for all platforms...
    npm run build-all
) else if "%choice%"=="5" (
    echo Building for current platform...
    npm run dist
) else (
    echo Invalid choice. Building for current platform...
    npm run dist
)

echo ✅ Build completed! Check the 'dist' folder for the built application.
echo.
echo 📁 Build artifacts:
dir dist\ 2>nul || echo No dist folder found - build may have failed

echo.
echo 🎉 HoanCau AI Desktop App build process completed!
echo 💡 To run the app in development mode: npm run electron-dev
echo 📦 To install the built app, run the installer from the dist folder

pause
