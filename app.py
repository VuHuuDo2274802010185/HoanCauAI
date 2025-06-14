# app.py

import streamlit as st
import pandas as pd

from modules.config import (
    LLM_CONFIG,
    get_models_for_provider,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    OUTPUT_CSV,
)
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor

# ——————————————————————————————
# 1) PHẢI LÀ LỆNH STREAMLIT ĐẦU TIÊN
# ——————————————————————————————
st.set_page_config(
    page_title="Hoàn Cầu AI CV Processor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ——————————————————————————————
# 2) LOAD EXTERNAL CSS
# ——————————————————————————————
def load_css(path: str = "static/style.css"):
    with open(path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("static/style.css")

# ——————————————————————————————
# 3) KHỞI TẠO session_state CHO SETTINGS
# ——————————————————————————————
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = LLM_CONFIG["provider"]
if "selected_model" not in st.session_state:
    st.session_state.selected_model = LLM_CONFIG["model"]

# ——————————————————————————————
# 4) SIDEBAR: LLM Settings
# ——————————————————————————————
st.sidebar.header("LLM Settings")

# Chọn provider
provider = st.sidebar.selectbox(
    "Provider",
    ["google", "openrouter"],
    index=["google", "openrouter"].index(st.session_state.selected_provider),
)

# Lấy model list động từ config
api_key = GOOGLE_API_KEY if provider == "google" else OPENROUTER_API_KEY
models = get_models_for_provider(provider, api_key)
if not models:
    # fallback nếu không lấy được
    models = [LLM_CONFIG["model"]]

# Đảm bảo model cũ còn hợp lệ
if st.session_state.selected_model not in models:
    st.session_state.selected_model = models[0]

model = st.sidebar.selectbox(
    "Model",
    models,
    index=models.index(st.session_state.selected_model),
)

# Apply button
if st.sidebar.button("Apply"):
    st.session_state.selected_provider = provider
    st.session_state.selected_model = model
    try:
        st.experimental_rerun()
    except AttributeError:
        st.sidebar.info("Please refresh the page to apply new settings.")

# ——————————————————————————————
# 5) MAIN UI: Tabs
# ——————————————————————————————
tab1, tab2, tab3 = st.tabs(["Batch Email", "Single File", "Results"])

with tab1:
    st.subheader("Process CVs from Email")
    if st.button("Start Processing"):
        fetcher = EmailFetcher()
        fetcher.connect()
        processor = CVProcessor(fetcher)
        df = processor.process()
        processor.save_to_csv(df)
        st.success(f"✅ Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV}`.")

with tab2:
    st.subheader("Process Single CV File")
    uploaded = st.file_uploader("Upload a CV (.pdf/.docx)", type=["pdf", "docx"])
    if uploaded:
        tmp_path = f"temp_{uploaded.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getbuffer())
        proc = CVProcessor()
        text = proc.extract_text(tmp_path)
        info = proc.extract_info_with_llm(text)
        st.json(info)

with tab3:
    st.subheader("View Results")
    try:
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    except FileNotFoundError:
        st.info(f"Chưa có file `{OUTPUT_CSV}`. Hãy chạy Batch Email hoặc Single File trước.")
    else:
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=OUTPUT_CSV,
            mime="text/csv",
        )
