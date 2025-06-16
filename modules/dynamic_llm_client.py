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
        self.provider = provider or st.session_state.get("selected_provider", LLM_CONFIG["provider"])
        # Chọn model: ưu tiên tham số, sau đó session_state, cuối cùng LLM_CONFIG
        self.model = model or st.session_state.get("selected_model", LLM_CONFIG["model"])
        # Lấy api_key từ tham số hoặc LLM_CONFIG
        self.api_key = api_key or LLM_CONFIG.get("api_key", "")
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

        else:
            # Provider không được hỗ trợ
            raise ValueError(f"Provider không hỗ trợ: {self.provider}")

    def generate_content(self, messages: List[str]) -> str:
        """
        Gửi list messages đến LLM và trả về nội dung kết quả.
        Tự động chọn phương thức tương ứng với provider.
        """
        if self.provider == "google":
            return self._gen_google(messages)
        else:
            return self._gen_openrouter(messages)

    def _gen_google(self, messages: List[str]) -> str:
        """
        Gửi yêu cầu tới Google Gemini qua SDK.
        - messages: mỗi phần tử là chuỗi nội dung
        - Kết nối thông qua genai client
        """
        prompt = "\n".join(messages)  # ghép các message thành 1 prompt duy nhất
        try:
            resp = self.client.generate_content(prompt)  # gọi API
            return resp.text  # trả về văn bản kết quả
        except Exception as e:
            logger.error(f"❌ Lỗi Google Gemini API: {e}")
            raise

    def _gen_openrouter(self, messages: List[str]) -> str:
        """
        Gửi yêu cầu tới OpenRouter bằng HTTP POST.
        - Chuyển messages thành định dạng chat: role + content
        - Tham số điều chỉnh: temperature, max_tokens
        - Trả về nội dung text từ response JSON
        """
        # Định dạng messages cho OpenRouter: role system cho phần đầu, user cho các phần sau
        formatted = []
        for i, m in enumerate(messages):
            role = "system" if i == 0 else "user"
            formatted.append({"role": role, "content": m})

        # Chuẩn bị payload JSON theo API spec của OpenRouter
        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": 0.1,
            "max_tokens": 2000,
        }
        # Header với API key
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            # Gửi POST request và chờ tối đa 30s
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            res.raise_for_status()  # ném lỗi nếu HTTP status != 200
            data = res.json()  # parse JSON
            # Trả về nội dung message đầu tiên
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter API: {e}")
            raise
