"""Tab xử lý từng file CV riêng lẻ."""

import logging
from pathlib import Path
import streamlit as st

from modules.cv_processor import CVProcessor
from modules.config import get_model_price
from modules.dynamic_llm_client import DynamicLLMClient


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
        
        # Tạo progress bar và status text
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text(f"🔍 Đang trích xuất văn bản từ {uploaded.name}...")
            progress_bar.progress(0.3)
            
            logging.info(f"Xử lý file đơn {uploaded.name}")
            proc = CVProcessor(
                llm_client=DynamicLLMClient(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                )
            )
            
            text = proc.extract_text(str(tmp_file))
            progress_bar.progress(0.6)
            status_text.text(f"🤖 Đang phân tích với {provider}/{label}...")
            
            info = proc.extract_info_with_llm(text)
            progress_bar.progress(1.0)
            status_text.text("✅ Hoàn thành phân tích!")
            
            # Ẩn progress bar và status sau một chút
            import time as time_module
            time_module.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Lỗi khi xử lý file: {e}")
            tmp_file.unlink(missing_ok=True)
            return
            
        st.json(info)
        tmp_file.unlink(missing_ok=True)
