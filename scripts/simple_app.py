import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from datetime import date, datetime

# Ensure the project's `src` directory is on sys.path so that the local
# `modules` package can be imported when running this script directly.
ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
for path in (ROOT, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor
from modules.dynamic_llm_client import DynamicLLMClient
from modules.config import (
    ATTACHMENT_DIR,
    OUTPUT_CSV,
    OUTPUT_EXCEL,
    EMAIL_HOST,
    EMAIL_PORT,
    LLM_PROVIDER,
    LLM_MODEL,
)

# Base directory of the project (one level up from this script)
STATIC_DIR = ROOT / "static"

def load_css() -> None:
    css_path = STATIC_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

logo_path = STATIC_DIR / "logo.png"
page_icon = str(logo_path) if logo_path.exists() else None

st.set_page_config(page_title="Resume AI Simple Mode", page_icon=page_icon)

load_css()

if logo_path.exists():
    st.image(str(logo_path))

st.title("Resume AI")
st.markdown("Nhập thông tin cần thiết và xử lý CV đơn giản.")

# --- API config ---
provider = LLM_PROVIDER
model = LLM_MODEL
api_key = st.text_input("API Key", type="password", help="Khóa API cho mô hình")

# --- Fetch CV from email ---
st.header("Lấy CV từ Email")
email_user = st.text_input("Gmail", help="Địa chỉ Gmail để lấy CV")
email_pass = st.text_input(
    "Mật khẩu", type="password", help="Mật khẩu hoặc App Password"
)
unseen_only = st.checkbox("Chỉ quét email chưa đọc", value=True)
col1, col2 = st.columns(2)
with col1:
    from_date_str = st.text_input("From (DD/MM/YYYY)", value="")
with col2:
    to_date_str = st.text_input("To (DD/MM/YYYY)", value="")

if st.button("Fetch CV"):
    if not email_user or not email_pass:
        st.warning("Vui lòng nhập Gmail và mật khẩu trước.")
    else:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
        fetcher.connect()
        since = (
            datetime.strptime(from_date_str, "%d/%m/%Y").date()
            if from_date_str
            else None
        )
        before = (
            datetime.strptime(to_date_str, "%d/%m/%Y").date()
            if to_date_str
            else None
        )
        files = fetcher.fetch_cv_attachments(
            since=since,
            before=before,
            unseen_only=unseen_only,
        )
        if files:
            st.success(f"Đã tải {len(files)} file: {files}")
        else:
            st.info("Không có file mới.")

# --- Process CV ---
st.header("Xử lý CV")
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
                    "Vị trí": info.get("vi_tri", ""),
                    "Học vấn": info.get("hoc_van", ""),
                    "Kinh nghiệm": info.get("kinh_nghiem", ""),
                    "Kỹ năng": info.get("ky_nang", ""),
                }
            )
            progress.progress(idx / total)
        df = pd.DataFrame(results)
        processor.save_to_csv(df, str(OUTPUT_CSV))
        processor.save_to_excel(df, str(OUTPUT_EXCEL))
        st.success(
            f"Đã xử lý {len(df)} CV. Kết quả lưu ở {OUTPUT_CSV} và {OUTPUT_EXCEL}"
        )

# --- View results ---
st.header("Xem kết quả")
if OUTPUT_CSV.exists():
    df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Tải CSV",
        df.to_csv(index=False, encoding="utf-8-sig").encode(),
        file_name=OUTPUT_CSV.name,
        mime="text/csv",
    )
    if OUTPUT_EXCEL.exists():
        with open(OUTPUT_EXCEL, "rb") as f:
            st.download_button(
                "Tải Excel",
                f.read(),
                file_name=OUTPUT_EXCEL.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
else:
    st.info("Chưa có kết quả để hiển thị.")
