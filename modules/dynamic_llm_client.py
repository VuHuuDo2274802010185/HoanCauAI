# modules/dynamic_llm_client.py
import os
import json
from typing import Dict, Any, Optional
import requests
import streamlit as st

class DynamicLLMClient:
    """Dynamic LLM client có thể thay đổi provider và model runtime"""
    
    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        self.provider = provider or st.session_state.get('selected_provider', 'google')
        self.model = model or st.session_state.get('selected_model', 'gemini-1.5-flash-latest')
        
        # Lấy API key tự động
        if not api_key:
            if self.provider == "google":
                self.api_key = os.getenv("GOOGLE_API_KEY", "")
            elif self.provider == "openrouter":
                self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        else:
            self.api_key = api_key
        
        self._setup_client()
    
    def _setup_client(self):
        """Setup client dựa trên provider"""
        if self.provider == "google":
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
            else:
                raise ValueError("Google API key không có sẵn")
        elif self.provider == "openrouter":
            self.client = None  # Sử dụng requests
            if not self.api_key:
                raise ValueError("OpenRouter API key không có sẵn")
        else:
            raise ValueError(f"Provider không được hỗ trợ: {self.provider}")
    
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
                "HTTP-Referer": "https://github.com/your-username/HoanCauAI",
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
    
    def get_model_info(self) -> Dict[str, str]:
        """Lấy thông tin về model hiện tại"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key_available": bool(self.api_key)
        }
