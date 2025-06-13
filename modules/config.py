# modules/config.py
import os
from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv()

# --- CẤU HÌNH LLM PROVIDER ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google").lower()  # google, openrouter
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")

# --- API KEYS ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- FUNCTION ĐỂ LẤY MODELS TỪ API ---
def get_available_models(provider: str, api_key: str) -> list:
    """Lấy danh sách models khả dụng từ API"""
    try:
        if provider == "google" and api_key:
            from .model_fetcher import ModelFetcher
            return ModelFetcher.get_google_models(api_key)
        elif provider == "openrouter" and api_key:
            from .model_fetcher import ModelFetcher
            return ModelFetcher.get_simple_openrouter_model_ids(api_key)
        else:
            return []
    except Exception as e:
        print(f"⚠️ Không thể lấy models từ API: {e}")
        return []

# --- FALLBACK MODELS (nếu API call thất bại) ---
GOOGLE_FALLBACK_MODELS = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest", 
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-pro-vision"
]

OPENROUTER_FALLBACK_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-3.5-turbo",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "qwen/qwen-2.5-72b-instruct"
]

# --- LẤY MODELS TỪ API HOẶC SỬ DỤNG FALLBACK ---
def get_models_for_provider(provider: str, api_key: str) -> list:
    """Lấy models từ API hoặc fallback"""
    api_models = get_available_models(provider, api_key)
    
    if api_models:
        print(f"✅ Đã lấy {len(api_models)} models từ {provider.upper()} API")
        return api_models
    else:
        print(f"⚠️ Sử dụng fallback models cho {provider.upper()}")
        if provider == "google":
            return GOOGLE_FALLBACK_MODELS
        elif provider == "openrouter":
            return OPENROUTER_FALLBACK_MODELS
        else:
            return []

# --- VALIDATION VÀ SETUP ---
def validate_and_setup_llm() -> Dict[str, Any]:
    """Kiểm tra và thiết lập cấu hình LLM"""
    config = {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "client": None,
        "api_key": None,
        "available_models": []
    }
    
    if LLM_PROVIDER == "google":
        if not GOOGLE_API_KEY:
            raise RuntimeError("Thiếu GOOGLE_API_KEY trong .env cho Google Gemini")
        
        # Lấy danh sách models từ API
        available_models = get_models_for_provider("google", GOOGLE_API_KEY)
        config["available_models"] = available_models
        
        if LLM_MODEL not in available_models:
            print(f"⚠️ Model {LLM_MODEL} không có trong danh sách. Sử dụng model đầu tiên.")
            config["model"] = available_models[0] if available_models else "gemini-1.5-flash-latest"
            
        genai.configure(api_key=GOOGLE_API_KEY)
        config["api_key"] = GOOGLE_API_KEY
        config["client"] = genai
        
    elif LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise RuntimeError("Thiếu OPENROUTER_API_KEY trong .env cho OpenRouter")
        
        # Lấy danh sách models từ API
        available_models = get_models_for_provider("openrouter", OPENROUTER_API_KEY)
        config["available_models"] = available_models
        
        if LLM_MODEL not in available_models:
            print(f"⚠️ Model {LLM_MODEL} không có trong danh sách. Sử dụng model đầu tiên.")
            config["model"] = available_models[0] if available_models else "anthropic/claude-3.5-sonnet"
            
        config["api_key"] = OPENROUTER_API_KEY
        
    else:
        raise RuntimeError(f"Provider không được hỗ trợ: {LLM_PROVIDER}. Chỉ hỗ trợ: google, openrouter")
    
    return config

# Khởi tạo cấu hình LLM
LLM_CONFIG = validate_and_setup_llm()

# Để backward compatibility
GOOGLE_MODELS = LLM_CONFIG.get("available_models", GOOGLE_FALLBACK_MODELS) if LLM_PROVIDER == "google" else GOOGLE_FALLBACK_MODELS
OPENROUTER_MODELS = LLM_CONFIG.get("available_models", OPENROUTER_FALLBACK_MODELS) if LLM_PROVIDER == "openrouter" else OPENROUTER_FALLBACK_MODELS

# Email IMAP
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Thư mục attachments & file xuất CSV
ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR", "attachments")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "cv_summary.csv")
Path(ATTACHMENT_DIR).mkdir(parents=True, exist_ok=True)