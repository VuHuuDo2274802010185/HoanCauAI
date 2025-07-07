# Sử dụng annotations trong tương lai để hỗ trợ typing tốt hơn
from __future__ import annotations

# contextmanager giúp định nghĩa hàm với cú pháp 'with'
from typing import Iterable

import streamlit as st


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


__all__ = ["display_logs"]
