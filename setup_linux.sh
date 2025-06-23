#!/usr/bin/env bash
# HoanCau AI - Setup Script for macOS/Linux
set -e

echo "=============================="
echo " HoanCau AI - Setup Script "
echo "=============================="

# 1) Check for python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required. Please install Python 3.10+ and rerun." >&2
    exit 1
fi

# 2) Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 3) Activate virtual environment
source .venv/bin/activate

# 4) Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5) Copy .env.example to .env if needed
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from template. Please edit this file with your credentials."
    else
        echo "Warning: .env.example not found. Create your .env manually." >&2
    fi
fi

# 6) Create required directories
mkdir -p attachments csv log static

echo "Setup completed successfully."
