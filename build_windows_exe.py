# Build Script for Windows Executable
# This script creates a Windows .exe file from the Python application

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller installed successfully")

def create_spec_file():
    """Create PyInstaller spec file for the application"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Add src directory to path
src_path = Path.cwd() / "src"
sys.path.insert(0, str(src_path))

block_cipher = None

a = Analysis(
    ['src/main_engine/app.py'],
    pathex=['.', 'src', 'src/main_engine', 'src/modules'],
    binaries=[],
    datas=[
        ('src/main_engine/tabs', 'main_engine/tabs'),
        ('src/modules', 'modules'),
        ('static', 'static'),
        ('.env.example', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.runtime.state',
        'streamlit.components.v1',
        'google.generativeai',
        'requests',
        'pandas',
        'python_dotenv',
        'pdfminer',
        'pdfminer.high_level',
        'PyPDF2',
        'fitz',
        'docx',
        'openpyxl',
        'click',
        'pathlib',
        'typing',
        'datetime',
        'json',
        're',
        'logging',
        'imaplib',
        'email',
        'email.header',
        'email.utils',
        'mimetypes',
        'base64',
        'os',
        'sys',
        'threading',
        'time',
        'concurrent.futures',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HoanCauAI_ResumeProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile_name=None,
    icon='static/logo.ico' if Path('static/logo.ico').exists() else None,
)
'''
    
    with open('HoanCauAI.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ Created PyInstaller spec file: HoanCauAI.spec")

def create_launcher_script():
    """Create a launcher script that starts Streamlit"""
    launcher_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HoanCau AI Resume Processor - Windows Launcher
Khởi động ứng dụng Streamlit cho Windows
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

def setup_environment():
    """Setup necessary environment variables and paths"""
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        app_path = Path(sys.executable).parent
    else:
        # Running in development
        base_path = Path(__file__).parent
        app_path = base_path
    
    # Set environment variables
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    
    # Add paths to sys.path
    sys.path.insert(0, str(base_path))
    sys.path.insert(0, str(base_path / 'src'))
    
    return base_path, app_path

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'streamlit', 'pandas', 'requests', 'dotenv',
        'google.generativeai', 'pathlib', 'json'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True

def create_env_file(app_path):
    """Create .env file if it doesn't exist"""
    env_file = app_path / '.env'
    env_example = app_path / '.env.example'
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"✅ Created .env file from template")
        else:
            # Create basic .env file
            basic_env = '''# HoanCau AI Resume Processor Configuration
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=your_google_api_key_here
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password_here
'''
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(basic_env)
            print(f"✅ Created basic .env file at {env_file}")
            print("⚠️  Please edit .env file and add your API keys!")

def start_streamlit(base_path):
    """Start Streamlit application"""
    try:
        # Import streamlit
        import streamlit.web.cli as stcli
        
        # Change to app directory
        app_file = base_path / 'src' / 'main_engine' / 'app.py'
        if not app_file.exists():
            app_file = base_path / 'main_engine' / 'app.py'
        
        if not app_file.exists():
            print("❌ Cannot find app.py file")
            return False
        
        # Set up Streamlit arguments
        sys.argv = [
            'streamlit',
            'run',
            str(app_file),
            '--server.port=8501',
            '--server.headless=true',
            '--browser.gatherUsageStats=false',
            '--server.address=localhost'
        ]
        
        print("🚀 Starting HoanCau AI Resume Processor...")
        print("📱 Web interface will open at: http://localhost:8501")
        
        # Start Streamlit
        stcli.main()
        
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        print("Trying alternative method...")
        
        # Alternative: use subprocess
        try:
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', str(app_file),
                '--server.port=8501',
                '--server.headless=true',
                '--browser.gatherUsageStats=false'
            ]
            subprocess.run(cmd)
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            return False
    
    return True

def open_browser():
    """Open browser after a delay"""
    time.sleep(3)  # Wait for Streamlit to start
    try:
        webbrowser.open('http://localhost:8501')
        print("🌐 Opened browser at http://localhost:8501")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please manually open: http://localhost:8501")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 HoanCau AI Resume Processor - Windows Launcher")
    print("=" * 60)
    
    # Setup environment
    base_path, app_path = setup_environment()
    print(f"📁 Base path: {base_path}")
    print(f"📁 App path: {app_path}")
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    # Create .env file if needed
    create_env_file(app_path)
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start Streamlit
    success = start_streamlit(base_path)
    
    if not success:
        print("❌ Failed to start the application")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    with open('src/main_engine/launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print("✅ Created launcher script: src/main_engine/launcher.py")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building Windows executable...")
    
    # Clean previous builds
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"🧹 Cleaned {folder} directory")
    
    # Run PyInstaller
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'HoanCauAI.spec'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        print(f"📦 Executable created at: dist/HoanCauAI_ResumeProcessor.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_installer_script():
    """Create a simple installer batch script"""
    installer_content = '''@echo off
title HoanCau AI Resume Processor - Installer
echo ============================================================
echo 🚀 HoanCau AI Resume Processor - Windows Installer
echo ============================================================
echo.

REM Create application directory
set APP_DIR=%USERPROFILE%\\HoanCauAI
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

REM Copy executable and files
echo 📦 Installing application...
copy "HoanCauAI_ResumeProcessor.exe" "%APP_DIR%\\" > nul
if exist ".env.example" copy ".env.example" "%APP_DIR%\\" > nul
if exist "requirements.txt" copy "requirements.txt" "%APP_DIR%\\" > nul
if exist "static" xcopy "static" "%APP_DIR%\\static" /E /I /Q > nul

REM Create desktop shortcut
echo 🔗 Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\HoanCau AI Resume Processor.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%APP_DIR%\\HoanCauAI_ResumeProcessor.exe'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = 'HoanCau AI Resume Processor'; $Shortcut.Save()"

REM Create start menu shortcut
echo 📋 Creating start menu shortcut...
set STARTMENU_PATH=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\HoanCau AI Resume Processor.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_PATH%'); $Shortcut.TargetPath = '%APP_DIR%\\HoanCauAI_ResumeProcessor.exe'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = 'HoanCau AI Resume Processor'; $Shortcut.Save()"

echo.
echo ✅ Installation completed successfully!
echo 📁 Application installed to: %APP_DIR%
echo 🖥️  Desktop shortcut created
echo 📋 Start menu shortcut created
echo.
echo ⚠️  Important: Edit .env file with your API keys before running
echo 🚀 Run the application from desktop shortcut or start menu
echo.
pause
'''
    
    with open('installer.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    print("✅ Created installer script: installer.bat")

def main():
    """Main build process"""
    print("=" * 70)
    print("🏗️  HoanCau AI Resume Processor - Windows Build Script")
    print("=" * 70)
    
    try:
        # Step 1: Install PyInstaller
        install_pyinstaller()
        
        # Step 2: Create launcher script
        create_launcher_script()
        
        # Step 3: Create spec file
        create_spec_file()
        
        # Step 4: Build executable
        if build_executable():
            # Step 5: Create installer
            create_installer_script()
            
            print("\n" + "=" * 70)
            print("🎉 BUILD COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("📦 Files created:")
            print("   - dist/HoanCauAI_ResumeProcessor.exe  (Main executable)")
            print("   - installer.bat                       (Installer script)")
            print()
            print("📝 Next steps:")
            print("   1. Copy the 'dist' folder to your Windows machine")
            print("   2. Run installer.bat to install the application")
            print("   3. Edit .env file with your API keys")
            print("   4. Launch from desktop shortcut")
            print()
            print("🌐 The app will run at: http://localhost:8501")
            print("=" * 70)
        else:
            print("❌ Build failed!")
            
    except Exception as e:
        print(f"❌ Build process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
