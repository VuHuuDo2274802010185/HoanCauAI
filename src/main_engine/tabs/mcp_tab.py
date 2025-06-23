import logging
import os
import subprocess
import streamlit as st

from modules.config import MCP_API_KEY


def render(detect_platform) -> None:
    """Render UI for MCP server management."""
    st.subheader("MCP Server")
    st.markdown(
        "Kết nối với MCP server và các client desktop như Cherry Studio, LangFlow, VectorShift."
    )
    st.markdown("**Hướng dẫn:**")
    st.markdown(
        "1. Khởi động MCP server bằng nút bên dưới hoặc chạy: `uvicorn modules.mcp_server:app --reload --host 0.0.0.0 --port 8000`\n"
        "2. Base URL: `http://localhost:8000`\n"
        "3. Cherry Studio: cấu hình endpoint HTTP để lấy các API, thêm flow & models.\n"
        "4. LangFlow: thêm gRPC hoặc HTTP node mới trỏ đến FastAPI endpoints.\n"
        "5. Nhập API key (Google, OpenRouter, VectorShift...) và hệ thống sẽ tự nhận diện.",
        unsafe_allow_html=True,
    )

    # Ensure mcp_api_key is set before widget instantiation
    if "mcp_api_key" not in st.session_state:
        st.session_state.mcp_api_key = MCP_API_KEY

    mcp_key = st.text_input(
        "API Key cho platform",
        type="password",
        value=st.session_state.mcp_api_key,
        key="mcp_api_key",
        help="Nhập API key cho VectorShift hoặc dịch vụ tương thích",
    )

    mcp_running = (
        "mcp_process" in st.session_state
        and st.session_state.mcp_process.poll() is None
    )

    col1, col2 = st.columns(2)
    with col1:
        if not mcp_running and st.button("Khởi động MCP server"):
            detected = detect_platform(mcp_key)
            if detected == "openrouter":
                os.environ["OPENROUTER_API_KEY"] = mcp_key
            elif detected == "google":
                os.environ["GOOGLE_API_KEY"] = mcp_key
            elif detected == "vectorshift":
                os.environ["MCP_API_KEY"] = mcp_key
            st.session_state.mcp_api_key = mcp_key
            cmd = [
                "uvicorn",
                "modules.mcp_server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
            st.session_state.mcp_process = subprocess.Popen(cmd)
            msg = "Đã khởi động MCP server"
            if detected:
                msg += f" (platform: {detected})"
            st.success(msg)
        elif mcp_running:
            st.success("MCP server đang chạy")

    with col2:
        if mcp_running and st.button("Dừng MCP server"):
            st.session_state.mcp_process.terminate()
            st.session_state.mcp_process.wait()
            del st.session_state.mcp_process
            st.info("Đã dừng MCP server")

    st.markdown("---")
    st.markdown(
        "*Xem code: `modules/mcp_server.py` để biết endpoints chi tiết.*",
        unsafe_allow_html=True,
    )
