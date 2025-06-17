# modules/model_fetcher.py

import os                      # thư viện xử lý đường dẫn và tương tác hệ thống file
import json                    # parse và dump dữ liệu JSON
import logging                 # ghi log
from typing import List, Dict # khai báo kiểu List, Dict cho hàm/method
import google.generativeai as genai  # SDK Google Gemini để list models
import requests                # gửi HTTP request (OpenRouter API)

# --- Cấu hình logger cho module ---
logger = logging.getLogger(__name__)       # lấy logger theo tên module hiện tại
logger.setLevel(logging.INFO)              # chỉ ghi log mức INFO trở lên
logger.addHandler(logging.StreamHandler()) # xuất log ra console

class ModelFetcher:
    """
    Fetch danh sách models từ Google & OpenRouter, có cơ chế cache và fallback.
    """

    # Thư mục cache lưu file JSON kết quả list_models
    CACHE_DIR = os.path.expanduser("~/.hoancauai_cache")
    os.makedirs(CACHE_DIR, exist_ok=True)  # tạo thư mục nếu chưa tồn tại

    @staticmethod
    def _cache_path(provider: str) -> str:
        """
        Trả về đường dẫn file cache cho provider (google hoặc openrouter).
        """
        return os.path.join(ModelFetcher.CACHE_DIR, f"{provider}_models.json")

    @staticmethod
    def _load_cache(provider: str) -> List:
        """
        Đọc cache từ file, trả về list nếu có.
        Trả về [] nếu file không tồn tại hoặc lỗi parse.
        """
        path = ModelFetcher._cache_path(provider)
        if os.path.exists(path):
            try:
                return json.load(open(path, "r", encoding="utf-8"))
            except Exception:
                pass
        return []

    @staticmethod
    def _save_cache(provider: str, data: List):
        """
        Ghi dữ liệu danh sách models vào file cache dạng JSON.
        """
        path = ModelFetcher._cache_path(provider)
        try:
            json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
        except Exception:
            pass

    @staticmethod
    def get_google_models(api_key: str) -> List[str]:
        """
        Lấy danh sách model từ Google Gemini qua SDK.
        - Kiểm tra cache trước, nếu có dùng luôn.
        - Nếu không, gọi genai.list_models(), lấy tất cả tên models.
        - Lưu kết quả vào cache và trả về.
        - Nếu lỗi, log và fallback về list cứng.
        """
        # thử load từ cache trước
        cached = ModelFetcher._load_cache("google")
        if cached:
            return cached

        try:
            genai.configure(api_key=api_key)           # cấu hình API key cho SDK
            models = genai.list_models()               # gọi list_models()
            # lấy tất cả tên model
            names = [
                m.name.split("/")[-1]
                for m in models
            ]
            names = sorted(names)                      # sắp xếp alphabet
            ModelFetcher._save_cache("google", names)  # lưu cache
            return names
        except Exception as e:
            logger.error(f"❌ Lỗi Google list_models: {e}")

        # fallback cứng nếu không lấy được từ API
        return [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-pro",
            "gemini-pro-vision",
        ]

    @staticmethod
    def get_openrouter_models(api_key: str) -> List[Dict]:
        """
        Lấy danh sách model từ OpenRouter qua HTTP GET.
        - Kiểm tra cache trước, nếu có dùng luôn.
        - Nếu không, gọi API, parse JSON->data, sort theo id.
        - Lưu cache và trả về list dict.
        - Nếu lỗi, log và fallback về list cứng.
        """
        cached = ModelFetcher._load_cache("openrouter")
        if cached:
            return cached

        try:
            res = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            res.raise_for_status()                     # ném lỗi nếu status != 200
            data = res.json().get("data", [])          # lấy trường data
            # sắp xếp list dict theo key 'id'
            models = sorted(data, key=lambda x: x.get("id", ""))
            ModelFetcher._save_cache("openrouter", models)
            return models
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter list_models: {e}")

        # fallback cứng nếu không lấy được
        return [
            {"id": "anthropic/claude-3.5-sonnet"},
            {"id": "anthropic/claude-3-haiku"},
            {"id": "openai/gpt-4o"},
            {"id": "openai/gpt-4o-mini"},
            {"id": "openai/gpt-3.5-turbo"},
            {"id": "google/gemini-pro-1.5"},
            {"id": "google/gemini-flash-1.5"},
            {"id": "meta-llama/llama-3.1-8b-instruct"},
            {"id": "meta-llama/llama-3.1-70b-instruct"},
            {"id": "qwen/qwen-2.5-72b-instruct"},
        ]

    @staticmethod
    def get_simple_openrouter_model_ids(api_key: str) -> List[str]:
        """
        Trả về chỉ danh sách id của models OpenRouter.
        Sử dụng get_openrouter_models() rồi lấy trường 'id'.
        """
        models = ModelFetcher.get_openrouter_models(api_key)
        return [m.get("id", "") for m in models]
