import os  # thư viện thao tác với hệ thống file (đọc, ghi, xóa tệp)
import streamlit as st  # framework để xây dựng ứng dụng web giao diện
import pandas as pd  # xử lý và hiển thị dữ liệu dạng DataFrame

# --- Import cấu hình và các hàm tiện ích ---
from modules.config import (
    LLM_CONFIG,               # cấu hình LLM chung (provider, model, api_key, ...)
    get_models_for_provider,  # hàm lấy danh sách models theo provider
    GOOGLE_API_KEY,           # API key Google
    OPENROUTER_API_KEY,       # API key OpenRouter
    OUTPUT_CSV,               # Path đến file CSV xuất kết quả
)
from modules.email_fetcher import EmailFetcher  # lớp kết nối IMAP và tải CV từ email
from modules.cv_processor import CVProcessor    # lớp xử lý trích xuất thông tin từ CV

# ——————————————————————————————
# 1) CẤU HÌNH TRANG STREAMLIT
# ——————————————————————————————
st.set_page_config(
    page_title="Hoàn Cầu AI CV Processor",  # tiêu đề tab trình duyệt
    layout="wide",                           # bố cục toàn chiều rộng
    initial_sidebar_state="expanded"         # mặc định sidebar mở rộng
)

# ——————————————————————————————
# 2) HÀM NẠP CSS TÙY CHỈNH
# ——————————————————————————————

def load_custom_css(path: str = "static/style.css"):
    """
    Đọc file CSS và chèn vào trang để áp dụng style tuỳ chỉnh.
    Nếu không tìm thấy file, hiển thị cảnh báo.
    """
    try:
        # mở file CSS dưới dạng text
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()  # đọc toàn bộ nội dung CSS
        # chèn CSS vào header HTML
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # nếu đường dẫn sai hoặc file không tồn tại
        st.warning(f"Không tìm thấy file CSS tại: {path}")

# gọi hàm để áp dụng CSS ngay khi load app
load_custom_css()

# ——————————————————————————————
# 3) KHỞI TẠO SESSION STATE CHO LỰA CHỌN LLM
# ——————————————————————————————
# Sử dụng session_state để lưu lựa chọn của user giữa các lần reload
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = LLM_CONFIG["provider"]  # provider mặc định
if "selected_model" not in st.session_state:
    st.session_state.selected_model = LLM_CONFIG["model"]      # model mặc định

# ——————————————————————————————
# 4) SIDEBAR: CÀI ĐẶT LLM
# ——————————————————————————————
st.sidebar.header("Cài đặt LLM")  # tiêu đề nhóm cài đặt

# 4.1) Chọn provider từ dropdown
provider = st.sidebar.selectbox(
    label="Provider",
    options=["google", "openrouter"],
    index=["google", "openrouter"].index(st.session_state.selected_provider)
)

# 4.2) Lấy API key tương ứng để fetch models
api_key = GOOGLE_API_KEY if provider == "google" else OPENROUTER_API_KEY
# 4.3) Lấy danh sách models từ API hoặc fallback
models = get_models_for_provider(provider, api_key)
# nếu không lấy được thì dùng model cũ đã lưu
if not models:
    models = [st.session_state.selected_model]
# nếu model đã lưu không còn có trong list, reset về model đầu
if st.session_state.selected_model not in models:
    st.session_state.selected_model = models[0]

# 4.4) Chọn model từ dropdown
model = st.sidebar.selectbox(
    label="Model",
    options=models,
    index=models.index(st.session_state.selected_model)
)

# 4.5) Nút áp dụng để lưu vào session và reload trang
if st.sidebar.button("Áp dụng"):
    st.session_state.selected_provider = provider
    st.session_state.selected_model = model
    try:
        # thử reload nội bộ Streamlit
        st.experimental_rerun()
    except AttributeError:
        # nếu không hỗ trợ, yêu cầu user refresh tay
        st.sidebar.info("Vui lòng refresh trang để áp dụng thay đổi.")

# ——————————————————————————————
# 5) GIAO DIỆN CHÍNH: 3 TAB
# ——————————————————————————————
tab1, tab2, tab3 = st.tabs(["Batch Email", "Single File", "Kết quả"])

# --- Tab 1: Xử lý hàng loạt từ email ---
with tab1:
    st.subheader("Batch xử lý CV từ Email")
    # Nút bắt đầu xử lý
    if st.button("Bắt đầu xử lý từ Email"):
        # 1) Kết nối IMAP và tải attachments
        fetcher = EmailFetcher()
        fetcher.connect()
        # 2) Trích xuất thông tin CV
        processor = CVProcessor(fetcher)
        df = processor.process()
        # 3) Lưu kết quả vào CSV
        processor.save_to_csv(df, OUTPUT_CSV)
        st.success(f"✅ Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}`.")

# --- Tab 2: Xử lý file đơn lẻ ---
with tab2:
    st.subheader("Xử lý một CV đơn lẻ")
    uploaded = st.file_uploader("Chọn file CV (.pdf/.docx)", type=["pdf", "docx"])
    if uploaded is not None:
        # Lưu file tạm
        tmp_path = f"temp_{uploaded.name}"
        with open(tmp_path, "wb") as tmp_file:
            tmp_file.write(uploaded.getbuffer())
        # Trích xuất text và thông tin
        proc = CVProcessor()
        text = proc.extract_text(tmp_path)
        info = proc.extract_info_with_llm(text)
        # Hiển thị kết quả JSON
        st.json(info)
        # Xóa file tạm sau sử dụng
        try:
            os.remove(tmp_path)
        except Exception as e:
            st.warning(f"Không xóa được file tạm: {e}")

# --- Tab 3: Hiển thị và tải kết quả ---
with tab3:
    st.subheader("Xem và tải kết quả");
    try:
        # Đọc CSV với encoding hỗ trợ BOM
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        # Hiển thị DataFrame
        st.dataframe(df, use_container_width=True)
        # Chuyển DataFrame thành bytes CSV để tải
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        # Nút download CSV
        st.download_button(
            label="Tải xuống CSV",
            data=csv_bytes,
            file_name=OUTPUT_CSV.name,  # chỉ tên file
            mime="text/csv",
        )
    except FileNotFoundError:
        # Nếu chưa có file kết quả
        st.info("Chưa có file kết quả. Vui lòng chạy Batch Email hoặc Single File trước.")
