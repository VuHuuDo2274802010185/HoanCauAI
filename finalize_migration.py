#!/usr/bin/env python3
"""
Update script to finalize Streamlit to Gradio migration
"""

import sys
from pathlib import Path
import shutil

def main():
    """Main update function"""
    print("🔄 Finalizing Streamlit to Gradio migration...")
    
    ROOT = Path(__file__).parent
    
    # 1. Backup original Streamlit app
    streamlit_app = ROOT / "src" / "main_engine" / "app.py"
    backup_app = ROOT / "src" / "main_engine" / "app_streamlit_backup.py"
    
    if streamlit_app.exists() and not backup_app.exists():
        shutil.copy2(streamlit_app, backup_app)
        print(f"✅ Backed up Streamlit app to {backup_app}")
    
    # 2. Update main runner to use Gradio by default
    new_main_content = '''#!/usr/bin/env python3
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
'''
    
    main_py = ROOT / "main.py"
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(new_main_content)
    print(f"✅ Updated {main_py} to support both interfaces")
    
    # 3. Create quick start scripts
    quick_start_content = '''#!/bin/bash
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
'''
    
    quick_start_sh = ROOT / "quick_start_gradio.sh"
    with open(quick_start_sh, "w", encoding="utf-8") as f:
        f.write(quick_start_content)
    quick_start_sh.chmod(0o755)
    print(f"✅ Created {quick_start_sh}")
    
    # 4. Update README
    readme_update = '''

## 🎉 New: Gradio Interface Available!

This project now supports both Streamlit and Gradio interfaces:

### 🌟 Gradio (Recommended)
- **Quick Start**: `./quick_start_gradio.sh` or `python gradio_simple.py`
- **Full Version**: `python main.py` (default)
- **URL**: http://localhost:7860

### 📊 Streamlit (Legacy)
- **Start**: `python main.py --interface streamlit`
- **URL**: http://localhost:8501

### ⚡ Quick Commands
```bash
# Gradio (simple)
python gradio_simple.py

# Gradio (full)
python main.py

# Streamlit
python main.py --interface streamlit

# Get help
python main.py --help
```

See `GRADIO_MIGRATION.md` for detailed migration notes.
'''
    
    readme_file = ROOT / "readme.md"
    if readme_file.exists():
        readme_content = readme_file.read_text(encoding="utf-8")
        if "Gradio Interface" not in readme_content:
            with open(readme_file, "a", encoding="utf-8") as f:
                f.write(readme_update)
            print(f"✅ Updated {readme_file} with Gradio information")
    
    # 5. Create completion summary
    summary = f"""
🎉 Migration Complete!

✅ Files created/updated:
   • gradio_simple.py - Simple Gradio interface (working)
   • src/main_engine/gradio_app.py - Full Gradio interface  
   • GRADIO_MIGRATION.md - Migration documentation
   • main.py - Updated main entry point
   • requirements.txt - Added Gradio dependency
   
✅ Scripts created:
   • quick_start_gradio.sh - Quick start for Gradio
   • start_gradio_linux.sh - Linux startup script
   • start_gradio_window.cmd - Windows startup script
   
✅ Backup created:
   • app_streamlit_backup.py - Original Streamlit app backup

🚀 Quick Start Options:
   1. Simple: python gradio_simple.py
   2. Full:   python main.py
   3. Legacy: python main.py --interface streamlit

🌐 Access: http://localhost:7860 (Gradio) or http://localhost:8501 (Streamlit)

📖 See GRADIO_MIGRATION.md for detailed information.
"""
    
    print(summary)
    
    # Save summary to file
    summary_file = ROOT / "MIGRATION_COMPLETE.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"# Migration Complete\n\n{summary}")
    
    print(f"✅ Migration summary saved to {summary_file}")

if __name__ == "__main__":
    main()
