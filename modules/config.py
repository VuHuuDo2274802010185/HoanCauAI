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


def _check_required_env(varname: str) -> str:
    """
    Kiểm tra biến môi trường bắt buộc và trả về giá trị đã làm sạch (loại bỏ comment và dấu nháy).
    """
    raw = os.getenv(varname, "")  # lấy chuỗi raw từ env
    # bỏ inline comment
    cleaned = raw.split('#', 1)[0].strip()
    # bỏ dấu nháy đơn hoặc kép nếu có
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    if not cleaned:
        raise RuntimeError(f"⚠️ Thiếu hoặc không hợp lệ biến môi trường: {varname}")
    return cleaned

# --- Nhà cung cấp (provider) và model mặc định ---
LLM_PROVIDER = _check_required_env("LLM_PROVIDER").lower()
LLM_MODEL = _check_required_env("LLM_MODEL")

# --- Khóa API cho Google và OpenRouter ---
GOOGLE_API_KEY = _check_required_env("GOOGLE_API_KEY")
OPENROUTER_API_KEY = _check_required_env("OPENROUTER_API_KEY")

# --- Cấu hình email (bắt buộc) ---
EMAIL_HOST = _check_required_env("EMAIL_HOST")
# EMAIL_PORT: làm sạch comment và chuyển sang int, mặc định 993
_raw_port = os.getenv("EMAIL_PORT", "").split('#', 1)[0].strip()
if _raw_port:
    try:
        EMAIL_PORT = int(_raw_port)
    except ValueError:
        raise RuntimeError(f"⚠️ EMAIL_PORT không hợp lệ: {_raw_port}")
else:
    EMAIL_PORT = 993

EMAIL_USER = _check_required_env("EMAIL_USER")
EMAIL_PASS = _check_required_env("EMAIL_PASS")

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
    "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-3.5-turbo",
    "google/gemini-pro-1.5", "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-8b-instruct", "meta-llama/llama-3.1-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
]

from .model_fetcher import ModelFetcher


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
    """Thiết lập và trả về cấu hình LLM"""
    config = {"provider": LLM_PROVIDER, "model": LLM_MODEL, "api_key": None, "client": None, "available_models": []}
    if LLM_PROVIDER == "google":
        available = get_models_for_provider("google", GOOGLE_API_KEY)
        config.update({"api_key": GOOGLE_API_KEY, "available_models": available})
        if LLM_MODEL not in available:
            logger.warning(f"Model {LLM_MODEL} không tồn tại, chuyển sang {available[0]}")
            config["model"] = available[0]
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        config["client"] = genai
    elif LLM_PROVIDER == "openrouter":
        available = get_models_for_provider("openrouter", OPENROUTER_API_KEY)
        config.update({"api_key": OPENROUTER_API_KEY, "available_models": available})
        if LLM_MODEL not in available:
            logger.warning(f"Model {LLM_MODEL} không tồn tại, chuyển sang {available[0]}")
            config["model"] = available[0]
    else:
        raise RuntimeError(f"Provider không hỗ trợ: {LLM_PROVIDER}")
    return config

LLM_CONFIG = validate_and_setup_llm()
