import logging
from pathlib import Path
import streamlit as st
import pandas as pd

from ..modules.cv_processor import CVProcessor
from ..modules.config import get_model_price


def render(provider: str, model: str, api_key: str, root: Path) -> None:
    """Render UI for processing a single CV file."""
    st.subheader("Xử lý một CV đơn lẻ")
    price = get_model_price(model)
    label = f"{model} ({price})" if price != 'unknown' else model
    st.markdown(f"**LLM:** `{provider}` / `{label}`")
    uploaded = st.file_uploader("Chọn file CV (.pdf, .docx)", type=["pdf", "docx"])
    if uploaded:
        tmp_file = root / f"tmp_{uploaded.name}"
        tmp_file.write_bytes(uploaded.getbuffer())
        with st.spinner(f"Đang trích xuất & phân tích... (LLM: {provider}/{label})"):
            logging.info(f"Xử lý file đơn {uploaded.name}")
            proc = CVProcessor()
            proc.llm_client.provider = provider
            proc.llm_client.model = model
            proc.llm_client.api_key = api_key
            text = proc.extract_text(str(tmp_file))
            info = proc.extract_info_with_llm(text)
        st.json(info)
        tmp_file.unlink(missing_ok=True)
