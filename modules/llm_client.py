# modules/llm_client.py

import os
import json
import logging
import requests
from typing import List

from .config import LLM_CONFIG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class LLMClient:
    """
    Client LLM đồng nhất cho mọi script backend.
    Dùng LLM_CONFIG từ config.py
    """

    def __init__(self):
        self.provider = LLM_CONFIG["provider"]
        self.model = LLM_CONFIG["model"]
        self.api_key = LLM_CONFIG["api_key"]
        if self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openrouter":
            self.client = None
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
        formatted = [{"role": "system" if i==0 else "user", "content": m}
                     for i, m in enumerate(messages)]
        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
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
