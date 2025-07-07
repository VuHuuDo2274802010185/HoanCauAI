#!/bin/bash
# Quick start script for Gradio

echo "🚀 Quick Start - HoanCau AI CV Processor (Gradio)"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start application
echo "🌐 Starting Gradio interface..."
python gradio_simple.py
