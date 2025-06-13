# app.py
import streamlit as st
import pandas as pd
import os
import logging
from typing import Any

from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.dynamic_llm_client import DynamicLLMClient
from modules.config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, 
    OUTPUT_CSV, ATTACHMENT_DIR, LLM_CONFIG
)
from modules.model_fetcher import ModelFetcher

# Cấu hình logging để thấy output trên console khi chạy
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Load CSS styling
def load_css():
    """Load custom CSS cho theme vàng kim"""
    try:
        with open('static/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Không tìm thấy file CSS theme")

# Hàm helper để xử lý dữ liệu trước khi hiển thị
def prepare_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Chuyển đổi các list thành string để tránh lỗi pyarrow"""
    df_display = df.copy()
    for col in df_display.columns:
        df_display[col] = df_display[col].apply(
            lambda x: ', '.join(map(str, x)) if isinstance(x, list) else str(x) if x is not None else ""
        )
    return df_display

# Hàm để lấy danh sách models
@st.cache_data(ttl=300)  # Cache 5 phút
def get_available_models(provider: str, api_key: str):
    """Lấy danh sách models với cache"""
    try:
        if provider == "google" and api_key:
            return ModelFetcher.get_google_models(api_key)
        elif provider == "openrouter" and api_key:
            return ModelFetcher.get_simple_openrouter_model_ids(api_key)
        else:
            return []
    except Exception as e:
        st.error(f"Lỗi khi lấy models: {e}")
        return []

# --- Cấu hình giao diện ---
st.set_page_config(
    page_title="🔥 CV AI Processor - Gold Edition",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS theme
load_css()

# Header với styling đặc biệt
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #FFD700, #FFA500); border-radius: 15px; margin-bottom: 30px;'>
    <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
        👑 CV AI Processor - Gold Edition 👑
    </h1>
    <p style='color: white; font-size: 18px; margin: 10px 0 0 0; opacity: 0.9;'>
        Trích xuất thông tin CV thông minh với AI
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: CẤU HÌNH MODEL ---
with st.sidebar:
    st.markdown("## ⚙️ Cấu hình LLM")
    
    # Hiển thị thông tin hiện tại
    current_provider = LLM_CONFIG['provider']
    current_model = LLM_CONFIG['model']
    
    st.info(f"� Provider hiện tại: **{current_provider.upper()}**")
    st.info(f"🎯 Model hiện tại: **{current_model}**")
    
    # Chọn provider
    providers = ["google", "openrouter"]
    selected_provider = st.selectbox(
        "🏢 Chọn LLM Provider:",
        providers,
        index=providers.index(current_provider) if current_provider in providers else 0
    )
    
    # Lấy API key cho provider được chọn
    if selected_provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            st.error("❌ Thiếu GOOGLE_API_KEY trong .env")
            available_models = []
        else:
            st.success("✅ Google API Key có sẵn")
            available_models = get_available_models("google", api_key)
    else:  # openrouter
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            st.error("❌ Thiếu OPENROUTER_API_KEY trong .env")
            available_models = []
        else:
            st.success("✅ OpenRouter API Key có sẵn")
            available_models = get_available_models("openrouter", api_key)
    
    # Chọn model
    if available_models:
        st.markdown("### 🎯 Chọn Model:")
        selected_model = st.selectbox(
            f"Models khả dụng ({len(available_models)}):",
            available_models,
            index=available_models.index(current_model) if current_model in available_models else 0
        )
          # Nút apply changes
        if st.button("🔄 Áp dụng thay đổi", type="primary"):
            # Lưu vào session state để sử dụng trong app
            st.session_state.selected_provider = selected_provider
            st.session_state.selected_model = selected_model
            st.success("✅ Đã cập nhật cấu hình!")
            st.rerun()
    else:
        st.warning("⚠️ Không thể lấy danh sách models")
        st.session_state.selected_provider = current_provider
        st.session_state.selected_model = current_model
    
    # Thông tin thống kê
    st.markdown("---")
    st.markdown("### 📊 Thống kê")
    if available_models:
        st.metric("Models khả dụng", len(available_models))
    
    # Links hữu ích
    st.markdown("### 🔗 Links hữu ích")
    st.markdown("- [Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.markdown("- [OpenRouter Keys](https://openrouter.ai/keys)")
    st.markdown("- [GitHub Repo](https://github.com)")

# Lấy cấu hình từ session state hoặc mặc định
current_provider = st.session_state.get('selected_provider', LLM_CONFIG['provider'])
current_model = st.session_state.get('selected_model', LLM_CONFIG['model'])

# Hiển thị thông tin cấu hình hiện tại trên main area
st.info(f"🔧 **Cấu hình hiện tại**: {current_provider.upper()} - {current_model}")

# --- Tạo các tab chức năng ---
tab1, tab2, tab3 = st.tabs(["Xử lý hàng loạt (Email)", "Xử lý file đơn lẻ", "Xem kết quả"])

# --- TAB 1: XỬ LÝ HÀNG LOẠT TỪ EMAIL ---
with tab1:
    st.header("Kích hoạt quy trình quét Email và xử lý hàng loạt")
    st.write("Nhấn nút bên dưới để bắt đầu quá trình kết nối tới email, tải các file CV mới, dùng AI trích xuất thông tin và lưu vào file `cv_summary.csv`.")
    
    if not all([EMAIL_USER, EMAIL_PASS]):
        st.error("Chưa cấu hình `EMAIL_USER` và `EMAIL_PASS` trong file `.env`. Vui lòng cấu hình để sử dụng chức năng này.")
    else:
        if st.button("🚀 Bắt đầu xử lý hàng loạt"):
            try:
                with st.spinner("Bước 1/3: Đang kết nối đến email và tìm kiếm CV..."):
                    fetcher = EmailFetcher(host=EMAIL_HOST, port=EMAIL_PORT, user=EMAIL_USER, password=EMAIL_PASS)
                    fetcher.connect()
                    st.info("Kết nối email thành công.")
                
                with st.spinner("Bước 2/3: Đang xử lý các CV tìm thấy bằng AI..."):
                    processor = CVProcessor(fetcher)
                    # Thiết lập model/provider cho processor
                    processor.llm_client = DynamicLLMClient(current_provider, current_model)
                    df = processor.process()
                
                with st.spinner("Bước 3/3: Đang lưu kết quả..."):
                    if not df.empty:
                        processor.save_to_csv(df, OUTPUT_CSV)
                        st.success(f"Hoàn tất! Đã xử lý và lưu {len(df)} hồ sơ vào `{OUTPUT_CSV}`.")
                        
                        # Xử lý dữ liệu để tránh lỗi hiển thị
                        df_display = prepare_dataframe_for_display(df)
                        st.dataframe(df_display)
                    else:
                        st.warning("Không tìm thấy CV mới hoặc không có CV nào để xử lý.")

            except Exception as e:
                st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
                logging.error("Lỗi chi tiết:", exc_info=True)


# --- TAB 2: XỬ LÝ FILE ĐƠN LẺ ---
with tab2:
    st.header("Kiểm tra trích xuất trên một file CV duy nhất")
    st.write("Tải lên một file `.pdf` hoặc `.docx` để xem kết quả trích xuất của AI ngay lập tức.")
    
    uploaded_file = st.file_uploader("Chọn file CV...", type=["pdf", "docx"])

    if uploaded_file is not None:
        if st.button("✨ Trích xuất thông tin từ file này"):
            # Lưu file tải lên vào một vị trí tạm thời
            temp_path = os.path.join(ATTACHMENT_DIR, f"temp_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                with st.spinner("Đang đọc file và gọi AI..."):
                    processor = CVProcessor() # Khởi tạo không cần fetcher
                    # Thiết lập model/provider cho processor
                    processor.llm_client = DynamicLLMClient(current_provider, current_model)
                    text = processor.extract_text(temp_path)
                    
                    if not text or not text.strip():
                        st.error("Không thể đọc được nội dung văn bản từ file này.")
                    else:
                        info = processor.extract_info_with_llm(text)
                        st.success("Trích xuất thành công!")
                        st.json(info)
            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi xử lý file: {e}")
                logging.error("Lỗi chi tiết:", exc_info=True)
            finally:
                # Dọn dẹp file tạm sau khi xử lý xong
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# --- TAB 3: XEM KẾT QUẢ ---
with tab3:
    st.header(f"Xem và tải file kết quả: `{OUTPUT_CSV}`")
    
    if os.path.exists(OUTPUT_CSV):
        try:
            df_results = pd.read_csv(OUTPUT_CSV)
            # Xử lý dữ liệu trước khi hiển thị
            df_display = prepare_dataframe_for_display(df_results)
            st.dataframe(df_display)
            
            # Cung cấp nút tải về
            with open(OUTPUT_CSV, "rb") as f:
                st.download_button(
                    label="📥 Tải về file CSV",
                    data=f,
                    file_name=OUTPUT_CSV,
                    mime='text/csv',
                )
        except Exception as e:
            st.error(f"Không thể đọc file {OUTPUT_CSV}: {e}")
    else:
        st.warning(f"File kết quả `{OUTPUT_CSV}` chưa tồn tại. Hãy chạy quy trình xử lý ở tab đầu tiên.")