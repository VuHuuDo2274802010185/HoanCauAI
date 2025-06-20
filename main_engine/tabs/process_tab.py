import logging
import os
import pandas as pd
import streamlit as st

from modules.cv_processor import CVProcessor
from modules.config import ATTACHMENT_DIR, OUTPUT_CSV, get_model_price
from modules.dynamic_llm_client import DynamicLLMClient


def render(provider: str, model: str, api_key: str) -> None:
    """Render UI for processing CV files in attachments."""
    st.subheader("Xử lý CV từ attachments")
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model
    st.markdown(f"**LLM:** `{provider}` / `{label}`")
    if st.button("Bắt đầu xử lý CV", help="Phân tích tất cả file trong attachments"):
        logging.info("Bắt đầu xử lý batch CV từ attachments")
        files = [
            str(p)
            for p in ATTACHMENT_DIR.glob("*")
            if p.suffix.lower() in (".pdf", ".docx")
        ]
        if not files:
            st.warning("Không có file CV trong thư mục attachments để xử lý.")
        else:
            processor = CVProcessor(
                llm_client=DynamicLLMClient(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                )
            )
            progress = st.progress(0)
            status = st.empty()
            results = []
            total = len(files)
            for idx, path in enumerate(files, start=1):
                fname = os.path.basename(path)
                status.text(f"({idx}/{total}) Đang xử lý: {fname}")
                logging.info(f"Đang xử lý {fname}")
                text = processor.extract_text(path)
                info = processor.extract_info_with_llm(text)
                results.append(
                    {
                        "Nguồn": fname,
                        "Họ tên": info.get("ten", ""),
                        "Tuổi": info.get("tuoi", ""),
                        "Email": info.get("email", ""),
                        "Điện thoại": info.get("dien_thoai", ""),
                        "Địa chỉ": info.get("dia_chi", ""),
                        "Học vấn": info.get("hoc_van", ""),
                        "Kinh nghiệm": info.get("kinh_nghiem", ""),
                        "Kỹ năng": info.get("ky_nang", ""),
                    }
                )
                progress.progress(idx / total)
            df = pd.DataFrame(
                results,
                columns=[
                    "Nguồn",
                    "Họ tên",
                    "Tuổi",
                    "Email",
                    "Điện thoại",
                    "Địa chỉ",
                    "Học vấn",
                    "Kinh nghiệm",
                    "Kỹ năng",
                ],
            )
            processor.save_to_csv(df, str(OUTPUT_CSV))
            logging.info(f"Đã xử lý {len(df)} CV và lưu kết quả")
            st.success(f"Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}`.")
