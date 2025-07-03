#!/usr/bin/env python3
"""
Simple Health Check for HoanCau AI
"""

import sys
import os
import importlib
from pathlib import Path

def print_status(message: str, success: bool = True):
    """Print status with color"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def main():
    print("🏥 HoanCau AI Quick Health Check")
    print("=" * 40)
    
    success_count = 0
    total_checks = 0
    
    # Check Python version
    total_checks += 1
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}")
        success_count += 1
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Need 3.8+", False)
    
    # Check key packages
    packages = ["streamlit", "pandas", "tqdm"]
    for pkg in packages:
        total_checks += 1
        try:
            importlib.import_module(pkg)
            print_status(f"{pkg} installed")
            success_count += 1
        except ImportError:
            print_status(f"{pkg} missing", False)
    
    # Check key files
    files = ["src/main_engine/app.py", "requirements.txt"]
    for file in files:
        total_checks += 1
        if Path(file).exists():
            print_status(f"{file} found")
            success_count += 1
        else:
            print_status(f"{file} missing", False)
    
    print("\n" + "=" * 40)
    print(f"Result: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 System ready!")
        return 0
    else:
        print("⚠️ Some issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())
