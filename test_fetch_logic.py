#!/usr/bin/env python3
"""Test fetch_process_tab trực tiếp"""

import sys
from pathlib import Path

# Add src to path
HERE = Path(__file__).parent
SRC_DIR = HERE / "src"
sys.path.insert(0, str(SRC_DIR))

def test_fetch_process():
    try:
        from modules.cv_processor import CVProcessor
        from modules.dynamic_llm_client import DynamicLLMClient
        import inspect
        
        print("✅ Import thành công")
        
        # Test signature
        sig = inspect.signature(CVProcessor.process)
        params = list(sig.parameters.keys())
        print(f"✅ Tham số của CVProcessor.process: {params}")
        
        if 'progress_callback' in params:
            print("✅ progress_callback có trong CVProcessor.process")
            
            # Test tạo processor như trong fetch_process_tab
            processor = CVProcessor(
                fetcher=None,  # Không dùng fetcher
                llm_client=DynamicLLMClient(provider="google", model="gemini-2.5-flash-lite", api_key="fake_key"),
            )
            print("✅ CVProcessor tạo thành công")
            
            # Test callback
            def progress_callback(current, total, message):
                print(f"Progress: {current}/{total} - {message}")
            
            # Gọi với progress_callback như trong fetch_process_tab
            df = processor.process(
                unseen_only=False,
                since=None,
                before=None,
                from_time=None,
                to_time=None,
                progress_callback=progress_callback,
            )
            print(f"✅ process() với progress_callback thành công! DataFrame shape: {df.shape}")
            
        else:
            print("❌ progress_callback không có trong CVProcessor.process")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Test fetch_process_tab logic...")
    test_fetch_process()
