# modules/dynamic_llm_client.py

import requests  # thư viện HTTP để tương tác với API OpenRouter
import streamlit as st  # lấy thông tin session_state trong Streamlit
import logging  # ghi log xử lý
from typing import List  # định nghĩa kiểu cho danh sách

from .config import LLM_CONFIG, OPENROUTER_BASE_URL  # cấu hình chung LLM và URL

# --- Thiết lập logger cho module dynamic_llm_client ---
logger = logging.getLogger(__name__)  # lấy logger theo tên module
logger.setLevel(logging.INFO)  # mức log tối thiểu INFO
logger.addHandler(logging.StreamHandler())  # xuất log ra console

def _streamlit_ctx_exists() -> bool:
    """Kiểm tra có đang chạy trong context Streamlit không."""
    try:
        return bool(st.runtime.exists())
    except Exception:
        try:
            return (
                st.runtime.scriptrunner.get_script_run_ctx(
                    suppress_warning=True
                )
                is not None
            )
        except Exception:
            return False

class DynamicLLMClient:
    """
    Client LLM động cho giao diện Streamlit.
    - Lấy provider và model từ ``st.session_state`` nếu có context,
      ngược lại dùng ``LLM_CONFIG``.
    - Tự cấu hình API key và client phù hợp.
    """
    def __init__(self,
                 provider: str = None,
                 model: str = None,
                 api_key: str = None):
        ctx = _streamlit_ctx_exists()
        # Chọn provider: ưu tiên tham số, sau đó session_state, cuối cùng LLM_CONFIG
        self.provider = provider or (
            st.session_state.get("selected_provider") if ctx else None
        ) or LLM_CONFIG["provider"]
        # Chọn model: ưu tiên tham số, sau đó session_state, cuối cùng LLM_CONFIG
        self.model = model or (
            st.session_state.get("selected_model") if ctx else None
        ) or LLM_CONFIG["model"]
        # Lấy api_key: ưu tiên tham số, sau đó session_state, cuối cùng config
        if ctx:
            session_key = (
                st.session_state.get("google_api_key")
                if self.provider == "google"
                else st.session_state.get("openrouter_api_key")
            )
        else:
            session_key = None
        self.api_key = api_key or session_key or LLM_CONFIG.get("api_key", "")
        # Thiết lập client theo provider đã chọn
        self._setup()

    def _setup(self):
        """
        Enhanced setup with better error handling and validation
        """
        try:
            if self.provider == "google":
                # Enhanced Google setup
                import google.generativeai as genai
                if not self.api_key:
                    raise ValueError("Google API key không có sẵn")
                
                # Configure with retry and timeout
                genai.configure(api_key=self.api_key)
                
                # Validate API key by listing models
                try:
                    models = list(genai.list_models())
                    logger.info(f"Google API key validated. Available models: {len(models)}")
                except Exception as e:
                    logger.warning(f"Could not validate Google API key: {e}")
                
                # Create client with safety settings
                self.client = genai.GenerativeModel(
                    self.model,
                    safety_settings={
                        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                    }
                )

            elif self.provider == "openrouter":
                # Enhanced OpenRouter setup
                if not self.api_key:
                    raise ValueError("OpenRouter API key không có sẵn")
                
                # Validate API key
                try:
                    response = requests.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info("OpenRouter API key validated successfully")
                    else:
                        logger.warning(f"OpenRouter API key validation returned status: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Could not validate OpenRouter API key: {e}")
                
                self.client = None  # Will use direct HTTP requests
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            logger.info(f"LLM client setup completed: {self.provider}/{self.model}")
            
        except Exception as e:
            logger.error(f"Failed to setup LLM client: {e}")
            raise

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
            raise  # propagate the exception to the caller

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
            url = f"{OPENROUTER_BASE_URL}/chat/completions"
            res = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            # Kiểm tra Unauthorized
            if res.status_code == 401:
                logger.error("OpenRouter API Unauthorized: check API key")
                raise ValueError("OpenRouter API Unauthorized: Vui lòng kiểm tra API key.")
            res.raise_for_status()                     # ném lỗi nếu status code != 200
            data = res.json()                          # parse JSON từ response
            # Trả về nội dung message đầu tiên trong choices
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter API: {e}")  # log lỗi nếu có
            raise  # propagate the exception to the caller
