# Thư viện logging chuẩn của Python
import logging

# traceback để in stack trace khi gặp lỗi
import traceback

# Kiểu dữ liệu cho typing
from typing import Any

# Streamlit dùng cho giao diện Web
import streamlit as st

# Tạo logger theo tên module
logger = logging.getLogger(__name__)


def handle_error(func):
    """Decorator for error handling"""

    def wrapper(*args, **kwargs):
        try:
            # Gọi hàm gốc
            return func(*args, **kwargs)
        except Exception as e:
            # Log và hiển thị lỗi
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            st.error(f"Lỗi trong {func.__name__}: {e}")
            return None

    return wrapper


def safe_session_state_get(key: str, default: Any = None) -> Any:
    """Safely get value from Streamlit session state"""
    try:
        # Lấy giá trị trong session_state, nếu không có trả về default
        return st.session_state.get(key, default)
    except Exception as e:
        # Nếu có lỗi (ví dụ session_state chưa khởi tạo)
        logger.warning(f"Error accessing session state key '{key}': {e}")
        return default


def safe_session_state_set(key: str, value: Any) -> bool:
    """Safely set value in Streamlit session state"""
    try:
        # Ghi giá trị vào session_state
        st.session_state[key] = value
        return True
    except Exception as e:
        # Ghi log cảnh báo nếu có lỗi
        logger.warning(f"Error setting session state key '{key}': {e}")
        return False

# Chỉ xuất ra những hàm hỗ trợ
__all__ = [
    "handle_error",
    "safe_session_state_get",
    "safe_session_state_set",
]
