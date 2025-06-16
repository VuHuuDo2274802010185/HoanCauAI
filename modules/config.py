# modules/config.py

import os  # thư viện xử lý biến môi trường và hệ thống file
from pathlib import Path  # thư viện để thao tác đường dẫn hệ thống
from typing import Dict, Any, List  # khai báo kiểu cho biến và hàm
from dotenv import load_dotenv  # thư viện để load file .env
import logging  # thư viện quản lý log

# --- Tải biến môi trường từ file .env ở thư mục gốc ---
load_dotenv()  # đọc và gán các biến trong .env vào môi trường hệ thống

# --- Cấu hình logging cơ bản ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def _get_env(varname: str, default: str = "") -> str:
    """Đọc biến môi trường, bỏ comment và dấu nháy, trả về chuỗi."""
    raw = os.getenv(varname, default)
    cleaned = raw.split('#', 1)[0].strip()
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    return cleaned

# --- Nhà cung cấp (provider) và model mặc định ---
LLM_PROVIDER = _get_env("LLM_PROVIDER", "google").lower()
LLM_MODEL = _get_env("LLM_MODEL", "gemini-1.5-flash-latest")

# --- Khóa API cho Google và OpenRouter (không bắt buộc) ---
GOOGLE_API_KEY = _get_env("GOOGLE_API_KEY")
OPENROUTER_API_KEY = _get_env("OPENROUTER_API_KEY")

# --- Cấu hình email (không bắt buộc) ---
EMAIL_HOST = _get_env("EMAIL_HOST", "imap.gmail.com")
# EMAIL_PORT: làm sạch comment và chuyển sang int, mặc định 993
_raw_port = os.getenv("EMAIL_PORT", "").split('#', 1)[0].strip()
if _raw_port:
    try:
        EMAIL_PORT = int(_raw_port)
    except ValueError:
        raise RuntimeError(f"⚠️ EMAIL_PORT không hợp lệ: {_raw_port}")
else:
    EMAIL_PORT = 993

EMAIL_USER = _get_env("EMAIL_USER")
EMAIL_PASS = _get_env("EMAIL_PASS")

# --- Thư mục lưu file đính kèm và file xuất kết quả ---
def _clean_path(varname: str, default: str) -> Path:
    """
    Lấy biến môi trường, loại bỏ comment và dấu nháy, trả về Path.
    """
    raw = os.getenv(varname, default)
    cleaned = raw.split('#', 1)[0].strip()
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    return Path(cleaned)

ATTACHMENT_DIR = _clean_path("ATTACHMENT_DIR", "attachments")
OUTPUT_CSV = _clean_path("OUTPUT_CSV", "cv_summary.csv")
# tạo thư mục nếu chưa tồn tại
ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)

# --- Danh sách models dự phòng ---
GOOGLE_FALLBACK_MODELS: List[str] = [
    "gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-1.5-pro-latest",
    "gemini-1.5-pro", "gemini-pro", "gemini-pro-vision",
]
OPENROUTER_FALLBACK_MODELS: List[str] = [
    "anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku",
    "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-3.5-turbo",]
@@ -89,47 +83,58 @@ from .model_fetcher import ModelFetcher

def get_available_models(provider: str, api_key: str) -> List[str]:
    """Lấy danh sách models từ API hoặc trả về rỗng nếu lỗi."""
    try:
        if provider == "google":
            return ModelFetcher.get_google_models(api_key)
        if provider == "openrouter":
            return ModelFetcher.get_simple_openrouter_model_ids(api_key)
    except Exception as e:
        logger.warning(f"Không thể lấy models từ API {provider}: {e}")
    return []


def get_models_for_provider(provider: str, api_key: str) -> List[str]:
    """Lấy models từ API hoặc dùng fallback"""
    available = get_available_models(provider, api_key)
    if available:
        logger.info(f"Đã lấy {len(available)} models từ {provider.upper()} API")
        return available
    fallback = GOOGLE_FALLBACK_MODELS if provider == "google" else OPENROUTER_FALLBACK_MODELS
    logger.warning(f"Sử dụng fallback models cho {provider.upper()}")
    return fallback


def validate_and_setup_llm() -> Dict[str, Any]:
    """Thiết lập cấu hình LLM từ env, dùng fallback khi thiếu API key."""
    config = {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "api_key": None,
        "client": None,
        "available_models": [],
    }

    provider = LLM_PROVIDER
    api_key = GOOGLE_API_KEY if provider == "google" else OPENROUTER_API_KEY

    available = get_models_for_provider(provider, api_key) if api_key else []
    if not available:
        available = GOOGLE_FALLBACK_MODELS if provider == "google" else OPENROUTER_FALLBACK_MODELS

    config.update({"api_key": api_key, "available_models": available})

    if config["model"] not in available:
        logger.warning(f"Model {config['model']} không tồn tại, chuyển sang {available[0]}")
        config["model"] = available[0]

    if provider == "google" and api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            config["client"] = genai
        except Exception as e:
            logger.warning(f"Không thể cấu hình Google client: {e}")

    return config

LLM_CONFIG = validate_and_setup_llm()