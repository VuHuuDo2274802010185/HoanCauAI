"""Tab tải file CV từ hộp thư email."""

import logging
from typing import List
from pathlib import Path
from datetime import datetime
import base64
import pandas as pd
import streamlit as st

from modules.config import (
    ATTACHMENT_DIR,
    EMAIL_HOST,
    EMAIL_PORT,
    SENT_TIME_FILE,
)
from modules.email_fetcher import EmailFetcher
from modules.ui_utils import loading_logs
from modules.sent_time_store import load_sent_times
from modules.cv_processor import format_sent_time_display


def render(email_user: str, email_pass: str, unseen_only: bool) -> None:
    """Render UI for fetching CVs from email."""
    st.subheader("Lấy CV từ Email")
    st.markdown(
        "**Email Config:** Khi đã nhập Gmail và mật khẩu ở sidebar, hệ thống sẽ tự động tải CV mới."
    )
    if not email_user or not email_pass:
        st.warning("Cần nhập Gmail và mật khẩu trong sidebar để bắt đầu auto fetch.")
    else:
        st.info(
            "Auto fetch đang chạy ngầm. Bạn có thể nhấn 'Fetch Now' để kiểm tra ngay."
        )
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From", value=None)
        with col2:
            to_date = st.date_input("To", value=None)
        if st.button("Fetch Now", help="Quét email ngay để tải CV"):
            logging.info("Thực hiện fetch email thủ công")
            with loading_logs("Đang quét email..."):
                fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
                fetcher.connect()
                new_files: List[str] = fetcher.fetch_cv_attachments(
                    since=from_date,
                    before=to_date,
                    unseen_only=unseen_only,
                )
            if new_files:
                st.success(f"Đã tải {len(new_files)} file mới:")
                st.write(new_files)
            else:
                st.info("Không có file đính kèm mới.")
        attachments = [
            p
            for p in ATTACHMENT_DIR.glob("*")
            if p.is_file()
            and p != SENT_TIME_FILE
            and p.suffix.lower() in (".pdf", ".docx")
        ]
        if attachments:
            sent_map = load_sent_times()

            def sort_key(p: Path) -> float:
                ts = sent_map.get(p.name)
                if ts:
                    try:
                        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                    except Exception:
                        pass
                return p.stat().st_mtime

            attachments.sort(key=sort_key, reverse=True)

            def make_link(path: Path) -> str:
                data = base64.b64encode(path.read_bytes()).decode()
                mime = (
                    "application/pdf"
                    if path.suffix.lower() == ".pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                return (
                    f'<a download="{path.name}" href="data:{mime};base64,{data}">{path.name}</a>'
                )

            rows = []
            for p in attachments:
                sent = format_sent_time_display(sent_map.get(p.name, ""))
                size_kb = p.stat().st_size / 1024
                rows.append({
                    "File": make_link(p),
                    "Dung lượng": f"{size_kb:.1f} KB",
                    "Gửi lúc": sent,
                })

            df = pd.DataFrame(rows, columns=["File", "Dung lượng", "Gửi lúc"])
            table_html = df.to_html(escape=False, index=False)
            styled_html = (
                "<div class='attachments-table-container' style='max-height: 400px; overflow:auto;'>"
                f"{table_html}"
                "</div>"
            )
            st.markdown(styled_html, unsafe_allow_html=True)
        else:
            st.info("Chưa có CV nào được tải về.")
    if st.button("Xóa toàn bộ attachments", help="Xoá tất cả file đã tải"):
        st.session_state.confirm_delete = True
    if st.session_state.get("confirm_delete"):
        st.warning(
            "Bạn có chắc muốn xoá toàn bộ attachments? Thao tác không thể hoàn tác."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Xác nhận xoá", key="confirm_delete_btn"):
                attachments = list(ATTACHMENT_DIR.iterdir())
                count = sum(1 for f in attachments if f.is_file())
                for f in attachments:
                    try:
                        f.unlink()
                    except Exception:
                        pass
                logging.info(f"Đã xóa {count} file trong attachments")
                st.success(f"Đã xóa {count} file trong thư mục attachments.")
                st.session_state.confirm_delete = False
        with col2:
            if st.button("Huỷ", key="cancel_delete_btn"):
                st.session_state.confirm_delete = False
