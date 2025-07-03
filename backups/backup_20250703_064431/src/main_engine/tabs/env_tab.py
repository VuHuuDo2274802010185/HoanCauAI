"""Tab chỉnh sửa file môi trường (.env)."""

from pathlib import Path
import streamlit as st
from dotenv import load_dotenv


def render(root: Path) -> None:
    """Render UI for editing the .env file."""
    st.subheader("Chỉnh sửa file .env")

    env_path = root / ".env"
    if not env_path.exists():
        st.info("Chưa có file .env, sẽ tạo mới khi lưu.")
        env_text = ""
    else:
        try:
            env_text = env_path.read_text(encoding="utf-8")
        except Exception as e:
            st.error(f"Không thể đọc file .env: {e}")
            env_text = ""

    env_content = st.text_area("Nội dung .env", value=env_text, height=400, key="env_editor")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Lưu .env"):
            try:
                env_path.write_text(env_content, encoding="utf-8")
                load_dotenv(env_path, override=True)
                st.success("Đã lưu file .env")
            except Exception as e:
                st.error(f"Lỗi khi lưu file .env: {e}")

    with col2:
        if st.button("Tải lại") and env_path.exists():
            try:
                refreshed = env_path.read_text(encoding="utf-8")
                st.session_state.env_editor = refreshed
                st.info("Đã tải lại nội dung từ file")
            except Exception as e:
                st.error(f"Lỗi tải lại file .env: {e}")

