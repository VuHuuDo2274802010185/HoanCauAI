#!/usr/bin/env python3
# config_info.py - Script hiển thị thông tin cấu hình LLM hiện tại

from modules.config import LLM_CONFIG
from modules.model_fetcher import ModelFetcher

def show_config_info():
    """Hiển thị thông tin cấu hình LLM hiện tại"""
    print("=" * 70)
    print("🤖 THÔNG TIN CẤU HÌNH LLM")
    print("=" * 70)
    
    print(f"📡 Provider hiện tại: {LLM_CONFIG['provider'].upper()}")
    print(f"🎯 Model hiện tại: {LLM_CONFIG['model']}")
    print(f"🔑 API Key: {'✅ Đã cấu hình' if LLM_CONFIG['api_key'] else '❌ Chưa cấu hình'}")
    
    available_models = LLM_CONFIG.get('available_models', [])
    if available_models:
        print(f"📊 Tổng số models khả dụng: {len(available_models)}")
    
    print("\n" + "=" * 70)
    print("📋 DANH SÁCH MODELS KHẢ DỤNG (TỪ API)")
    print("=" * 70)
    
    if LLM_CONFIG['provider'] == 'google' and LLM_CONFIG['api_key']:
        print("\n🔵 GOOGLE GEMINI MODELS (Từ API):")
        try:
            models = ModelFetcher.get_google_models(LLM_CONFIG['api_key'])
            for i, model in enumerate(models, 1):
                current = " ⭐ (đang dùng)" if LLM_CONFIG['model'] == model else ""
                print(f"  {i:2d}. {model}{current}")
        except Exception as e:
            print(f"  ❌ Lỗi lấy models từ API: {e}")
            print("  ℹ️  Sử dụng fallback models...")
    
    elif LLM_CONFIG['provider'] == 'openrouter' and LLM_CONFIG['api_key']:
        print("\n🟠 OPENROUTER MODELS (Từ API):")
        try:
            models_info = ModelFetcher.get_openrouter_models(LLM_CONFIG['api_key'])
            for i, model in enumerate(models_info, 1):
                current = " ⭐ (đang dùng)" if LLM_CONFIG['model'] == model['id'] else ""
                context_info = f" ({model.get('context_length', 'N/A')} tokens)" if model.get('context_length') else ""
                print(f"  {i:2d}. {model['id']}{context_info}{current}")
                if model.get('name') and model['name'] != model['id']:
                    print(f"      📝 {model['name']}")
                if i >= 20:  # Giới hạn hiển thị 20 models đầu tiên
                    print(f"      ... và {len(models_info) - 20} models khác")
                    break
        except Exception as e:
            print(f"  ❌ Lỗi lấy models từ API: {e}")
            print("  ℹ️  Sử dụng fallback models...")
    
    else:
        print("\n⚠️  Không thể lấy models từ API - thiếu API key")
        print("Hiển thị fallback models:")
        
        if available_models:
            for i, model in enumerate(available_models, 1):
                current = " ⭐ (đang dùng)" if LLM_CONFIG['model'] == model else ""
                print(f"  {i:2d}. {model}{current}")
    
    print("\n" + "=" * 70)
    print("⚙️  CÁCH THAY ĐỔI CẤU HÌNH")
    print("=" * 70)
    print("1. Chỉnh sửa file .env:")
    print("   LLM_PROVIDER=google|openrouter")
    print("   LLM_MODEL=tên_model")
    print("   GOOGLE_API_KEY=your_key (cho Google)")
    print("   OPENROUTER_API_KEY=your_key (cho OpenRouter)")
    print("\n2. Khởi động lại ứng dụng")
    print("\n3. Models sẽ được tự động lấy từ API")
    print("   - Google: https://aistudio.google.com/app/apikey")
    print("   - OpenRouter: https://openrouter.ai/keys")

def show_all_openrouter_models():
    """Hiển thị tất cả OpenRouter models với thông tin chi tiết"""
    from modules.config import OPENROUTER_API_KEY
    
    if not OPENROUTER_API_KEY:
        print("❌ Cần OPENROUTER_API_KEY để xem danh sách đầy đủ")
        return
    
    print("🔍 ĐANG TẢI TẤT CẢ OPENROUTER MODELS...")
    try:
        models = ModelFetcher.get_openrouter_models(OPENROUTER_API_KEY)
        print(f"\n📊 Tổng cộng: {len(models)} models")
        print("=" * 80)
        
        for i, model in enumerate(models, 1):
            print(f"{i:3d}. {model['id']}")
            if model.get('name'):
                print(f"     📝 {model['name']}")
            if model.get('context_length'):
                print(f"     🔢 Context: {model['context_length']:,} tokens")
            if model.get('pricing'):
                pricing = model['pricing']
                if pricing.get('prompt'):
                    print(f"     💰 Prompt: ${pricing['prompt']} | Completion: ${pricing.get('completion', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    try:
        show_config_info()
        
        # Tùy chọn hiển thị tất cả OpenRouter models
        user_input = input("\n🤔 Bạn có muốn xem tất cả OpenRouter models? (y/N): ")
        if user_input.lower() in ['y', 'yes']:
            show_all_openrouter_models()
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("💡 Hãy đảm bảo file .env đã được cấu hình đúng")
