#!/usr/bin/env python3
"""
Script to run the Gradio version of HoanCau AI CV Processor
"""

import sys
from pathlib import Path
import logging

# Add project root to path
HERE = Path(__file__).parent
ROOT = HERE.parent
SRC_DIR = ROOT / "src"

for path in (ROOT, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

def main():
    """Main entry point"""
    try:
        from src.main_engine.gradio_app import main as run_gradio_app
        run_gradio_app()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
