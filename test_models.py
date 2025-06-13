#!/usr/bin/env python3
# test_models.py - Script test lấy models từ API

import os
from dotenv import load_dotenv
load_dotenv()

def test_google_models():
    """Test lấy Google models"""
    print("🔵 Testing Google Gemini API...")
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ Thiếu GOOGLE_API_KEY trong .env")
        return
    
    try:
        from modules.model_fetcher import ModelFetcher
        models = ModelFetcher.get_google_models(api_key)
        print(f"✅ Lấy được {len(models)} Google models:")
        for i, model in enumerate(models, 1):
            print(f"  {i:2d}. {model}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_openrouter_models():
    """Test lấy OpenRouter models"""
    print("\n🟠 Testing OpenRouter API...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ Thiếu OPENROUTER_API_KEY trong .env")
        return
    
    try:
        from modules.model_fetcher import ModelFetcher
        models = ModelFetcher.get_openrouter_models(api_key)
        print(f"✅ Lấy được {len(models)} OpenRouter models:")
        for i, model in enumerate(models[:10], 1):  # Chỉ hiển thị 10 đầu tiên
            print(f"  {i:2d}. {model['id']} - {model.get('name', 'N/A')}")
        if len(models) > 10:
            print(f"      ... và {len(models) - 10} models khác")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    print("🧪 TEST VIỆC LẤY MODELS TỪ API")
    print("=" * 50)
    
    test_google_models()
    test_openrouter_models()
    
    print("\n" + "=" * 50)
    print("💡 Để xem đầy đủ, chạy: python config_info.py")
