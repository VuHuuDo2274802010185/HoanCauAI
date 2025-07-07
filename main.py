#!/usr/bin/env python3
"""
Main entry point for HoanCau AI CV Processor
Now uses Gradio by default, with Streamlit as backup option
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main entry point with interface selection"""
    parser = argparse.ArgumentParser(description="HoanCau AI CV Processor")
    parser.add_argument(
        "--interface", 
        choices=["gradio", "streamlit"], 
        default="gradio",
        help="Choose interface (default: gradio)"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simplified Gradio interface"
    )
    
    args = parser.parse_args()
    
    if args.interface == "streamlit":
        print("🚀 Starting Streamlit interface...")
        try:
            import streamlit.web.cli as stcli
            sys.argv = ["streamlit", "run", "src/main_engine/app.py"]
            stcli.main()
        except ImportError:
            print("❌ Streamlit not available. Please install: pip install streamlit")
            sys.exit(1)
    
    elif args.simple:
        print("🚀 Starting Simple Gradio interface...")
        try:
            from gradio_simple import main as run_simple_gradio
            run_simple_gradio()
        except ImportError as e:
            print(f"❌ Error importing simple Gradio app: {e}")
            sys.exit(1)
    
    else:
        print("🚀 Starting Gradio interface...")
        try:
            from src.main_engine.gradio_app import main as run_gradio
            run_gradio()
        except ImportError:
            print("⚠️ Full Gradio app not available, trying simple version...")
            try:
                from gradio_simple import main as run_simple_gradio
                run_simple_gradio()
            except ImportError as e:
                print(f"❌ Error: {e}")
                print("💡 Try: python gradio_simple.py")
                sys.exit(1)

if __name__ == "__main__":
    main()
