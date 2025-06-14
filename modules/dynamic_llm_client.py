# modules/dynamic_llm_client.py

import os
from typing import List, Dict
import requests
import streamlit as st
import logging

from .config import LLM_CONFIG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class DynamicLLMClient:
    """
    Client LLM động dùng trong Streamlit.
    Chọn provider/model từ session_state, tự cấu hình API key.
    """

    def __init__(self,
                 provider: str = None,
                 model: str = None,
                 api_key: str = None):
        self.provider = provider or st.session_state.get("selected_provider", LLM_CONFIG["provider"])
        self.model = model or st.session_state.get("selected_model", LLM_CONFIG["model"])
        self.api_key = api_key or LLM_CONFIG.get("api_key", "")
        self._setup()

    def _setup(self):
        if self.provider == "google":
            import google.generativeai as genai
            if not self.api_key:
                raise ValueError("Google API key không có sẵn")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openrouter":
            if not self.api_key:
                raise ValueError("OpenRouter API key không có sẵn")
            self.client = None  # we'll use requests
        else:
            raise ValueError(f"Provider không hỗ trợ: {self.provider}")

    def generate_content(self, messages: List[str]) -> str:
        if self.provider == "google":
            return self._gen_google(messages)
        else:
            return self._gen_openrouter(messages)

    def _gen_google(self, messages: List[str]) -> str:
        prompt = "\n".join(messages)
        try:
            resp = self.client.generate_content(prompt)
            return resp.text
        except Exception as e:
            logger.error(f"❌ Lỗi Google Gemini API: {e}")
            raise

    def _gen_openrouter(self, messages: List[str]) -> str:
        formatted = []
        for i, m in enumerate(messages):
            role = "system" if i == 0 else "user"
            formatted.append({"role": role, "content": m})
        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload, headers=headers, timeout=30
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Lỗi OpenRouter API: {e}")
            raise
