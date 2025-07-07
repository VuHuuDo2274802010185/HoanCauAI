#!/usr/bin/env python3
"""
Debug script to test module imports
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 Debug Information:")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Script location: {__file__}")
    
    # Add paths
    HERE = Path(__file__).parent
    ROOT = HERE
    SRC_DIR = ROOT / "src"
    
    print(f"ROOT: {ROOT}")
    print(f"SRC_DIR: {SRC_DIR}")
    print(f"SRC_DIR exists: {SRC_DIR.exists()}")
    print(f"modules dir exists: {(SRC_DIR / 'modules').exists()}")
    
    # Add to Python path
    for path in (ROOT, SRC_DIR):
        path_str = str(path.absolute())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    
    print(f"Python path (first 5): {sys.path[:5]}")
    
    # Test imports
    try:
        print("\n📦 Testing imports...")
        
        # Test basic import
        import modules
        print(f"✅ modules package imported from: {modules.__file__}")
        
        # Test config import
        from modules.config import OUTPUT_CSV
        print(f"✅ config imported, OUTPUT_CSV: {OUTPUT_CSV}")
        
        # Test other imports
        from modules.dynamic_llm_client import DynamicLLMClient
        print("✅ DynamicLLMClient imported")
        
        from modules.cv_processor import CVProcessor
        print("✅ CVProcessor imported")
        
        from modules.email_fetcher import EmailFetcher
        print("✅ EmailFetcher imported")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
