# Utility functions and initialization helpers for the Streamlit app
import sys
import logging
import traceback
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Ensure repository root is on sys.path
HERE = Path(__file__).parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure log directory exists
LOG_DIR = ROOT / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# --- Error handling utilities ---
def handle_error(func):
    """Decorator to log and display Streamlit errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:  # pragma: no cover - UI error handling
            logger.error("Error in %s: %s", func.__name__, e)
            logger.error(traceback.format_exc())
            st.error(f"Lỗi trong {func.__name__}: {e}")
            return None

    return wrapper


# Session state helpers

def safe_session_state_get(key: str, default: Any = None) -> Any:
    try:
        return st.session_state.get(key, default)
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Error accessing session key %s: %s", key, e)
        return default


def safe_session_state_set(key: str, value: Any) -> bool:
    try:
        st.session_state[key] = value
        return True
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Error setting session key %s: %s", key, e)
        return False


# Configuration validation

def validate_configuration() -> Dict[str, bool]:
    config_status = {
        "env_file": (ROOT / ".env").exists(),
        "config_module": True,
        "static_files": (ROOT / "static").exists(),
        "modules": True,
    }
    try:
        import modules.qa_chatbot  # noqa: F401
        config_status["qa_module"] = True
    except Exception:
        config_status["qa_module"] = False
    return config_status


# Initialize default session state

def initialize_session_state() -> None:
    defaults = {
        "conversation_history": [],
        "background_color": "#fffbf0",
        "text_color": "#000000",
        "accent_color": "#d4af37",
        "secondary_color": "#f4e09c",
        "font_family_index": 0,
        "font_size": 14,
        "border_radius": 8,
        "layout_compact": False,
        "app_initialized": False,
        "last_error": None,
        "error_count": 0,
        "logs": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            safe_session_state_set(k, v)


class StreamlitLogHandler(logging.Handler):
    """Send log messages to Streamlit session state."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - UI
        try:
            if not self._check_streamlit_context():
                return
            msg = self.format(record)
            logs = safe_session_state_get("logs", [])
            if len(logs) > 500:
                logs = logs[-400:]
            logs.append(
                {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "message": msg,
                    "module": record.module,
                }
            )
            safe_session_state_set("logs", logs)
        except Exception as e:
            print(f"StreamlitLogHandler error: {e}")

    def _check_streamlit_context(self) -> bool:
        try:
            return bool(st.runtime.exists())
        except Exception:
            try:
                return (
                    st.runtime.scriptrunner.get_script_run_ctx(suppress_warning=True)
                    is not None
                )
            except Exception:
                return False


def configure_streamlit_page() -> None:
    """Configure basic Streamlit page settings."""
    st.set_page_config(
        page_title="Hoàn Cầu AI CV Processor",
        page_icon=str(ROOT / "static" / "logo.png"),
        layout="wide",
        initial_sidebar_state="expanded",
    )


@handle_error
def load_css() -> None:
    css_path = ROOT / "static" / "style.css"
    if css_path.exists():
        try:
            st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
        except Exception as e:
            logger.error("Failed to load CSS: %s", e)
            st.warning(f"Không thể tải CSS: {e}")


@handle_error
def detect_platform(api_key: str) -> Optional[str]:
    if not api_key or not isinstance(api_key, str):
        return None
    api_key = api_key.strip()
    patterns = {
        "openrouter": ["sk-or-", "or-"],
        "google": ["AIza"],
        "vectorshift": ["vs-", "vectorshift"],
    }
    for platform, prefixes in patterns.items():
        if any(api_key.lower().startswith(p.lower()) for p in prefixes):
            return platform
    endpoints = [
        ("openrouter", "https://openrouter.ai/api/v1/models", {"Authorization": f"Bearer {api_key}"}),
        ("google", f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}", {}),
    ]
    for platform, url, headers in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return platform
        except requests.RequestException:
            continue
    return None


@handle_error
def get_available_models(provider: str, api_key: str) -> list:
    cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
    cached = safe_session_state_get(cache_key)
    if cached and isinstance(cached, dict):
        if time.time() - cached.get("timestamp", 0) < 300:
            return cached.get("models", [])
    try:
        from modules.config import get_models_for_provider, LLM_CONFIG

        models = get_models_for_provider(provider, api_key)
        if models:
            safe_session_state_set(
                cache_key, {"models": models, "timestamp": time.time()}
            )
            return models
    except Exception as e:
        logger.error("Failed to get models: %s", e)
    from modules.config import LLM_CONFIG

    return [LLM_CONFIG.get("model", "gemini-2.0-flash")]


def initialize_app():
    """Initial setup for Streamlit app."""
    if safe_session_state_get("app_initialized", False):
        return
    initialize_session_state()
    handler = StreamlitLogHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s - %(message)s"))
    logging.getLogger().addHandler(handler)
    configure_streamlit_page()
    load_css()
    safe_session_state_set("app_initialized", True)


