# app.py
import streamlit as st

# Cấu hình giao diện
st.set_page_config(
    page_title="Trình trích xuất CV AI",
    page_icon="static/logo.png",
    layout="centered"
)

# Logo & lời chào
st.image("static/logo.png", width=200)
st.title("👋 Chào mừng đến với Trình trích xuất CV AI")
st.markdown("""
Hệ thống này giúp bạn trích xuất thông tin từ CV nhanh chóng và dễ dàng với sự hỗ trợ từ AI.

👉 Chọn menu bên trái để bắt đầu.
""")
