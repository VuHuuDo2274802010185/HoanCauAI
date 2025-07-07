"""Tab chỉnh sửa file môi trường (.env)."""  # Mô tả chức năng của module

# Import các thư viện cần thiết
from pathlib import Path  # Thư viện xử lý đường dẫn file/folder một cách hiện đại
import streamlit as st  # Framework tạo ứng dụng web
from dotenv import load_dotenv  # Thư viện để load các biến môi trường từ file .env


def render(root: Path) -> None:
    """Hiển thị giao diện chỉnh sửa file .env."""  # Hàm hiển thị giao diện chỉnh sửa file .env
    st.subheader("Chỉnh sửa file .env")  # Hiển thị tiêu đề phụ

    # Tạo đường dẫn tới file .env trong thư mục gốc
    env_path = root / ".env"
    
    # Kiểm tra xem file .env có tồn tại hay không
    if not env_path.exists():
        st.info("Chưa có file .env, sẽ tạo mới khi lưu.")  # Thông báo nếu chưa có file
        env_text = ""  # Khởi tạo nội dung rỗng
    else:
        try:
            # Đọc nội dung file .env với encoding UTF-8
            env_text = env_path.read_text(encoding="utf-8")
        except Exception as e:  # Xử lý ngoại lệ khi đọc file
            st.error(f"Không thể đọc file .env: {e}")  # Hiển thị thông báo lỗi
            env_text = ""  # Đặt nội dung rỗng nếu có lỗi

    # Tạo text area để chỉnh sửa nội dung file .env
    env_content = st.text_area("Nội dung .env", value=env_text, height=400, key="env_editor")

    # Tạo 2 cột để đặt các nút bấm
    col1, col2 = st.columns(2)
    
    # Cột 1: Nút "Lưu .env"
    with col1:
        if st.button("Lưu .env"):  # Kiểm tra nếu nút được bấm
            try:
                # Ghi nội dung mới vào file .env với encoding UTF-8
                env_path.write_text(env_content, encoding="utf-8")
                # Load lại các biến môi trường từ file .env (ghi đè các giá trị cũ)
                load_dotenv(env_path, override=True)
                st.success("Đã lưu file .env")  # Hiển thị thông báo thành công
            except Exception as e:  # Xử lý ngoại lệ khi lưu file
                st.error(f"Lỗi khi lưu file .env: {e}")  # Hiển thị thông báo lỗi

    # Cột 2: Nút "Tải lại"
    with col2:
        # Kiểm tra nếu nút được bấm và file .env tồn tại
        if st.button("Tải lại") and env_path.exists():
            try:
                # Đọc lại nội dung từ file .env
                refreshed = env_path.read_text(encoding="utf-8")
                # Cập nhật lại nội dung trong session state để hiển thị trên UI
                st.session_state.env_editor = refreshed
                st.info("Đã tải lại nội dung từ file")  # Thông báo thành công
            except Exception as e:  # Xử lý ngoại lệ khi tải lại file
                st.error(f"Lỗi tải lại file .env: {e}")  # Hiển thị thông báo lỗi

