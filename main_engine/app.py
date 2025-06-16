# main_engine/app.py

import os, sys
from pathlib import Path

# Đưa thư mục gốc (chứa `modules/`) vào sys.path để import modules
HERE = Path(__file__).parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

# Import cấu hình và modules
from modules.config import (
    LLM_CONFIG,
    get_models_for_provider,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    ATTACHMENT_DIR,
    OUTPUT_CSV,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASS,
)
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor

# --- Cấu hình chung cho trang Streamlit ---
st.set_page_config(
    page_title="Hoàn Cầu AI CV Processor",
    page_icon=str(ROOT / "static" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load CSS tuỳ chỉnh ---
def load_css():
    path = ROOT / "static" / "style.css"
    if path.exists():
        st.markdown(f"<style>{path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Không tìm thấy CSS tại: {path}")
load_css()

# --- Sidebar: logo và cấu hình LLM ---
logo_path = ROOT / "static" / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

st.sidebar.header("Cấu hình LLM")

# Chọn provider
provider = st.sidebar.selectbox(
    "Provider",
    options=["google", "openrouter"],
    key="selected_provider",
    help="Chọn nhà cung cấp LLM"
)

# Nhập API key theo provider
if provider == "google":
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        value=st.session_state.get("google_api_key", GOOGLE_API_KEY),
        key="google_api_key"
    )
else:
    api_key = st.sidebar.text_input(
        "OpenRouter API Key",
        type="password",
        value=st.session_state.get("openrouter_api_key", OPENROUTER_API_KEY),
        key="openrouter_api_key"
    )

if st.sidebar.button("Lấy models"):
    if not api_key:
        st.sidebar.warning("Vui lòng nhập API Key trước khi lấy models")
    else:
        st.session_state.available_models = get_models_for_provider(provider, api_key)

models = st.session_state.get("available_models", get_models_for_provider(provider, api_key))
if not models:
    st.sidebar.error("Không lấy được models, vui lòng kiểm tra API Key.")
    models = [LLM_CONFIG.get("model")]
# Đặt model mặc định nếu session chưa có hoặc không hợp lệ
if 'selected_model' not in st.session_state or st.session_state.selected_model not in models:
    st.session_state.selected_model = models[0]
# Chọn model, lưu tự động vào session_state
model = st.sidebar.selectbox(
    "Model",
    options=models,
    key="selected_model",
    help="Chọn mô hình LLM"
)

# Hiển thị cấu hình đang dùng
st.sidebar.markdown(f"**Đang dùng:** `{provider}` / `{model}`")

st.sidebar.header("Thông tin Email")
email_user = st.sidebar.text_input(
    "Gmail",
    value=st.session_state.get("email_user", EMAIL_USER),
    key="email_user",
)
email_pass = st.sidebar.text_input(
    "Mật khẩu",
    type="password",
    value=st.session_state.get("email_pass", EMAIL_PASS),
    key="email_pass",
)

# --- Main UI: 3 Tabs ---
tab1, tab2, tab3 = st.tabs(["Batch Email", "Single File", "Kết quả"])

# --- Tab 1: Batch xử lý CV từ Email ---
with tab1:
    st.subheader("Batch xử lý CV từ Email")
    st.markdown(f"**LLM:** `{provider}` / `{model}`")
    if st.button("Bắt đầu xử lý từ Email"):
        if not email_user or not email_pass:
            st.error("Cần nhập Gmail và mật khẩu")
            st.stop()
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
        fetcher.connect()
        files = fetcher.fetch_cv_attachments()
        if not files:
            st.info("Không tìm thấy file CV mới, dò trong thư mục attachments.")
            files = [
                str(ROOT / ATTACHMENT_DIR / f)
                for f in os.listdir(ROOT / ATTACHMENT_DIR)
                if f.lower().endswith((".pdf", ".docx"))
            ]
        if not files:
            st.warning("Không có file CV để xử lý.")
        else:
            processor = CVProcessor()
            # Gán provider/model/api key cho client
            processor.llm_client.provider = provider
            processor.llm_client.model = model
            processor.llm_client.api_key = api_key

            progress = st.progress(0)
            status = st.empty()
            results = []
            total = len(files)
            for idx, path in enumerate(files, start=1):
                fname = os.path.basename(path)
                status.text(f"({idx}/{total}) Đang xử lý: {fname}")
                text = processor.extract_text(path)
                info = processor.extract_info_with_llm(text)
                results.append({
                    "Nguồn": fname,
                    "Họ tên": info.get("ten", ""),
                    "Email": info.get("email", ""),
                    "Điện thoại": info.get("dien_thoai", ""),
                    "Học vấn": info.get("hoc_van", ""),
                    "Kinh nghiệm": info.get("kinh_nghiem", ""),
                })
                progress.progress(idx / total)
            status.text("Hoàn tất xử lý tất cả file.")
            df = pd.DataFrame(results)
            processor.save_to_csv(df, OUTPUT_CSV)
            st.success(f"Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}`.")

# --- Tab 2: Xử lý một CV đơn lẻ ---
with tab2:
    st.subheader("Xử lý một CV đơn lẻ")
    st.markdown(f"**LLM:** `{provider}` / `{model}`")
    uploaded = st.file_uploader("Chọn file CV (.pdf, .docx)", type=["pdf", "docx"])
    if uploaded:
        tmp_file = ROOT / f"tmp_{uploaded.name}"
        tmp_file.write_bytes(uploaded.getbuffer())
        with st.spinner(f"Đang trích xuất & phân tích... (LLM: {provider}/{model})"):
            proc = CVProcessor()
            proc.llm_client.provider = provider
            proc.llm_client.model = model
            proc.llm_client.api_key = api_key
            text = proc.extract_text(str(tmp_file))
            info = proc.extract_info_with_llm(text)
        st.json(info)
        tmp_file.unlink(missing_ok=True)

# --- Tab 3: Xem và tải kết quả ---
with tab3:
    st.subheader("Xem và tải kết quả")
    if os.path.exists(OUTPUT_CSV):
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        st.download_button(
            label="Tải xuống CSV",
            data=csv_bytes,
            file_name=OUTPUT_CSV.name,
            mime="text/csv"
        )
    else:
        st.info("Chưa có kết quả. Vui lòng chạy Batch hoặc Single.")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<center><small>Powered by Hoàn Cầu AI CV Processor</small></center>")