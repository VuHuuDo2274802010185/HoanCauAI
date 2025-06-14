# modules/model_fetcher.py

import os
import json
import logging
from typing import List, Dict
import google.generativeai as genai
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class ModelFetcher:
    """Fetch danh sách models từ Google & OpenRouter, có fallback."""

    CACHE_DIR = os.path.expanduser("~/.hoancauai_cache")
    os.makedirs(CACHE_DIR, exist_ok=True)

    @staticmethod
    def _cache_path(provider: str) -> str:
        return os.path.join(ModelFetcher.CACHE_DIR, f"{provider}_models.json")

    @staticmethod
    def _load_cache(provider: str) -> List:
        path = ModelFetcher._cache_path(provider)
        if os.path.exists(path):
            try:
                return json.load(open(path, "r"))
            except:
                pass
        return []

    @staticmethod
    def _save_cache(provider: str, data: List):
        path = ModelFetcher._cache_path(provider)
        try:
            json.dump(data, open(path, "w"), indent=2)
        except:
            pass

    @staticmethod
    def get_google_models(api_key: str) -> List[str]:
        """List Google Gemini models, cache kết quả."""
        cached = ModelFetcher._load_cache("google")
        if cached:
            return cached
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            names = [
                m.name.split("/")[-1]
                for m in models
                if "generate" in getattr(m, "supported_generation_methods", [])
            ]
            names = sorted(names)
            ModelFetcher._save_cache("google", names)
            return names
        except Exception as e:
            logger.error(f"❌ Lỗi Google list_models: {e}")
        # fallback cứng
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
        """List OpenRouter models, cache kết quả."""
        cached = ModelFetcher._load_cache("openrouter")
        if cached:
            return cached
        try:
            res = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            res.raise_for_status()
            data = res.json().get("data", [])
            models = sorted(data, key=lambda x: x.get("id", ""))
            ModelFetcher._save_cache("openrouter", models)
            return models
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter list_models: {e}")
        # fallback cứng
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
        """Chỉ lấy id models từ OpenRouter."""
        models = ModelFetcher.get_openrouter_models(api_key)
        return [m.get("id", "") for m in models]
