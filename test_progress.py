#!/usr/bin/env python3
"""Test script để kiểm tra thanh tiến trình"""

import sys
from pathlib import Path
import time

# Add src to path
HERE = Path(__file__).parent
SRC_DIR = HERE / "src"
sys.path.insert(0, str(SRC_DIR))

def dummy_progress_callback(current, total, message):
    """Callback giả lập để test"""
    percent = (current / total * 100) if total > 0 else 0
    print(f"[{percent:5.1f}%] {current:3d}/{total:3d} - {message}")

def test_email_fetcher():
    """Test EmailFetcher với progress callback"""
    print("🧪 Test EmailFetcher với progress callback...")
    try:
        from modules.email_fetcher import EmailFetcher
        # Tạo fetcher nhưng không connect thật
        fetcher = EmailFetcher()
        print("✅ EmailFetcher import thành công")
        
        # Test signature của fetch_cv_attachments
        import inspect
        sig = inspect.signature(fetcher.fetch_cv_attachments)
        params = list(sig.parameters.keys())
        print(f"✅ Tham số của fetch_cv_attachments: {params}")
        
        if 'progress_callback' in params:
            print("✅ progress_callback đã được thêm thành công")
        else:
            print("❌ progress_callback chưa được thêm")
            
    except Exception as e:
        print(f"❌ Lỗi test EmailFetcher: {e}")

def test_cv_processor():
    """Test CVProcessor với progress callback"""
    print("\n🧪 Test CVProcessor với progress callback...")
    try:
        from modules.cv_processor import CVProcessor
        # Tạo processor nhưng không dùng LLM thật
        processor = CVProcessor()
        print("✅ CVProcessor import thành công")
        
        # Test signature của process
        import inspect
        sig = inspect.signature(processor.process)
        params = list(sig.parameters.keys())
        print(f"✅ Tham số của process: {params}")
        
        if 'progress_callback' in params:
            print("✅ progress_callback đã được thêm thành công")
        else:
            print("❌ progress_callback chưa được thêm")
            
    except Exception as e:
        print(f"❌ Lỗi test CVProcessor: {e}")

if __name__ == "__main__":
    print("🚀 Bắt đầu test progress callback...")
    test_email_fetcher()
    test_cv_processor()
    print("\n✅ Hoàn thành test!")
