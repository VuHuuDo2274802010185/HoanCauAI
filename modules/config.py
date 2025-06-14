# modules/config.py

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def _check_required_env(varname: str) -> str:
    """Raise if a required env var is missing."""
    value = os.getenv(varname)
    if not value:
        raise RuntimeError(f"⚠️ Thiếu biến môi trường: {varname}")
    return value


# --- PROVIDER & MODEL ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")

# --- API KEYS ---
# Google key is only required if you actually choose Google
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- EMAIL CONFIG (bắt buộc) ---
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))
EMAIL_USER = _check_required_env("EMAIL_USER")
EMAIL_PASS = _check_required_env("EMAIL_PASS")

# --- ATTACHMENTS & OUTPUT ---
ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR", "attachments")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "cv_summary.csv")
Path(ATTACHMENT_DIR).mkdir(parents=True, exist_ok=True)

# --- MODEL FETCHING & FALLBACK ---
from .model_fetcher import ModelFetcher

def get_available_models(provider: str, api_key: str) -> list:
    try:
        if provider == "google" and api_key:
            return ModelFetcher.get_google_models(api_key)
        elif provider == "openrouter" and api_key:
            return ModelFetcher.get_simple_openrouter_model_ids(api_key)
    except Exception as e:
        print(f"⚠️ Không thể lấy models từ API: {e}")
    return []

GOOGLE_FALLBACK_MODELS = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-pro-vision",
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
    "qwen/qwen-2.5-72b-instruct",
]

def get_models_for_provider(provider: str, api_key: str) -> list:
    api_models = get_available_models(provider, api_key)
    if api_models:
        print(f"✅ Đã lấy {len(api_models)} models từ {provider.upper()} API")
        return api_models
    print(f"⚠️ Sử dụng fallback models cho {provider.upper()}")
    return (
        GOOGLE_FALLBACK_MODELS if provider == "google" else OPENROUTER_FALLBACK_MODELS
    )

def validate_and_setup_llm() -> Dict[str, Any]:
    """Kiểm tra & thiết lập LLM, trả về dict chứa client, key, model, v.v."""
    config: Dict[str, Any] = {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "api_key": None,
        "client": None,
        "available_models": [],
    }

    if LLM_PROVIDER == "google":
        _check_required_env("GOOGLE_API_KEY")
        available = get_models_for_provider("google", GOOGLE_API_KEY)
        config["available_models"] = available
        if LLM_MODEL not in available:
            print(f"⚠️ Model {LLM_MODEL} không có trong danh sách, dùng {available[0]}")
            config["model"] = available[0]
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        config.update({"api_key": GOOGLE_API_KEY, "client": genai})

    elif LLM_PROVIDER == "openrouter":
        _check_required_env("OPENROUTER_API_KEY")
        available = get_models_for_provider("openrouter", OPENROUTER_API_KEY)
        config["available_models"] = available
        if LLM_MODEL not in available:
            print(f"⚠️ Model {LLM_MODEL} không có trong danh sách, dùng {available[0]}")
            config["model"] = available[0]
        config.update({"api_key": OPENROUTER_API_KEY})

    else:
        raise RuntimeError(f"Provider không hỗ trợ: {LLM_PROVIDER}")

    return config

# Khởi tạo 1 lần để dùng chung toàn project
LLM_CONFIG = validate_and_setup_llm()
