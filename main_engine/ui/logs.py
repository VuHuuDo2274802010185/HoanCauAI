from __future__ import annotations

from datetime import datetime
import streamlit as st

from ..utils import safe_session_state_get


def update_log_display(container) -> None:
    """Render log messages stored in session state."""
    logs = safe_session_state_get("logs", [])
    if not logs:
        container.info("Chưa có log nào.")
        return
    recent_logs = logs[-50:]
    log_text = ""
    for entry in recent_logs:
        if isinstance(entry, dict):
            ts = entry.get("timestamp", "")
            level = entry.get("level", "INFO")
            msg = entry.get("message", "")
            log_text += f"[{ts}] {level}: {msg}\n"
        else:
            log_text += f"{entry}\n"
    container.code(log_text, language="text")

