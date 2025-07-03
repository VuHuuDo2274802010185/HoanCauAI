"""Tab xử lý hàng loạt file CV."""

import logging
from datetime import datetime, time, timezone
import streamlit as st

from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.config import (
    OUTPUT_CSV,
    OUTPUT_EXCEL,
    EMAIL_HOST,
    EMAIL_PORT,
    get_model_price,
)
from modules.dynamic_llm_client import DynamicLLMClient
from modules.ui_utils import loading_logs


def render(
    provider: str,
    model: str,
    api_key: str,
    email_user: str = "",
    email_pass: str = "",
    unseen_only: bool = True,
) -> None:
    """Render UI for processing CV files from attachments or email."""
    st.subheader("Xử lý CV từ attachments hoặc email")
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model
    st.markdown(f"**LLM:** `{provider}` / `{label}`")

    col1, col2 = st.columns(2)
    with col1:
        from_date_str = st.text_input("From date (DD/MM/YYYY)", value="", key="cv_from")
    with col2:
        to_date_str = st.text_input("To date (DD/MM/YYYY)", value="", key="cv_to")

    if st.button(
        "Bắt đầu xử lý CV",
        help="Phân tích CV trong attachments hoặc fetch từ email nếu có thông tin",
    ):
        logging.info("Bắt đầu xử lý batch CV")
        fetcher = None
        if email_user and email_pass:
            try:
                fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
                fetcher.connect()
            except Exception as e:
                st.error(f"Không thể kết nối email: {e}")
                logging.error("Email connection failed: %s", e)
                fetcher = None

        processor = CVProcessor(
            fetcher,
            llm_client=DynamicLLMClient(provider=provider, model=model, api_key=api_key),
        )

        from_dt = (
            datetime.combine(
                datetime.strptime(from_date_str, "%d/%m/%Y"),
                time.min,
                tzinfo=datetime.timezone.utc,
            )
            if from_date_str
            else None
        )
        to_dt = (
            datetime.combine(
                datetime.strptime(to_date_str, "%d/%m/%Y"),
                time.max,
                tzinfo=datetime.timezone.utc,
            )
            if to_date_str
            else None
        )

        since = from_dt.date() if from_dt else None
        before = to_dt.date() if to_dt else None

        with loading_logs("Đang xử lý CV..."):
            df = processor.process(
                unseen_only=unseen_only,
                since=since,
                before=before,
                from_time=from_dt,
                to_time=to_dt,
            )

        if df.empty:
            st.info("Không có CV nào để xử lý.")
        else:
            processor.save_to_csv(df, str(OUTPUT_CSV))
            processor.save_to_excel(df, str(OUTPUT_EXCEL))
            logging.info("Đã xử lý %s CV và lưu kết quả", len(df))
            st.success(
                f"Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`."
            )
