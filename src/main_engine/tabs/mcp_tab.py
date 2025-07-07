"""Tab quản lý MCP server và API key cho client."""  # Mô tả chức năng của module

# Import các thư viện cần thiết
import os  # Thư viện để thao tác với biến môi trường và hệ điều hành
import subprocess  # Thư viện để chạy các tiến trình con (subprocess)
import streamlit as st  # Framework tạo ứng dụng web

# Import cấu hình API key mặc định cho MCP
from modules.config import MCP_API_KEY


def render(detect_platform) -> None:
    """Render UI for MCP server management."""  # Hàm hiển thị giao diện quản lý MCP server
    st.subheader("MCP Server")  # Hiển thị tiêu đề phụ
    # Hiển thị mô tả chức năng của MCP server
    st.markdown(
        "Kết nối với MCP server và các client desktop như Cherry Studio, LangFlow, VectorShift."
    )
    st.markdown("**Hướng dẫn:**")  # Tiêu đề hướng dẫn sử dụng
    # Hiển thị các bước hướng dẫn chi tiết
    st.markdown(
        "1. Khởi động MCP server bằng nút bên dưới hoặc chạy: `uvicorn modules.mcp_server:app --reload --host 0.0.0.0 --port 8000`\n"
        "2. Base URL: `http://localhost:8000`\n"
        "3. Cherry Studio: cấu hình endpoint HTTP để lấy các API, thêm flow & models.\n"
        "4. LangFlow: thêm gRPC hoặc HTTP node mới trỏ đến FastAPI endpoints.\n"
        "5. Nhập API key (Google, OpenRouter, VectorShift...) và hệ thống sẽ tự nhận diện.",
        unsafe_allow_html=True,
    )

    # Đảm bảo mcp_api_key được khởi tạo trong session_state trước khi tạo widget
    if "mcp_api_key" not in st.session_state:
        st.session_state.mcp_api_key = MCP_API_KEY  # Đặt giá trị mặc định từ config

    # Tạo ô nhập API key với kiểu password (ẩn nội dung)
    mcp_key = st.text_input(
        "API Key cho platform",  # Label của input
        type="password",  # Kiểu password để ẩn nội dung
        value=st.session_state.mcp_api_key,  # Giá trị hiện tại từ session state
        key="mcp_api_key",  # Key để lưu trong session state
        help="Nhập API key cho VectorShift hoặc dịch vụ tương thích",  # Tooltip hướng dẫn
    )

    # Kiểm tra xem MCP server có đang chạy hay không
    mcp_running = (
        "mcp_process" in st.session_state  # Kiểm tra có process trong session state
        and st.session_state.mcp_process.poll() is None  # Kiểm tra process còn chạy (poll() trả None)
    )

    # Tạo 2 cột cho các nút điều khiển
    col1, col2 = st.columns(2)
    
    # Cột 1: Nút khởi động MCP server
    with col1:
        # Hiển thị nút khởi động nếu server chưa chạy
        if not mcp_running and st.button("Khởi động MCP server"):
            detected = detect_platform(mcp_key)  # Nhận diện platform từ API key
            
            # Đặt biến môi trường tương ứng với platform được phát hiện
            if detected == "openrouter":
                os.environ["OPENROUTER_API_KEY"] = mcp_key  # Đặt API key cho OpenRouter
            elif detected == "google":
                os.environ["GOOGLE_API_KEY"] = mcp_key  # Đặt API key cho Google
            elif detected == "vectorshift":
                os.environ["MCP_API_KEY"] = mcp_key  # Đặt API key cho VectorShift
            
            st.session_state.mcp_api_key = mcp_key  # Lưu API key vào session state
            
            # Tạo command để khởi động uvicorn server
            cmd = [
                "uvicorn",  # ASGI server
                "modules.mcp_server:app",  # Module và app object
                "--host",  # Tham số host
                "0.0.0.0",  # Listen trên tất cả interface
                "--port",  # Tham số port
                "8000",  # Port 8000
            ]
            # Khởi động process và lưu vào session state
            st.session_state.mcp_process = subprocess.Popen(cmd)
            
            # Tạo thông báo thành công
            msg = "Đã khởi động MCP server"
            if detected:  # Nếu có nhận diện được platform
                msg += f" (platform: {detected})"  # Thêm tên platform vào thông báo
            st.success(msg)  # Hiển thị thông báo thành công
        elif mcp_running:  # Nếu server đang chạy
            st.success("MCP server đang chạy")  # Hiển thị trạng thái đang chạy

    # Cột 2: Nút dừng MCP server
    with col2:
        # Hiển thị nút dừng nếu server đang chạy
        if mcp_running and st.button("Dừng MCP server"):
            st.session_state.mcp_process.terminate()  # Gửi signal terminate đến process
            st.session_state.mcp_process.wait()  # Chờ process kết thúc
            del st.session_state.mcp_process  # Xóa process khỏi session state
            st.info("Đã dừng MCP server")  # Hiển thị thông báo đã dừng

    st.markdown("---")  # Tạo đường phân cách
    # Hiển thị ghi chú về code chi tiết
    st.markdown(
        "*Xem code: `modules/mcp_server.py` để biết endpoints chi tiết.*",
        unsafe_allow_html=True,
    )
