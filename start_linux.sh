#!/usr/bin/env bash
# HoanCau AI - Run Script for macOS/Linux
set -e

# 0) Ensure we're in project root
if [ ! -f "src/main_engine/app.py" ]; then
    echo "[ERROR] Please run this script from the project root directory" >&2
    exit 1
fi

# 1) Check for python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 is required but not found." >&2
    exit 1
fi

# 2) Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "[OK] Virtual environment activated."
else
    echo "[WARN] .venv not found, using system Python."
fi

MODE=$1
shift || true

case "$MODE" in
    cli)
        echo "[MODE] Running CLI processor..."
        python3 src/main_engine/main.py "$@"
        ;;
    select)
        echo "[MODE] Selecting TOP 5 resumes..."
        python3 src/main_engine/select_top5.py "$@"
        ;;
    *)
        echo "[MODE] Launching Streamlit UI..."
        streamlit run src/main_engine/app.py
        ;;
esac
