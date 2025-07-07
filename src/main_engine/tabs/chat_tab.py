"""Tab hỏi đáp với AI về dữ liệu CV."""  # Mô tả chức năng của module

# Import các thư viện cần thiết
import logging  # Thư viện ghi log để theo dõi hoạt động của ứng dụng
import os  # Thư viện để thao tác với hệ điều hành và file system
import pandas as pd  # Thư viện xử lý dữ liệu dạng bảng (DataFrame)
import streamlit as st  # Framework tạo ứng dụng web
from typing import cast  # Hàm cast để ép kiểu dữ liệu
from modules.progress_manager import StreamlitProgressBar  # Module quản lý thanh tiến trình

from modules.qa_chatbot import QAChatbot  # Module chatbot hỏi đáp
from modules.config import OUTPUT_CSV  # Import đường dẫn file CSV output


def render(provider: str, model: str, api_key: str) -> None:
    """Hiển thị giao diện hỏi đáp với AI về dữ liệu CV."""  # Hàm hiển thị giao diện hỏi đáp AI
    st.subheader("Hỏi AI về dữ liệu CV")  # Hiển thị tiêu đề phụ
    
    # Kiểm tra và khởi tạo trạng thái trigger_ai trong session_state
    if 'trigger_ai' not in st.session_state:
        st.session_state.trigger_ai = False  # Đặt giá trị mặc định là False

    # Hàm callback khi người dùng gửi câu hỏi
    def submit_ai():
        st.session_state.trigger_ai = True  # Đặt flag để kích hoạt xử lý AI

    # Tạo ô nhập câu hỏi với callback khi thay đổi
    question = st.text_input(
        "Nhập câu hỏi và nhấn Enter để gửi", key="ai_question", on_change=submit_ai
    )

    # Kiểm tra nếu có trigger để xử lý câu hỏi AI
    if st.session_state.trigger_ai:
        st.session_state.trigger_ai = False  # Reset flag sau khi xử lý
        
        # Kiểm tra nếu câu hỏi trống
        if not question.strip():
            st.warning("Vui lòng nhập câu hỏi trước khi gửi.")  # Hiển thị cảnh báo
        # Kiểm tra nếu file CSV không tồn tại
        elif not os.path.exists(OUTPUT_CSV):
            st.warning("Chưa có dữ liệu CSV để hỏi.")  # Hiển thị cảnh báo
        else:
            # Đọc dữ liệu từ file CSV với encoding UTF-8
            df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
            
            # Khởi tạo chatbot với các tham số được truyền vào
            chatbot = QAChatbot(
                provider=cast(str, provider),  # Nhà cung cấp AI (ép kiểu string)
                model=cast(str, model),  # Model AI sử dụng (ép kiểu string)
                api_key=cast(str, api_key),  # API key để xác thực (ép kiểu string)
            )
            
            # Khởi tạo thanh tiến trình
            progress_bar = StreamlitProgressBar()
            progress_bar.initialize(2, "💬 Đang hỏi AI...")  # Khởi tạo với 2 bước
            
            try:
                # Ghi log thông tin về việc gửi câu hỏi
                logging.info("Đang gửi câu hỏi tới AI")
                progress_bar.update(1, "Đang chờ phản hồi...")  # Cập nhật bước 1
                
                # Gửi câu hỏi tới chatbot và nhận câu trả lời
                answer = chatbot.ask_question(question, df)
                progress_bar.finish("✅ Đã nhận câu trả lời")  # Hoàn thành thanh tiến trình
                
                # Hiển thị câu trả lời (cho phép HTML)
                st.markdown(answer, unsafe_allow_html=True)
            except Exception as e:  # Xử lý ngoại lệ
                progress_bar.finish("❌ Lỗi")  # Hoàn thành thanh tiến trình với trạng thái lỗi
                logging.error(f"Lỗi hỏi AI: {e}")  # Ghi log lỗi
                st.error(f"Lỗi khi hỏi AI: {e}")  # Hiển thị thông báo lỗi cho người dùng
