#!/bin/bash
# start_gradio_linux.sh

echo "🚀 Starting Hoàn Cầu AI CV Processor with Gradio..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📥 Installing/updating dependencies..."
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"

# Run the Gradio application
echo "🌐 Starting Gradio interface..."
python run_gradio.py

echo "✅ Application finished."
