# modules/llm_client.py
import os
import json
from typing import Dict, Any, Optional
import requests
from modules.config import LLM_CONFIG

class LLMClient:
    """Wrapper client để xử lý nhiều LLM providers"""
    
    def __init__(self):
        self.provider = LLM_CONFIG["provider"]
        self.model = LLM_CONFIG["model"]
        self.api_key = LLM_CONFIG["api_key"]
        
        if self.provider == "google":
            import google.generativeai as genai
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openrouter":
            self.client = None  # Sử dụng requests
        
    def generate_content(self, messages: list) -> str:
        """Tạo nội dung từ LLM với prompt"""
        if self.provider == "google":
            return self._generate_google(messages)
        elif self.provider == "openrouter":
            return self._generate_openrouter(messages)
        else:
            raise ValueError(f"Provider không được hỗ trợ: {self.provider}")
    
    def _generate_google(self, messages: list) -> str:
        """Gọi Google Gemini API"""
        try:
            # Nối các messages thành một prompt
            prompt = "\n".join(str(msg) for msg in messages)
            response = self.client.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Lỗi Google Gemini API: {e}")
    
    def _generate_openrouter(self, messages: list) -> str:
        """Gọi OpenRouter API"""
        try:
            # Chuyển đổi messages sang format OpenAI
            formatted_messages = []
            for i, msg in enumerate(messages):
                if i == 0:
                    formatted_messages.append({"role": "system", "content": str(msg)})
                else:
                    formatted_messages.append({"role": "user", "content": str(msg)})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/HoanCauAI",  # Thay đổi theo repo của bạn
                "X-Title": "HoanCauAI CV Processor"
            }
            
            data = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API lỗi {response.status_code}: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise Exception(f"Lỗi OpenRouter API: {e}")
