# modules/llm_client.py

import logging                     # thư viện ghi log
import requests                    # thư viện HTTP để gửi yêu cầu tới API OpenRouter
from typing import List           # khai báo kiểu List cho Python 3.8+

from .config import LLM_CONFIG, OPENROUTER_BASE_URL  # import cấu hình LLM và URL chung

# --- Thiết lập logger cho module llm_client ---
logger = logging.getLogger(__name__)        # lấy logger theo tên module hiện tại
logger.setLevel(logging.INFO)               # đặt mức log tối thiểu là INFO
logger.addHandler(logging.StreamHandler())   # thêm handler để xuất log ra console


class LLMClient:
    """
    Client LLM đồng nhất cho mọi script backend.
    Sử dụng thông tin provider, model, api_key từ LLM_CONFIG.
    """

    def __init__(self):
        """
        Khởi tạo LLMClient:
        - Lấy provider, model, api_key từ LLM_CONFIG
        - Cấu hình client tương ứng: Google SDK hoặc HTTP cho OpenRouter
        """
        self.provider = LLM_CONFIG["provider"]  # provider hiện tại (google hoặc openrouter)
        self.model = LLM_CONFIG["model"]        # model hiện tại (ví dụ gemini-1.5-flash-latest)
        self.api_key = LLM_CONFIG["api_key"]    # api_key tương ứng

        # Thiết lập client dựa trên provider
        if self.provider == "google":
            # Nếu là Google Gemini: cấu hình SDK
            import google.generativeai as genai   # import Google Gemini SDK
            genai.configure(api_key=self.api_key)  # cấu hình API key
            self.client = genai.GenerativeModel(self.model)  # khởi tạo client với model đã chọn
        elif self.provider == "openrouter":
            # Nếu là OpenRouter: không có SDK, sẽ dùng requests trong _gen_openrouter
            self.client = None
        else:
            # Nếu provider không hợp lệ, báo lỗi
            raise ValueError(f"Provider không hỗ trợ: {self.provider}")

    def generate_content(self, messages: List[str]) -> str:
        """
        Gửi danh sách messages tới LLM và trả về nội dung kết quả.
        Tự động chọn phương thức generate tương ứng với provider.
        """
        if self.provider == "google":
            return self._gen_google(messages)      # gọi Google Gemini SDK
        else:
            return self._gen_openrouter(messages)  # gọi HTTP OpenRouter

    def _gen_google(self, messages: List[str]) -> str:
        """
        Gửi yêu cầu tới Google Gemini thông qua SDK.
        - messages: list các chuỗi nội dung (prompt)
        - Trả về văn bản kết quả từ resp.text
        """
        prompt = "\n".join(messages)  # ghép các message thành 1 chuỗi prompt duy nhất
        try:
            resp = self.client.generate_content(prompt)  # gọi API
            return resp.text                              # trả về nội dung text
        except Exception as e:
            logger.error(f"❌ Lỗi Google Gemini API: {e}")  # log lỗi nếu có
            raise                                       # ném ngoại lệ lên trên

    def _gen_openrouter(self, messages: List[str]) -> str:
        """
        Gửi yêu cầu tới OpenRouter qua HTTP POST.
        - Chuyển messages thành định dạng chat: hệ thống + người dùng
        - Tham số điều chỉnh: temperature, max_tokens
        - Trả về nội dung text từ response JSON
        """
        # Định dạng messages cho OpenRouter: role "system" cho phần đầu, "user" cho các phần sau
        formatted = [
            {"role": "system" if i == 0 else "user", "content": m}
            for i, m in enumerate(messages)
        ]

        # Thiết lập payload JSON theo API spec của OpenRouter
        payload = {
            "model": self.model,               # model muốn dùng
            "messages": formatted,             # danh sách message đã format
            "temperature": 0.1,                # mức độ sáng tạo (thấp = ổn định)
            "max_tokens": 2000,                # số token tối đa trả về
        }

        # Header chứa API key và content type
        headers = {
            "Authorization": f"Bearer {self.api_key}",  
            "Content-Type": "application/json",
        }

        try:
            # Gửi POST request, timeout 30s
            res = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            res.raise_for_status()                     # ném lỗi nếu status code != 200
            data = res.json()                          # parse JSON từ response
            # Trả về nội dung message đầu tiên trong choices
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter API: {e}")  # log lỗi nếu có
            raise                                       # ném ngoại lệ lên trên
