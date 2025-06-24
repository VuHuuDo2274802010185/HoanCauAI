from __future__ import annotations
from contextlib import contextmanager
import streamlit as st


@contextmanager
def loading_overlay(message: str = "Đang xử lý..."):
    """Hiển thị overlay loading toàn trang."""
    placeholder = st.empty()
    overlay_html = f"""
    <div class='loading-overlay'>
        <div class='loading-spinner'></div>
        <div class='loading-text'>{message}</div>
    </div>
    """
    placeholder.markdown(overlay_html, unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()

__all__ = ["loading_overlay"]
