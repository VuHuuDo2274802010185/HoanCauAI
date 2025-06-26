# Sử dụng annotations trong tương lai để hỗ trợ typing tốt hơn
from __future__ import annotations

# contextmanager giúp định nghĩa hàm với cú pháp 'with'
from contextlib import contextmanager

# Thư viện giao diện Streamlit
import streamlit as st


@contextmanager  # Định nghĩa context manager để sử dụng with
def loading_overlay(message: str = "Đang xử lý..."):
    """Hiển thị overlay loading toàn trang."""

    # Tạo placeholder rỗng để chèn HTML
    placeholder = st.empty()

    # HTML của overlay hiển thị spinner và thông báo
    overlay_html = f"""
    <div class='loading-overlay'>
        <div class='loading-spinner'></div>
        <div class='loading-text'>{message}</div>
    </div>
    """

    # Chèn HTML vào trang, cho phép dùng thẻ HTML tùy ý
    placeholder.markdown(overlay_html, unsafe_allow_html=True)
    try:
        # Chạy phần code bên trong khối with
        yield
    finally:
        # Xóa overlay khi kết thúc
        placeholder.empty()

__all__ = ["loading_overlay"]  # Xuất ra hàm duy nhất của module
