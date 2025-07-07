#!/bin/bash

# HoanCau AI CV Processor - Gradio Full Interface Launcher
# Enhanced version with complete feature set

echo "🚀 Starting HoanCau AI CV Processor - Full Gradio Interface"
echo "=================================================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import gradio; print(f'✅ Gradio version: {gradio.__version__}')" || {
    echo "❌ Gradio not found. Installing..."
    pip install gradio
}

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating template..."
    cat > .env << EOF
# LLM API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Email Configuration
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password_here
EMAIL_UNSEEN_ONLY=True

# Other settings
LLM_MODEL=gemini-2.0-flash-exp
EOF
    echo "📝 Please edit .env file with your API keys and email configuration"
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p attachments csv excel log static backups

# Check for logo
if [ ! -f "static/logo.png" ]; then
    echo "ℹ️ Logo not found at static/logo.png"
fi

echo ""
echo "🌟 Configuration Summary:"
echo "   • Full-featured Gradio interface"
echo "   • Advanced CV processing with AI"
echo "   • Email integration for automated CV fetching"
echo "   • Multi-provider LLM support (Google AI, OpenRouter)"
echo "   • Interactive chat interface"
echo "   • Real-time progress tracking"
echo "   • Export to CSV/Excel"
echo ""
echo "🌐 Starting server on http://localhost:7863"
echo "📝 Make sure to configure your API keys in the interface"
echo ""

# Start the application
python gradio_full.py
