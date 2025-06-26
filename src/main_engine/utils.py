import logging
import traceback
from typing import Any
import streamlit as st

logger = logging.getLogger(__name__)


def handle_error(func):
    """Decorator for error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            st.error(f"Lỗi trong {func.__name__}: {e}")
            return None
    return wrapper


def safe_session_state_get(key: str, default: Any = None) -> Any:
    """Safely get value from Streamlit session state"""
    try:
        return st.session_state.get(key, default)
    except Exception as e:
        logger.warning(f"Error accessing session state key '{key}': {e}")
        return default


def safe_session_state_set(key: str, value: Any) -> bool:
    """Safely set value in Streamlit session state"""
    try:
        st.session_state[key] = value
        return True
    except Exception as e:
        logger.warning(f"Error setting session state key '{key}': {e}")
        return False

__all__ = [
    "handle_error",
    "safe_session_state_get",
    "safe_session_state_set",
]
