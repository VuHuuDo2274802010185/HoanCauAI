"""Tab xử lý hàng loạt file CV."""

import logging
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

        with loading_logs("Đang xử lý CV..."):
            df = processor.process(unseen_only=unseen_only)

        if df.empty:
            st.info("Không có CV nào để xử lý.")
        else:
            processor.save_to_csv(df, str(OUTPUT_CSV))
            processor.save_to_excel(df, str(OUTPUT_EXCEL))
            logging.info("Đã xử lý %s CV và lưu kết quả", len(df))
            st.success(
                f"Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`."
            )
