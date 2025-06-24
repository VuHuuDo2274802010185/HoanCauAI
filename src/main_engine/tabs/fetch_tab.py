import logging
from typing import List
from pathlib import Path
import streamlit as st

from modules.config import ATTACHMENT_DIR, EMAIL_HOST, EMAIL_PORT
from modules.email_fetcher import EmailFetcher


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
        if st.button("Fetch Now", help="Quét email ngay để tải CV"):
            logging.info("Thực hiện fetch email thủ công")
            fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
            fetcher.connect()
            new_files: List[str] = fetcher.fetch_cv_attachments(unseen_only=unseen_only)
            if new_files:
                st.success(f"Đã tải {len(new_files)} file mới:")
                st.write(new_files)
            else:
                st.info("Không có file đính kèm mới.")
        attachments = sorted(ATTACHMENT_DIR.glob("*"))
        if attachments:
            items = "".join(f"<li>{Path(p).name}</li>" for p in attachments)
            list_html = f"<ul>{items}</ul>"
            styled_html = (
                "<div style='max-height: 400px; overflow-y: auto; overflow-x: auto;'>"
                f"{list_html}"
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
