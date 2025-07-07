#!/usr/bin/env python3
"""
Enhanced Health Check Script for HoanCau AI
Performs comprehensive system validation and dependency checking
"""

import sys
import os
import logging
import importlib
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    colors = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED
    }
    color = colors.get(status, Colors.NC)
    print(f"{color}[{status}]{Colors.NC} {message}")

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    print_status("Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} ✓", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+", "ERROR")
        return False

def check_required_packages() -> Tuple[bool, List[str]]:
    """Check if all required packages are installed"""
    print_status("Checking required packages...")
    
    required_packages = [
        "streamlit",
        "pandas",
        "google.generativeai",
        "pdfminer.six",
        "python_docx",
        "openpyxl",
        "requests",
        "tqdm",
        "python_dotenv",
        "fastapi",
        "uvicorn"
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            # Handle special package names
            if package == "pdfminer.six":
                importlib.import_module("pdfminer.high_level")
            elif package == "python_docx":
                importlib.import_module("docx")
            elif package == "python_dotenv":
                importlib.import_module("dotenv")
            else:
                importlib.import_module(package)
            
            installed_packages.append(package)
            print_status(f"  {package} ✓", "SUCCESS")
        except ImportError:
            missing_packages.append(package)
            print_status(f"  {package} ✗", "ERROR")
    
    if missing_packages:
        print_status(f"Missing packages: {', '.join(missing_packages)}", "ERROR")
        return False, missing_packages
    else:
        print_status("All required packages installed ✓", "SUCCESS")
        return True, []

def check_project_structure() -> bool:
    """Check if project structure is correct"""
    print_status("Checking project structure...")
    
    required_files = [
        "src/main_engine/app.py",
        "src/modules/__init__.py",
        "src/modules/config.py",
        "src/modules/cv_processor.py",
        "src/modules/llm_client.py",
        "requirements.txt",
        "start_linux.sh"
    ]
    
    required_dirs = [
        "src/main_engine",
        "src/modules",
        "attachments",
        "log",
        "csv",
        "excel"
    ]
    
    missing_items = []
    
    # Check files
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_items.append(f"File: {file_path}")
            print_status(f"  {file_path} ✗", "ERROR")
        else:
            print_status(f"  {file_path} ✓", "SUCCESS")
    
    # Check directories
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_items.append(f"Directory: {dir_path}")
            print_status(f"  {dir_path}/ ✗", "ERROR")
        else:
            print_status(f"  {dir_path}/ ✓", "SUCCESS")
    
    if missing_items:
        print_status(f"Missing items: {len(missing_items)}", "ERROR")
        return False
    else:
        print_status("Project structure is correct ✓", "SUCCESS")
        return True

def check_environment_variables() -> bool:
    """Check environment variables and config"""
    print_status("Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print_status(".env file found ✓", "SUCCESS")
    else:
        print_status(".env file not found (optional)", "WARNING")
    
    # Check important environment variables
    important_vars = ["GOOGLE_API_KEY", "EMAIL_USER", "EMAIL_PASS"]
    missing_vars = []
    
    for var in important_vars:
        if os.getenv(var):
            print_status(f"  {var} is set ✓", "SUCCESS")
        else:
            missing_vars.append(var)
            print_status(f"  {var} not set", "WARNING")
    
    if missing_vars:
        print_status("Some environment variables are missing (can be set in UI)", "WARNING")
    
    return True

def check_streamlit_functionality() -> bool:
    """Test basic Streamlit functionality"""
    print_status("Testing Streamlit functionality...")
    
    try:
        import streamlit as st
        print_status(f"Streamlit version: {st.__version__} ✓", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Streamlit test failed: {str(e)}", "ERROR")
        return False

def check_llm_connectivity() -> bool:
    """Test LLM connectivity (if API key is available)"""
    print_status("Testing LLM connectivity...")
    
    try:
        sys.path.insert(0, "src")
        from modules.llm_client import LLMClient
        
        # Try to initialize LLM client
        client = LLMClient()
        print_status("LLM client initialized ✓", "SUCCESS")
        
        # Test with a simple prompt if API key is available
        if os.getenv("GOOGLE_API_KEY"):
            try:
                response = client.generate_content(["Test prompt: respond with 'OK'"])
                if response and "OK" in response:
                    print_status("LLM connectivity test passed ✓", "SUCCESS")
                else:
                    print_status("LLM responded but unexpected result", "WARNING")
            except Exception as e:
                print_status(f"LLM connectivity test failed: {str(e)}", "WARNING")
        else:
            print_status("No API key found, skipping connectivity test", "WARNING")
        
        return True
    except Exception as e:
        print_status(f"LLM client test failed: {str(e)}", "ERROR")
        return False

def check_file_permissions() -> bool:
    """Check file and directory permissions"""
    print_status("Checking file permissions...")
    
    # Test write permissions in key directories
    test_dirs = ["attachments", "log", "csv", "excel"]
    
    for dir_name in test_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print_status(f"Created directory: {dir_name} ✓", "SUCCESS")
            except Exception as e:
                print_status(f"Cannot create directory {dir_name}: {str(e)}", "ERROR")
                return False
        
        # Test write permission
        test_file = dir_path / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print_status(f"Write permission OK: {dir_name} ✓", "SUCCESS")
        except Exception as e:
            print_status(f"No write permission in {dir_name}: {str(e)}", "ERROR")
            return False
    
    return True

def performance_benchmark() -> Dict[str, float]:
    """Run basic performance benchmarks"""
    print_status("Running performance benchmarks...")
    
    results = {}
    
    # Test import time
    start_time = time.time()
    try:
        sys.path.insert(0, "src")
        import modules.cv_processor
        import modules.llm_client
        import streamlit
        results["import_time"] = time.time() - start_time
        print_status(f"Module import time: {results['import_time']:.2f}s ✓", "SUCCESS")
    except Exception as e:
        print_status(f"Import benchmark failed: {str(e)}", "ERROR")
        results["import_time"] = -1
    
    # Test file I/O
    start_time = time.time()
    try:
        test_data = "x" * 1000000  # 1MB of data
        test_file = Path("test_io.tmp")
        test_file.write_text(test_data)
        _ = test_file.read_text()
        test_file.unlink()
        results["io_time"] = time.time() - start_time
        print_status(f"File I/O test (1MB): {results['io_time']:.2f}s ✓", "SUCCESS")
    except Exception as e:
        print_status(f"I/O benchmark failed: {str(e)}", "ERROR")
        results["io_time"] = -1
    
    return results

def generate_report(checks: Dict[str, bool], performance: Dict[str, float]):
    """Generate health check report"""
    print("\n" + "="*60)
    print(f"{Colors.BOLD}HEALTH CHECK REPORT{Colors.NC}")
    print("="*60)
    
    # Summary
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    if passed == total:
        print_status(f"Overall Status: HEALTHY ({passed}/{total})", "SUCCESS")
    elif passed >= total * 0.8:
        print_status(f"Overall Status: WARNING ({passed}/{total})", "WARNING")
    else:
        print_status(f"Overall Status: CRITICAL ({passed}/{total})", "ERROR")
    
    print(f"\n{Colors.BOLD}Component Status:{Colors.NC}")
    for check, status in checks.items():
        icon = "✓" if status else "✗"
        color = Colors.GREEN if status else Colors.RED
        print(f"  {color}{icon}{Colors.NC} {check}")
    
    print(f"\n{Colors.BOLD}Performance Metrics:{Colors.NC}")
    for metric, value in performance.items():
        if value >= 0:
            print(f"  • {metric}: {value:.2f}s")
        else:
            print(f"  • {metric}: Failed")
    
    print("\n" + "="*60)

def install_missing_packages(missing_packages: List[str]) -> bool:
    """Install missing packages"""
    if not missing_packages:
        return True
    
    print_status(f"Installing {len(missing_packages)} missing packages...", "INFO")
    
    try:
        # Convert package names for pip
        pip_packages = []
        for pkg in missing_packages:
            if pkg == "pdfminer.six":
                pip_packages.append("pdfminer.six")
            elif pkg == "python_docx":
                pip_packages.append("python-docx")
            elif pkg == "python_dotenv":
                pip_packages.append("python-dotenv")
            elif pkg == "google.generativeai":
                pip_packages.append("google-generativeai")
            else:
                pip_packages.append(pkg)
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet"
        ] + pip_packages)
        
        print_status("Packages installed successfully ✓", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to install packages: {str(e)}", "ERROR")
        return False

def main():
    """Main health check function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🏥 HoanCau AI Health Check")
    print("=" * 40)
    print(f"{Colors.NC}")
    
    checks = {}
    
    # Run all checks
    checks["Python Version"] = check_python_version()
    
    packages_ok, missing = check_required_packages()
    if not packages_ok:
        if input("\nInstall missing packages? (y/N): ").lower() == 'y':
            if install_missing_packages(missing):
                checks["Required Packages"] = True
            else:
                checks["Required Packages"] = False
        else:
            checks["Required Packages"] = False
    else:
        checks["Required Packages"] = True
    
    checks["Project Structure"] = check_project_structure()
    checks["Environment Config"] = check_environment_variables()
    checks["Streamlit"] = check_streamlit_functionality()
    checks["LLM Client"] = check_llm_connectivity()
    checks["File Permissions"] = check_file_permissions()
    
    # Run performance benchmarks
    performance = performance_benchmark()
    
    # Generate report
    generate_report(checks, performance)
    
    # Exit with appropriate code
    if all(checks.values()):
        print_status("System is ready! 🚀", "SUCCESS")
        sys.exit(0)
    elif sum(checks.values()) >= len(checks) * 0.8:
        print_status("System has minor issues but should work", "WARNING")
        sys.exit(1)
    else:
        print_status("System has critical issues", "ERROR")
        sys.exit(2)

if __name__ == "__main__":
    main()
