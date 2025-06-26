# modules/config.py

import os  # thư viện xử lý biến môi trường và hệ thống file
from pathlib import Path  # thư viện để thao tác đường dẫn hệ thống
from typing import Dict, Any, List  # khai báo kiểu cho biến và hàm
from dotenv import load_dotenv  # thư viện để load file .env
import logging  # thư viện quản lý log
import shutil  # thao tác tệp và thư mục

# --- Tải biến môi trường từ file .env ở thư mục gốc ---
load_dotenv()  # đọc và gán các biến trong .env vào môi trường hệ thống

# --- Cấu hình logging cơ bản ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Project root directory (parent của thư mục modules)
BASE_DIR = Path(__file__).resolve().parents[2]


def _get_env(varname: str, default: str = "") -> str:
    """Đọc biến môi trường, bỏ comment và dấu nháy, trả về chuỗi."""
    raw = os.getenv(varname, default)
    cleaned = raw.split('#', 1)[0].strip()
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    return cleaned

# --- Nhà cung cấp (provider) và model mặc định ---
LLM_PROVIDER = _get_env("LLM_PROVIDER", "google").lower()
LLM_MODEL = _get_env("LLM_MODEL", "gemini-2.5-flash-lite-preview-06-17")

# --- Khóa API cho Google, OpenRouter và các platform khác (không bắt buộc) ---
GOOGLE_API_KEY = _get_env("GOOGLE_API_KEY")
OPENROUTER_API_KEY = _get_env("OPENROUTER_API_KEY")
MCP_API_KEY = _get_env("MCP_API_KEY")  # API key dùng cho MCP server (tự nhận diện)

# --- Base URL cho OpenRouter API ---
# Có thể tuỳ chỉnh qua biến môi trường OPENROUTER_BASE_URL
# Dùng chung cho mọi client và fetcher
OPENROUTER_BASE_URL = _get_env(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)

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

# --- Tuỳ chọn quét email: chỉ UNSEEN hay tất cả ---
def _get_bool(varname: str, default: bool = True) -> bool:
    val = os.getenv(varname)
    if val is None:
        return default
    cleaned = val.split('#', 1)[0].strip().lower()
    return cleaned not in ("0", "false", "no", "")

EMAIL_UNSEEN_ONLY = _get_bool("EMAIL_UNSEEN_ONLY", True)

# --- Thư mục lưu file đính kèm và file xuất kết quả ---
def _clean_path(varname: str, default: str) -> Path:
    """
    Lấy biến môi trường, loại bỏ comment và dấu nháy, trả về Path.
    """
    raw = os.getenv(varname, default)
    cleaned = raw.split('#', 1)[0].strip()
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    path = Path(cleaned)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path

# Thư mục lưu log chung
LOG_DIR = _clean_path("LOG_DIR", "log")
LOG_FILE = _clean_path("LOG_FILE", str(LOG_DIR / "app.log"))

ATTACHMENT_DIR = _clean_path("ATTACHMENT_DIR", "attachments")
OUTPUT_CSV = _clean_path("OUTPUT_CSV", "csv/cv_summary.csv")
OUTPUT_EXCEL = _clean_path("OUTPUT_EXCEL", "excel/cv_summary.xlsx")
# File lưu log hội thoại chat
CHAT_LOG_FILE = _clean_path("CHAT_LOG_FILE", str(LOG_DIR / "chat_log.json"))
# tạo thư mục nếu chưa tồn tại
ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_EXCEL.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
CHAT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Danh sách models dự phòng ---
GOOGLE_FALLBACK_MODELS: List[str] = [
    # Common Gemini models (flash, pro, vision) and extended variants
    "gemini-1.0", "gemini-1.0-pro", "gemini-1.5-flash", "gemini-1.5-flash-latest",
    "gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro", "gemini-pro-vision",
    # Newer and experimental variants
    "gemini-2.0-alpha", "gemini-2.0-vision", "gemini-2.0-vision-extended",
    "gemini-2.0-flash", "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.5-pro", "gemini-2.5-pro-latest"
]
OPENROUTER_FALLBACK_MODELS: List[str] = [
    "anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku",
    "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-3.5-turbo",
]

# --- Bảng giá tham khảo cho từng model ---
MODEL_PRICES: Dict[str, str] = {
    # Google Gemini
    "gemini-1.5-flash": "free",
    "gemini-1.5-flash-latest": "free",
    "gemini-1.5-pro": "1$/token",
    "gemini-1.5-pro-latest": "1$/token",
    "gemini-pro": "1$/token",
    "gemini-pro-vision": "1$/token",
    "gemini-2.0-flash": "unknown",
    "gemini-2.5-flash-lite-preview-06-17": "unknown",
    # OpenRouter fallback models (giá tham khảo, có thể thay đổi)
    "anthropic/claude-3.5-sonnet": "variable",
    "anthropic/claude-3-haiku": "variable",
    "openai/gpt-4o": "variable",
    "openai/gpt-4o-mini": "variable",
    "openai/gpt-3.5-turbo": "variable",
}

def get_model_price(model: str) -> str:
    """Trả về giá (chuỗi) của model hoặc 'unknown' nếu không có."""
    return MODEL_PRICES.get(model, "unknown")

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
    """Lấy models từ API và kết hợp với fallback để đảm bảo đầy đủ các variant"""
    available = get_available_models(provider, api_key)
    if provider == "google":
        # Kết hợp API-fetched và fallback để bao gồm hết các Gemini variants
        combined = list({*available, *GOOGLE_FALLBACK_MODELS})
        sorted_models = sorted(combined)
        logger.info(f"Sử dụng tổng cộng {len(sorted_models)} models Google (API + fallback)")
        return sorted_models
    else:
        # OpenRouter: nếu API gọi thành công, dùng API, ngược lại dùng fallback
        if available:
            logger.info(f"Đã lấy {len(available)} models từ OpenRouter API")
            return available
        logger.warning("Sử dụng fallback models cho OpenRouter")
        return OPENROUTER_FALLBACK_MODELS

# --- Cấu hình LLM mặc định ---
LLM_CONFIG = {
    "provider": LLM_PROVIDER,
    "model": LLM_MODEL,
    "api_key": GOOGLE_API_KEY if LLM_PROVIDER == "google" else OPENROUTER_API_KEY,
    "available_models": get_models_for_provider(
        LLM_PROVIDER, 
        GOOGLE_API_KEY if LLM_PROVIDER == "google" else OPENROUTER_API_KEY
    ),
}

# --- Enhanced configuration validation ---
def validate_api_key(api_key: str, provider: str) -> bool:
    """Validate API key format for different providers."""
    if not api_key or not isinstance(api_key, str):
        return False
    
    api_key = api_key.strip()
    
    if provider == "google":
        return api_key.startswith("AIza") and len(api_key) > 10
    elif provider == "openrouter":
        return api_key.startswith("sk-or-") and len(api_key) > 20
    elif provider == "vectorshift":
        return ("vectorshift" in api_key.lower() or api_key.lower().startswith("vs-")) and len(api_key) > 10
    
    return len(api_key) > 10  # Basic length check for unknown providers


def validate_email_config(host: str, port: int, user: str, password: str) -> Dict[str, bool]:
    """Validate email configuration."""
    return {
        "host_valid": bool(host and isinstance(host, str) and "." in host),
        "port_valid": isinstance(port, int) and 1 <= port <= 65535,
        "user_valid": bool(user and isinstance(user, str) and "@" in user),
        "password_valid": bool(password and isinstance(password, str) and len(password) > 3)
    }


def get_config_status() -> Dict[str, Any]:
    """Get comprehensive configuration status."""
    return {
        "llm_config": {
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
            "google_key_valid": validate_api_key(GOOGLE_API_KEY, "google"),
            "openrouter_key_valid": validate_api_key(OPENROUTER_API_KEY, "openrouter"),
            "mcp_key_available": bool(MCP_API_KEY)
        },
        "email_config": validate_email_config(EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS),
        "paths": {
            "attachment_dir_exists": ATTACHMENT_DIR.exists(),
            "output_csv_parent_exists": OUTPUT_CSV.parent.exists(),
            "chat_log_parent_exists": CHAT_LOG_FILE.parent.exists(),
            "log_dir_exists": LOG_DIR.exists(),
            "log_file_parent_exists": LOG_FILE.parent.exists()
        }
    }


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        ATTACHMENT_DIR,
        OUTPUT_CSV.parent,
        LOG_DIR,
        CHAT_LOG_FILE.parent,
        LOG_FILE.parent,
    ]
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

def cleanup_legacy_log_dirs() -> None:
    """Move logs from old directories (.log, logs) into LOG_DIR."""
    alt_dirs = [BASE_DIR / ".log", BASE_DIR / "logs"]
    for alt_dir in alt_dirs:
        if alt_dir == LOG_DIR:
            continue
        if alt_dir.exists() and alt_dir.is_dir():
            for item in alt_dir.iterdir():
                dest = LOG_DIR / item.name
                try:
                    if dest.exists():
                        dest = LOG_DIR / f"{alt_dir.name}_{item.name}"
                    shutil.move(str(item), dest)
                    logger.info(f"Moved {item} to {dest}")
                except Exception as e:
                    logger.warning(f"Could not move {item} from {alt_dir}: {e}")
            try:
                alt_dir.rmdir()
                logger.info(f"Removed legacy log dir {alt_dir}")
            except Exception:
                pass


# --- Auto-ensure directories on module import ---
ensure_directories()
cleanup_legacy_log_dirs()


# --- Enhanced model fetching ---
