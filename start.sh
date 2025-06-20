#!/bin/bash
# Hoàn Cầu AI CV Processor - Quick Start Script

echo "🚀 Hoàn Cầu AI CV Processor - Quick Start"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "main_engine/app.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Check virtual environment
if [ -d ".venv" ]; then
    echo "✅ Virtual environment found"
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Run health check
echo "🏥 Running health check..."
python3 health_check.py
health_status=$?

if [ $health_status -eq 0 ]; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check found some issues, but continuing..."
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
    echo "📁 Opening .env file for editing..."
    ${EDITOR:-nano} .env
fi

# Create required directories
echo "📁 Ensuring required directories exist..."
mkdir -p attachments csv log static

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys if you haven't already"
echo "2. Run the application with: python3 -m streamlit run main_engine/app.py"
echo "3. Open your browser to: http://localhost:8501"
echo ""
echo "🔧 Available commands:"
echo "- Health check: python3 health_check.py"
echo "- CLI mode: python3 cli_agent.py --help"
echo "- Simple mode: python3 -m streamlit run simple_app.py"
echo ""

# Ask if user wants to start the app
read -p "🚀 Start the Streamlit app now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎬 Starting Hoàn Cầu AI CV Processor..."
    echo "📱 Access the app at: http://localhost:8501"
    echo "🛑 Press Ctrl+C to stop the server"
    echo ""
    python3 -m streamlit run main_engine/app.py --server.port 8501 --server.address 0.0.0.0
else
    echo "👋 Setup complete! Run 'python3 -m streamlit run main_engine/app.py' when you're ready."
fi
