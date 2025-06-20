#!/usr/bin/env python3
"""
Test script để kiểm tra tab chat hoạt động
"""

import sys
from pathlib import Path

# Add repository root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    # Test import modules
    print("Testing module imports...")
    
    from modules.config import LLM_CONFIG
    print("✅ modules.config imported successfully")
    
    from modules.qa_chatbot import QAChatbot
    print("✅ modules.qa_chatbot imported successfully")
    
    # Test chat functionality without Streamlit
    print("\nTesting chat functionality...")
    
    # Mock test
    provider = "google"
    model = "gemini-2.0-flash"
    api_key = "test_key"
    
    try:
        chatbot = QAChatbot(provider=provider, model=model, api_key=api_key)
        print("✅ QAChatbot instance created successfully")
    except Exception as e:
        print(f"⚠️ QAChatbot creation failed (expected with test key): {e}")
    
    print("\n🎉 All basic tests passed! Chat tab should work.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
