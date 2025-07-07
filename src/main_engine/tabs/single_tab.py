"""Tab xử lý từng file CV riêng lẻ."""  # Mô tả chức năng của module

# Import các thư viện cần thiết
import logging  # Thư viện ghi log để theo dõi hoạt động của ứng dụng
from pathlib import Path  # Thư viện xử lý đường dẫn file/folder hiện đại
import streamlit as st  # Framework tạo ứng dụng web

# Import các module xử lý CV và AI
from modules.cv_processor import CVProcessor  # Module xử lý file CV
from modules.config import get_model_price  # Hàm lấy giá của model AI
from modules.dynamic_llm_client import DynamicLLMClient  # Client kết nối với các LLM khác nhau
from modules.progress_manager import StreamlitProgressBar  # Module quản lý thanh tiến trình


def render(provider: str, model: str, api_key: str, root: Path) -> None:
    """Render UI for processing a single CV file."""  # Hàm hiển thị giao diện xử lý file CV đơn lẻ
    st.subheader("Xử lý một CV đơn lẻ")  # Hiển thị tiêu đề phụ
    
    # Lấy giá của model và tạo label hiển thị
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model  # Thêm giá vào label nếu có
    st.markdown(f"**LLM:** `{provider}` / `{label}`")  # Hiển thị thông tin LLM đang sử dụng
    
    # Tạo widget upload file với các ràng buộc
    uploaded = st.file_uploader(
        "Chọn file CV (.pdf, .docx)",  # Label của file uploader
        type=["pdf", "docx"],  # Chỉ cho phép upload file PDF và DOCX
        help="Tải lên một file CV để phân tích ngay",  # Tooltip hướng dẫn
    )
    
    # Xử lý khi có file được upload
    if uploaded:
        # Tạo file tạm thời trong thư mục root với prefix "tmp_"
        tmp_file = root / f"tmp_{uploaded.name}"
        tmp_file.write_bytes(uploaded.getbuffer())  # Ghi nội dung file upload vào file tạm
        
        # Khởi tạo thanh tiến trình
        progress_bar = StreamlitProgressBar()
        progress_bar.initialize(2, f"Đang trích xuất & phân tích... (LLM: {provider}/{label})")  # Khởi tạo với 2 bước
        
        logging.info(f"Xử lý file đơn {uploaded.name}")  # Ghi log thông tin xử lý file
        
        # Khởi tạo CV processor với LLM client
        proc = CVProcessor(
            llm_client=DynamicLLMClient(
                provider=provider,  # Nhà cung cấp AI
                model=model,  # Model AI sử dụng
                api_key=api_key,  # API key để xác thực
            )
        )
        
        # Bước 1: Trích xuất text từ file CV
        text = proc.extract_text(str(tmp_file))
        progress_bar.update(1, "Đang phân tích với LLM...")  # Cập nhật tiến trình bước 1
        
        # Bước 2: Phân tích thông tin CV bằng LLM
        info = proc.extract_info_with_llm(text)
        progress_bar.finish("✅ Hoàn tất")  # Hoàn thành thanh tiến trình
        
        # Hiển thị kết quả phân tích dưới dạng JSON
        st.json(info)
        
        # Xóa file tạm thời (missing_ok=True để không lỗi nếu file không tồn tại)
        tmp_file.unlink(missing_ok=True)
