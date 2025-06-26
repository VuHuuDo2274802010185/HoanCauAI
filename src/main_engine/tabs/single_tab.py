"""Tab xử lý từng file CV riêng lẻ."""

import logging
from pathlib import Path
import streamlit as st

from modules.cv_processor import CVProcessor
from modules.config import get_model_price
from modules.dynamic_llm_client import DynamicLLMClient
from modules.ui_utils import loading_overlay


def render(provider: str, model: str, api_key: str, root: Path) -> None:
    """Render UI for processing a single CV file."""
    st.subheader("Xử lý một CV đơn lẻ")
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model
    st.markdown(f"**LLM:** `{provider}` / `{label}`")
    uploaded = st.file_uploader(
        "Chọn file CV (.pdf, .docx)",
        type=["pdf", "docx"],
        help="Tải lên một file CV để phân tích ngay",
    )
    if uploaded:
        tmp_file = root / f"tmp_{uploaded.name}"
        tmp_file.write_bytes(uploaded.getbuffer())
        with loading_overlay(f"Đang trích xuất & phân tích... (LLM: {provider}/{label})"):
            logging.info(f"Xử lý file đơn {uploaded.name}")
            proc = CVProcessor(
                llm_client=DynamicLLMClient(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                )
            )
            text = proc.extract_text(str(tmp_file))
            info = proc.extract_info_with_llm(text)
        st.json(info)
        tmp_file.unlink(missing_ok=True)
