# app.py
import streamlit as st
import pandas as pd
import os
import shutil
import logging

from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, 
    OUTPUT_CSV, ATTACHMENT_DIR
)

# Cấu hình logging để thấy output trên console khi chạy
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# --- Cấu hình giao diện ---
st.set_page_config(
    page_title="Công cụ Test - Trích xuất CV AI",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Công cụ Test cho Trình trích xuất CV AI")
st.markdown("Sử dụng giao diện này để kiểm tra các chức năng cốt lõi trước khi triển khai MCP Server.")

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
                    df = processor.process()
                
                with st.spinner("Bước 3/3: Đang lưu kết quả..."):
                    if not df.empty:
                        processor.save_to_csv(df, OUTPUT_CSV)
                        st.success(f"Hoàn tất! Đã xử lý và lưu {len(df)} hồ sơ vào `{OUTPUT_CSV}`.")
                        st.dataframe(df)
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
            st.dataframe(df_results)
            
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