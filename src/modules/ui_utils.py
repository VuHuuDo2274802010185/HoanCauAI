# Sử dụng annotations trong tương lai để hỗ trợ typing tốt hơn
from __future__ import annotations

# contextmanager giúp định nghĩa hàm với cú pháp 'with'
from contextlib import contextmanager
from typing import Iterable

import streamlit as st


@contextmanager  # Định nghĩa context manager để sử dụng with
def loading_overlay(message: str = "Đang xử lý..."):
    """Hiển thị overlay loading toàn trang."""

    # Tạo placeholder rỗng để chèn HTML
    placeholder = st.empty()

    # HTML của overlay hiển thị spinner và thông báo
    overlay_html = f"""
    <div class='loading-overlay'>
        <div class='loading-spinner'>
            <div class='loading-dot'></div>
            <div class='loading-dot'></div>
            <div class='loading-dot'></div>
        </div>
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

def display_logs(container: st.delta_generator.DeltaGenerator, max_lines: int = 50) -> None:
    """Hiển thị log mới nhất trong container."""
    logs = st.session_state.get("logs", [])
    if not logs:
        container.info("Chưa có log nào.")
        return

    recent_logs: Iterable = logs[-max_lines:]
    log_text = ""
    for entry in recent_logs:
        if isinstance(entry, dict):
            timestamp = entry.get("timestamp", "")
            level = entry.get("level", "INFO")
            message = entry.get("message", "")
            log_text += f"[{timestamp}] {level}: {message}\n"
        else:
            log_text += f"{entry}\n"
    container.code(log_text, language="text")


@contextmanager
def loading_logs(message: str = "Đang xử lý..."):
    """Overlay loading hiển thị log realtime."""
    overlay = st.empty()

    def render(log_text: str = "") -> None:
        overlay_html = f"""
        <div class='loading-overlay'>
            <div class='loading-spinner'>
                <div class='loading-dot'></div>
                <div class='loading-dot'></div>
                <div class='loading-dot'></div>
            </div>
            <div class='loading-text'>{message}</div>
            <pre class='loading-log'>{log_text}</pre>
        </div>
        """
        overlay.markdown(overlay_html, unsafe_allow_html=True)

    # Lưu hàm cập nhật overlay vào session_state để handler có thể gọi
    st.session_state["log_overlay_updater"] = render
    render()
    try:
        yield overlay
    finally:
        overlay.empty()
        st.session_state.pop("log_overlay_updater", None)


__all__ = ["loading_overlay", "loading_logs", "display_logs"]
