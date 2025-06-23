#!/bin/bash
# start-api.sh - Script to start the API server

echo "🚀 Starting HoanCau AI API Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python is not installed. Please install Python 3.10+ first."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.10"

if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "❌ Python 3.10 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating template..."
    cat > .env << EOF
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# OpenRouter API  
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Email configuration (optional)
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# MCP Configuration (optional)
MCP_API_KEY=your_mcp_api_key_here
EOF
    echo "📝 Please edit .env file with your API keys before running the server."
    echo "🔗 Get Google API key: https://makersuite.google.com/app/apikey"
    echo "🔗 Get OpenRouter API key: https://openrouter.ai/keys"
fi

# Start the API server
echo "🌐 Starting API server on http://localhost:8000..."
echo "📖 API docs will be available at http://localhost:8000/docs"
echo "🎯 Widget demo at http://localhost:8000/widget"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON_CMD api_server.py
