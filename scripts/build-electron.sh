#!/bin/bash
# build-electron.sh - Script to build Electron app

echo "🚀 Building HoanCau AI Desktop App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd desktop
npm install

# Install Electron and build tools if not installed
if [ ! -d "node_modules/electron" ]; then
    echo "⚡ Installing Electron..."
    npm install electron --save-dev
fi

if [ ! -d "node_modules/electron-builder" ]; then
    echo "🔨 Installing Electron Builder..."
    npm install electron-builder --save-dev
fi

cd ..

# Create Python distribution (optional - for standalone builds)
echo "🐍 Preparing Python environment..."
if [ ! -d "python-dist" ]; then
    mkdir -p python-dist
    echo "Creating Python distribution directory..."
fi

# Build the application
echo "🔨 Building Electron application..."

# Ask user which platform to build for
echo "Select build target:"
echo "1) Windows (win)"
echo "2) macOS (mac)"
echo "3) Linux (linux)"
echo "4) All platforms"
echo "5) Current platform only"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Building for Windows..."
        cd desktop && npm run build-win
        ;;
    2)
        echo "Building for macOS..."
        cd desktop && npm run build-mac
        ;;
    3)
        echo "Building for Linux..."
        cd desktop && npm run build-linux
        ;;
    4)
        echo "Building for all platforms..."
        cd desktop && npm run build-all
        ;;
    5)
        echo "Building for current platform..."
        cd desktop && npm run dist
        ;;
    *)
        echo "Invalid choice. Building for current platform..."
        cd desktop && npm run dist
        ;;
esac

echo "✅ Build completed! Check the 'desktop/dist' folder for the built application."
echo ""
echo "📁 Build artifacts:"
ls -la desktop/dist/ 2>/dev/null || echo "No desktop/dist folder found - build may have failed"

echo ""
echo "🎉 HoanCau AI Desktop App build process completed!"
echo "💡 To run the app in development mode: cd desktop && npm run electron-dev"
echo "📦 To install the built app, run the installer from the desktop/dist folder"
