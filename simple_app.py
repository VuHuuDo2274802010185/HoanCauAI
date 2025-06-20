import os
from pathlib import Path
import pandas as pd
import streamlit as st
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor
from modules.dynamic_llm_client import DynamicLLMClient
from modules.config import (
    ATTACHMENT_DIR,
    OUTPUT_CSV,
    EMAIL_HOST,
    EMAIL_PORT,
)

ROOT = Path(__file__).parent

def load_css() -> None:
    css_path = ROOT / "static" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

logo_path = ROOT / "static" / "logo.png"
page_icon = str(logo_path) if logo_path.exists() else None

st.set_page_config(page_title="Resume AI Simple Mode", page_icon=page_icon)

load_css()

if logo_path.exists():
    st.image(str(logo_path), width=180)

st.title("Resume AI - Simple Mode")
st.markdown("Làm theo từng bước để tải và xử lý CV một cách dễ dàng.")

# --- Step 1: API config ---
provider = st.selectbox(
    "Provider", ["google", "openrouter"], help="Chọn nhà cung cấp LLM"
)
api_key = st.text_input("API Key", type="password", help="Nhập khóa API cho provider")
model = st.text_input("Model", "gemini-2.0-flask", help="Tên model muốn sử dụng")

# --- Step 2: Fetch CV from email ---
st.header("Bước 1: Lấy CV từ Email")
email_user = st.text_input("Gmail", help="Địa chỉ Gmail để lấy CV")
email_pass = st.text_input(
    "Mật khẩu", type="password", help="Mật khẩu hoặc App Password"
)
unseen_only = st.checkbox("Chỉ quét email chưa đọc", value=True)

if st.button("Fetch CV"):
    if not email_user or not email_pass:
        st.warning("Vui lòng nhập Gmail và mật khẩu trước.")
    else:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
        fetcher.connect()
        files = fetcher.fetch_cv_attachments(unseen_only=unseen_only)
        if files:
            st.success(f"Đã tải {len(files)} file: {files}")
        else:
            st.info("Không có file mới.")

# --- Step 3: Process CV ---
st.header("Bước 2: Xử lý CV")
if st.button("Process CV"):
    cv_files = [
        str(p)
        for p in ATTACHMENT_DIR.glob("*")
        if p.suffix.lower() in (".pdf", ".docx")
    ]
    if not cv_files:
        st.warning("Không có file CV trong attachments.")
    else:
        processor = CVProcessor(
            llm_client=DynamicLLMClient(provider=provider, model=model, api_key=api_key)
        )
        progress = st.progress(0)
        results = []
        total = len(cv_files)
        for idx, path in enumerate(cv_files, start=1):
            text = processor.extract_text(path)
            info = processor.extract_info_with_llm(text)
            results.append(
                {
                    "Nguồn": os.path.basename(path),
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
        df = pd.DataFrame(results)
        processor.save_to_csv(df, str(OUTPUT_CSV))
        st.success(f"Đã xử lý {len(df)} CV. Kết quả lưu ở {OUTPUT_CSV}")

# --- Step 4: View results ---
st.header("Bước 3: Xem kết quả")
if OUTPUT_CSV.exists():
    df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Tải CSV",
        df.to_csv(index=False, encoding="utf-8-sig").encode(),
        file_name=OUTPUT_CSV.name,
        mime="text/csv",
    )
else:
    st.info("Chưa có kết quả để hiển thị.")
