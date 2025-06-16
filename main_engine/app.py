# main_engine/app.py

import os
import sys

# Đưa thư mục gốc (chứa `modules/`) vào sys.path để có thể import modules
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st               # framework UI
import pandas as pd                  # xử lý DataFrame

# --- Import cấu hình và tiện ích từ modules ---
from modules.config import (
    LLM_CONFIG,                      # cấu hình LLM chung
    get_models_for_provider,         # hàm lấy list models
    GOOGLE_API_KEY,                  # API key Google
    OPENROUTER_API_KEY,              # API key OpenRouter
    OUTPUT_CSV                       # đường dẫn file CSV kết quả
)
from modules.email_fetcher import EmailFetcher  # lớp fetch email + attachments
from modules.cv_processor import CVProcessor    # lớp xử lý trích xuất CV

# ——————————————————————————————
# 1) CẤU HÌNH TRANG STREAMLIT
# ——————————————————————————————
st.set_page_config(
    page_title="Hoàn Cầu AI CV Processor",  # tiêu đề tab
    layout="wide",                           # bố cục full-width
    initial_sidebar_state="expanded"         # sidebar mặc định mở
)

# ——————————————————————————————
# 2) NẠP CSS TÙY CHỈNH
# ——————————————————————————————
def load_custom_css(path: str = "static/style.css"):
    """
    Đọc file CSS và chèn vào trang cho style tuỳ chỉnh.
    Nếu không tìm thấy, hiện cảnh báo.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()                  # đọc CSS
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Không tìm thấy file CSS tại: {path}")

load_custom_css()  # áp dụng CSS ngay

# ——————————————————————————————
# 3) INIT SESSION_STATE CHO LLM
# ——————————————————————————————
# Lưu chọn provider/model giữa các reload
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = LLM_CONFIG["provider"]
if "selected_model" not in st.session_state:
    st.session_state.selected_model = LLM_CONFIG["model"]

# ——————————————————————————————
# 4) SIDEBAR: CÀI ĐẶT LLM
# ——————————————————————————————
st.sidebar.header("Cài đặt LLM")  # header sidebar

# 4.1) Chọn provider
provider = st.sidebar.selectbox(
    "Provider",
    ["google", "openrouter"],
    index=["google", "openrouter"].index(st.session_state.selected_provider)
)

# 4.2) Chọn API key tương ứng
api_key = GOOGLE_API_KEY if provider == "google" else OPENROUTER_API_KEY

# 4.3) Lấy danh sách models
models = get_models_for_provider(provider, api_key)
if not models:  # nếu API lỗi, fallback giữ model cũ
    models = [st.session_state.selected_model]
# nếu model cũ không còn trong list, reset về đầu
if st.session_state.selected_model not in models:
    st.session_state.selected_model = models[0]

# 4.4) Chọn model
model = st.sidebar.selectbox(
    "Model",
    models,
    index=models.index(st.session_state.selected_model)
)

# 4.5) Áp dụng thay đổi
if st.sidebar.button("Áp dụng"):
    st.session_state.selected_provider = provider
    st.session_state.selected_model = model
    try:
        st.experimental_rerun()  # reload nội bộ
    except AttributeError:
        st.sidebar.info("Vui lòng refresh trang để áp dụng thay đổi.")

# ——————————————————————————————
# 5) MAIN UI: 3 TABS
# ——————————————————————————————
tab1, tab2, tab3 = st.tabs(["Batch Email", "Single File", "Kết quả"])

# --- Tab 1: Batch Email ---
with tab1:
    st.subheader("Batch xử lý CV từ Email")
    if st.button("Bắt đầu xử lý từ Email"):
        fetcher = EmailFetcher()               # khởi tạo fetcher
        fetcher.connect()                      # kết nối IMAP
        processor = CVProcessor(fetcher)       # khởi tạo processor
        df = processor.process()               # chạy process
        processor.save_to_csv(df, OUTPUT_CSV)  # lưu CSV & Excel
        st.success(f"Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}`")

# --- Tab 2: Single File ---
with tab2:
    st.subheader("Xử lý một CV đơn lẻ")
    uploaded = st.file_uploader("Chọn file CV (.pdf/.docx)", type=["pdf", "docx"])
    if uploaded:
        tmp_path = f"temp_{uploaded.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getbuffer())       # ghi file tạm
        proc = CVProcessor()                    # new processor (không fetcher)
        text = proc.extract_text(tmp_path)      # trích text
        info = proc.extract_info_with_llm(text) # trích info
        st.json(info)                           # show JSON
        try:
            os.remove(tmp_path)                 # xóa file tạm
        except Exception as e:
            st.warning(f"Không xóa được file tạm: {e}")

# --- Tab 3: Results ---
with tab3:
    st.subheader("Xem và tải kết quả")
    try:
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        st.dataframe(df, use_container_width=True)        # hiển thị bảng
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        st.download_button(
            "Tải xuống CSV",
            data=csv_bytes,
            file_name=OUTPUT_CSV.name,
            mime="text/csv"
        )
    except FileNotFoundError:
        st.info("Chưa có file kết quả. Vui lòng chạy Batch hoặc Single trước.")
