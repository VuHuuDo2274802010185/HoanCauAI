"""Tab kết hợp lấy và xử lý CV từ email."""

import logging
from typing import List
from pathlib import Path
from datetime import datetime, time, timezone, date
import base64

from modules.progress_manager import StreamlitProgressBar

import pandas as pd
import streamlit as st

from modules.config import (
    ATTACHMENT_DIR,
    EMAIL_HOST,
    EMAIL_PORT,
    OUTPUT_CSV,
    OUTPUT_EXCEL,
    SENT_TIME_FILE,
    EMAIL_UNSEEN_ONLY,
    get_model_price,
)
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor, format_sent_time_display
from modules.dynamic_llm_client import DynamicLLMClient
from modules.sent_time_store import load_sent_times
from ..utils import safe_session_state_get


def render(
    provider: str,
    model: str,
    api_key: str,
    email_user: str = "",
    email_pass: str = "",
) -> None:
    """Render UI for fetching and processing CVs."""
    st.subheader("Lấy & Xử lý CV")
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model
    st.markdown(f"**LLM:** `{provider}` / `{label}`")
    if not email_user or not email_pass:
        st.warning("Cần nhập Gmail và mật khẩu trong sidebar để fetch CV.")
        fetcher = None
    else:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
        fetcher.connect()
        
        # Show current UID status
        if fetcher:
            last_uid = fetcher.get_last_processed_uid()
            if last_uid:
                st.info(f"📧 Last processed UID: {last_uid}")
            else:
                st.info("📧 No previous UID found - will process all emails")

    col1, col2 = st.columns(2)
    today_str = date.today().strftime("%d/%m/%Y")
    with col1:
        from_date_str = st.text_input("From (DD/MM/YYYY)", value="")
    with col2:
        to_date_str = st.text_input("To (DD/MM/YYYY)", value="", placeholder=today_str)

    unseen_only = st.checkbox(
        "👁️ Chỉ quét email chưa đọc",
        value=safe_session_state_get("unseen_only", EMAIL_UNSEEN_ONLY),
        key="unseen_only",
        help="Nếu bỏ chọn, hệ thống sẽ quét toàn bộ hộp thư",
    )
    
    ignore_last_uid = st.checkbox(
        "🔄 Bỏ qua UID đã lưu (xử lý lại tất cả email)",
        value=False,
        key="ignore_last_uid",
        help="Bỏ qua UID đã lưu và xử lý lại tất cả email từ đầu",
    )
    
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    
    with col_btn3:
        if st.button("🗑️ Reset UID", help="Xóa UID đã lưu để xử lý lại từ đầu"):
            if fetcher:
                fetcher.reset_uid_store()
                st.success("✅ Đã reset UID store!")
                st.rerun()
            else:
                st.error("❌ Cần kết nối email trước")
    
    with col_btn1:
        fetch_button = st.button("📥 Fetch", help="Tải email CV từ hộp thư")
    
    with col_btn2:
        process_button = st.button("⚙️ Process", help="Phân tích CV đã tải về")
    
    st.markdown("---")

    # Handle Fetch button
    if fetch_button:
        if not fetcher:
            st.error("❌ Cần kết nối email trước khi fetch")
        else:
            logging.info("Bắt đầu fetch CV từ email")
            from_dt = (
                datetime.combine(
                    datetime.strptime(from_date_str, "%d/%m/%Y"),
                    time.min,
                    tzinfo=timezone.utc,
                )
                if from_date_str
                else None
            )
            to_dt = (
                datetime.combine(
                    datetime.strptime(to_date_str, "%d/%m/%Y"),
                    time.max,
                    tzinfo=timezone.utc,
                )
                if to_date_str
                else None
            )
            since = from_dt.date() if from_dt else None
            before = to_dt.date() if to_dt else None
            
            status_placeholder = st.empty()
            with st.spinner("📥 Đang tải email..."):
                try:
                    status_placeholder.info("🔍 Đang tìm kiếm email...")
                    new_files = fetcher.fetch_cv_attachments(
                        since=since,
                        before=before,
                        unseen_only=unseen_only,
                        ignore_last_uid=ignore_last_uid,
                    )
                    status_placeholder.empty()
                    
                    if new_files:
                        st.success(f"✅ Đã tải xuống {len(new_files)} file CV mới:")
                        for file_path in new_files:
                            st.write(f"- {Path(file_path).name}")
                        
                        # Show updated UID status after fetch
                        new_uid = fetcher.get_last_processed_uid()
                        if new_uid:
                            st.info(f"📧 Updated last processed UID: {new_uid}")
                    else:
                        st.info("📧 Không tìm thấy CV mới để tải về")
                        
                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"❌ Lỗi khi fetch email: {e}")
                    logging.error(f"Fetch error: {e}")

    # Handle Process button  
    if process_button:
        logging.info("Bắt đầu process CV đã tải về")
        from_dt = (
            datetime.combine(
                datetime.strptime(from_date_str, "%d/%m/%Y"),
                time.min,
                tzinfo=timezone.utc,
            )
            if from_date_str
            else None
        )
        to_dt = (
            datetime.combine(
                datetime.strptime(to_date_str, "%d/%m/%Y"),
                time.max,
                tzinfo=timezone.utc,
            )
            if to_date_str
            else None
        )
        
        progress_container = st.container()
        with progress_container:
            progress_bar = StreamlitProgressBar(progress_container)
            progress_bar.initialize(100, "⚙️ Đang khởi tạo xử lý CV...")

            processor = CVProcessor(
                fetcher=None,  # Don't fetch, only process existing files
                llm_client=DynamicLLMClient(provider=provider, model=model, api_key=api_key),
            )

            def progress_callback(current, message):
                progress_bar.update(current, message)

            df = processor.process(
                unseen_only=False,  # Process all files in directory
                since=None,  # Don't filter by email dates when processing existing files
                before=None,
                from_time=from_dt,
                to_time=to_dt,
                progress_callback=progress_callback,
                ignore_last_uid=False,  # Not relevant when fetcher is None
            )

            progress_bar.finish("✅ Xử lý CV hoàn tất!")

        if df.empty:
            st.info("📁 Không có CV nào trong thư mục attachments để xử lý.")
        else:
            processor.save_to_csv(df, str(OUTPUT_CSV))
            processor.save_to_excel(df, str(OUTPUT_EXCEL))
            logging.info("Đã xử lý %s CV và lưu kết quả", len(df))
            st.success(
                f"✅ Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`."
            )

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
            return f'<a download="{path.name}" href="data:{mime};base64,{data}">{path.name}</a>'

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
        st.warning("Bạn có chắc muốn xoá toàn bộ attachments? Thao tác không thể hoàn tác.")
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
