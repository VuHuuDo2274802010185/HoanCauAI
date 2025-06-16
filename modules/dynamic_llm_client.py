# modules/dynamic_llm_client.py

import os  # thư viện xử lý biến môi trường và hệ thống file
import requests  # thư viện HTTP để tương tác với API OpenRouter
import streamlit as st  # lấy thông tin session_state trong Streamlit
import logging  # ghi log xử lý
from typing import List  # định nghĩa kiểu cho danh sách

from .config import LLM_CONFIG  # cấu hình chung LLM từ modules/config.py

# --- Thiết lập logger cho module dynamic_llm_client ---
logger = logging.getLogger(__name__)  # lấy logger theo tên module
logger.setLevel(logging.INFO)  # mức log tối thiểu INFO
logger.addHandler(logging.StreamHandler())  # xuất log ra console

class DynamicLLMClient:
    """
    Client LLM động sử dụng cho giao diện Streamlit.
    - Lấy provider và model từ session_state hoặc LLM_CONFIG
    - Tự cấu hình API key và client phù hợp
    """
    def __init__(self,
                 provider: str = None,
                 model: str = None,
                 api_key: str = None):
        # Chọn provider: ưu tiên tham số, sau đó session_state, cuối cùng LLM_CONFIG
        self.provider = provider or st.session_state.get(
            "selected_provider", LLM_CONFIG["provider"]
        )
        # Chọn model: ưu tiên tham số, sau đó session_state, cuối cùng LLM_CONFIG
        self.model = model or st.session_state.get(
            "selected_model", LLM_CONFIG["model"]
        )
        # Lấy api_key: ưu tiên tham số, sau đó session_state, cuối cùng config
        session_key = (
            st.session_state.get("google_api_key")
            if self.provider == "google"
            else st.session_state.get("openrouter_api_key")
        )
        self.api_key = api_key or session_key or LLM_CONFIG.get("api_key", "")
        # Thiết lập client theo provider đã chọn
        self._setup()

    def _setup(self):
        """
        Cấu hình client LLM dựa trên provider:
        - google: cấu hình SDK google.generativeai
        - openrouter: lưu key, sẽ dùng HTTP requests
        """
        if self.provider == "google":
            # Cấu hình Google Gemini SDK
            import google.generativeai as genai
            if not self.api_key:
                raise ValueError("Google API key không có sẵn")
            genai.configure(api_key=self.api_key)
            # Tạo client cho model đã chọn
            self.client = genai.GenerativeModel(self.model)

        elif self.provider == "openrouter":
            # Sử dụng HTTP request cho OpenRouter
            if not self.api_key:
                raise ValueError("OpenRouter API key không có sẵn")
            # Không có SDK, sẽ dùng requests trong phương thức _gen_openrouter
            self.client = None