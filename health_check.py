#!/usr/bin/env python3
"""
System health check and validation script for Hoàn Cầu AI CV Processor
"""

import os
import sys
from pathlib import Path
import logging
import traceback
from typing import Dict, Any, List

# Add root directory to path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_environment() -> Dict[str, Any]:
    """Check Python environment and required packages."""
    results = {
        "python_version": sys.version,
        "python_path": sys.executable,
        "packages": {},
        "errors": []
    }
    
    required_packages = [
        "streamlit", "pandas", "requests", "dotenv",
        "pathlib", "typing", "datetime", "json", "re"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            results["packages"][package] = "✅ OK"
        except ImportError as e:
            results["packages"][package] = f"❌ Missing: {e}"
            results["errors"].append(f"Missing package: {package}")
    
    return results


def check_configuration_files() -> Dict[str, Any]:
    """Check configuration files and directories."""
    results = {
        "files": {},
        "directories": {},
        "errors": []
    }
    
    # Check important files
    important_files = [
        ".env.example",
        "requirements.txt",
        "readme.md",
        "main_engine/app.py",
        "modules/config.py",
        "modules/qa_chatbot.py",
        "modules/cv_processor.py",
        "modules/dynamic_llm_client.py",
        "modules/email_fetcher.py",
        "static/style.css",
        "static/logo.png"
    ]
    
    for file_path in important_files:
        full_path = ROOT / file_path
        if full_path.exists():
            results["files"][file_path] = f"✅ OK ({full_path.stat().st_size} bytes)"
        else:
            results["files"][file_path] = "❌ Missing"
            results["errors"].append(f"Missing file: {file_path}")
    
    # Check directories
    important_dirs = [
        "attachments",
        "main_engine",
        "modules",
        "static",
        "main_engine/tabs"
    ]
    
    for dir_path in important_dirs:
        full_path = ROOT / dir_path
        if full_path.exists() and full_path.is_dir():
            file_count = len(list(full_path.iterdir()))
            results["directories"][dir_path] = f"✅ OK ({file_count} items)"
        else:
            results["directories"][dir_path] = "❌ Missing"
            results["errors"].append(f"Missing directory: {dir_path}")
    
    return results


def check_modules_import() -> Dict[str, Any]:
    """Check if all custom modules can be imported."""
    results = {
        "modules": {},
        "errors": []
    }
    
    modules_to_test = [
        "modules.config",
        "modules.qa_chatbot", 
        "modules.cv_processor",
        "modules.dynamic_llm_client",
        "modules.email_fetcher",
        "modules.auto_fetcher"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            results["modules"][module_name] = "✅ OK"
        except Exception as e:
            results["modules"][module_name] = f"❌ Error: {str(e)}"
            results["errors"].append(f"Module import error {module_name}: {e}")
    
    return results


def check_environment_variables() -> Dict[str, Any]:
    """Check environment variables configuration."""
    results = {
        "variables": {},
        "errors": [],
        "warnings": []
    }
    
    # Check .env file
    env_file = ROOT / ".env"
    if env_file.exists():
        results["env_file"] = "✅ Found"
        try:
            from dotenv import load_dotenv
            load_dotenv()
            results["env_loaded"] = "✅ Loaded"
        except Exception as e:
            results["env_loaded"] = f"❌ Error loading: {e}"
            results["errors"].append(f"Error loading .env: {e}")
    else:
        results["env_file"] = "⚠️ Not found (using defaults)"
        results["warnings"].append("No .env file found - using default configuration")
    
    # Check important environment variables
    important_vars = [
        "LLM_PROVIDER", "LLM_MODEL", "GOOGLE_API_KEY", "OPENROUTER_API_KEY",
        "EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASS"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Don't show full API keys or passwords for security
            if "API_KEY" in var or "PASS" in var:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            results["variables"][var] = f"✅ Set ({display_value})"
        else:
            results["variables"][var] = "⚠️ Not set"
            results["warnings"].append(f"Environment variable not set: {var}")
    
    return results


def check_streamlit_compatibility() -> Dict[str, Any]:
    """Check Streamlit specific compatibility."""
    results = {
        "streamlit": {},
        "errors": []
    }
    
    try:
        import streamlit as st
        results["streamlit"]["version"] = f"✅ {st.__version__}"
        
        # Check if we can create basic Streamlit components
        try:
            # This should work in a non-Streamlit context
            results["streamlit"]["basic_functions"] = "✅ Available"
        except Exception as e:
            results["streamlit"]["basic_functions"] = f"❌ Error: {e}"
            results["errors"].append(f"Streamlit functions error: {e}")
            
    except ImportError as e:
        results["streamlit"]["version"] = f"❌ Not installed: {e}"
        results["errors"].append(f"Streamlit not available: {e}")
    
    return results


def run_comprehensive_health_check() -> Dict[str, Any]:
    """Run comprehensive health check."""
    logger.info("🔍 Starting comprehensive health check...")
    
    health_report = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "python_env": {},
        "config_files": {},
        "modules": {},
        "environment": {},
        "streamlit": {},
        "overall_status": "unknown",
        "total_errors": 0,
        "total_warnings": 0
    }
    
    # Run all checks
    checks = [
        ("python_env", check_python_environment),
        ("config_files", check_configuration_files),
        ("modules", check_modules_import),
        ("environment", check_environment_variables),
        ("streamlit", check_streamlit_compatibility)
    ]
    
    total_errors = 0
    total_warnings = 0
    
    for check_name, check_function in checks:
        try:
            logger.info(f"Running {check_name} check...")
            result = check_function()
            health_report[check_name] = result
            
            # Count errors and warnings
            total_errors += len(result.get("errors", []))
            total_warnings += len(result.get("warnings", []))
            
        except Exception as e:
            logger.error(f"Check {check_name} failed: {e}")
            health_report[check_name] = {"error": str(e), "traceback": traceback.format_exc()}
            total_errors += 1
    
    # Determine overall status
    if total_errors == 0:
        if total_warnings == 0:
            health_report["overall_status"] = "✅ HEALTHY"
        else:
            health_report["overall_status"] = f"⚠️ HEALTHY WITH WARNINGS ({total_warnings})"
    else:
        health_report["overall_status"] = f"❌ ISSUES FOUND ({total_errors} errors, {total_warnings} warnings)"
    
    health_report["total_errors"] = total_errors
    health_report["total_warnings"] = total_warnings
    
    return health_report


def print_health_report(report: Dict[str, Any]):
    """Print formatted health report."""
    print("\n" + "=" * 80)
    print("🏥 HOÀN CẦU AI CV PROCESSOR - HEALTH CHECK REPORT")
    print("=" * 80)
    
    print(f"\n📊 OVERALL STATUS: {report['overall_status']}")
    print(f"📈 Total Errors: {report['total_errors']}")
    print(f"⚠️ Total Warnings: {report['total_warnings']}")
    
    # Print detailed results
    for section_name, section_data in report.items():
        if section_name in ["timestamp", "overall_status", "total_errors", "total_warnings"]:
            continue
            
        print(f"\n📋 {section_name.upper().replace('_', ' ')}:")
        print("-" * 40)
        
        if isinstance(section_data, dict):
            # Print main items
            for key, value in section_data.items():
                if key not in ["errors", "warnings"]:
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    else:
                        print(f"  {key}: {value}")
            
            # Print errors and warnings
            if "errors" in section_data and section_data["errors"]:
                print(f"  ❌ ERRORS:")
                for error in section_data["errors"]:
                    print(f"    - {error}")
            
            if "warnings" in section_data and section_data["warnings"]:
                print(f"  ⚠️ WARNINGS:")
                for warning in section_data["warnings"]:
                    print(f"    - {warning}")
    
    print("\n" + "=" * 80)
    print("Health check completed. Review any errors or warnings above.")
    print("=" * 80)


def main():
    """Main function."""
    try:
        logger.info("Starting Hoàn Cầu AI CV Processor Health Check")
        
        # Run health check
        report = run_comprehensive_health_check()
        
        # Print report
        print_health_report(report)
        
        # Save report to file
        import json
        report_file = ROOT / "health_check_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Health check report saved to: {report_file}")
        
        # Exit with appropriate code
        if report["total_errors"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
