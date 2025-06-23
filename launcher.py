# Simple App Launcher - Alternative to EXE
# This creates a simple Python launcher that works like an executable

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def setup_paths():
    """Setup application paths"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        app_dir = Path(sys.executable).parent
    else:
        # Running as script
        app_dir = Path(__file__).parent
    
    # Ensure we're in the right directory
    os.chdir(app_dir)
    
    # Add src to Python path
    src_path = app_dir / 'src'
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    
    return app_dir

def check_python():
    """Check if Python and required modules are available"""
    try:
        import streamlit
        import pandas
        import requests
        import dotenv
        return True
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def check_env_file(app_dir):
    """Check and create .env file if needed"""
    env_file = app_dir / '.env'
    env_example = app_dir / '.env.example'
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env from template")
        else:
            print("⚠️  No .env file found. Please create one with your API keys.")
        
        print("⚠️  Please edit .env file with your API keys before running!")
        input("Press Enter after editing .env file...")

def open_browser_delayed():
    """Open browser after Streamlit starts"""
    time.sleep(5)  # Wait for Streamlit to fully start
    try:
        webbrowser.open('http://localhost:8501')
        print("🌐 Opened browser at http://localhost:8501")
    except:
        print("Please manually open: http://localhost:8501")

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🚀 HoanCau AI Resume Processor")
    print("=" * 60)
    
    # Setup paths
    app_dir = setup_paths()
    print(f"📁 App directory: {app_dir}")
    
    # Check dependencies
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Check .env file
    check_env_file(app_dir)
    
    # Find the main app file
    app_file = None
    possible_paths = [
        app_dir / 'src' / 'main_engine' / 'app.py',
        app_dir / 'main_engine' / 'app.py',
        app_dir / 'app.py'
    ]
    
    for path in possible_paths:
        if path.exists():
            app_file = path
            break
    
    if not app_file:
        print("❌ Cannot find app.py file")
        input("Press Enter to exit...")
        return
    
    print(f"📱 Found app at: {app_file}")
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # Start Streamlit
    print("🚀 Starting application...")
    print("🌐 Web interface: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', str(app_file),
            '--server.port=8501',
            '--browser.gatherUsageStats=false',
            '--server.headless=true'
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
