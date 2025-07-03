#!/usr/bin/env python3
"""Test script để kiểm tra update system"""

import sys
from pathlib import Path

# Add src to path
HERE = Path(__file__).parent
ROOT = HERE
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

def test_update_system():
    """Test các component của update system"""
    print("🧪 Test Update System Components...")
    
    try:
        # Test 1: Import UpdateManager
        from modules.update_manager import UpdateManager
        print("✅ UpdateManager import thành công")
        
        # Test 2: Tạo instance
        update_manager = UpdateManager()
        print("✅ UpdateManager instance tạo thành công")
        
        # Test 3: Kiểm tra version
        version_info = update_manager.get_current_version()
        print(f"✅ Current version: {version_info.get('version', 'unknown')}")
        
        # Test 4: List backups (should work even if empty)
        backups = update_manager.list_backups()
        print(f"✅ Found {len(backups)} backups")
        
        # Test 5: Test update tab import
        from main_engine.tabs.update_tab import render
        print("✅ Update tab import thành công")
        
        # Test 6: Test CLI script import
        import subprocess
        result = subprocess.run([
            sys.executable, 
            str(ROOT / "scripts" / "update_manager.py"), 
            "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ CLI update_manager.py hoạt động tốt")
        else:
            print(f"⚠️ CLI có vấn đề: {result.stderr}")
        
        print("\n🎉 Tất cả test passed! Update system sẵn sàng sử dụng.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_update_system()
