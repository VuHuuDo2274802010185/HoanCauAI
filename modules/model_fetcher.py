# modules/model_fetcher.py
import requests
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ModelFetcher:
    """Class để fetch danh sách models từ các API providers"""
    
    @staticmethod
    def get_google_models(api_key: str) -> List[str]:
        """Lấy danh sách models từ Google Gemini API"""
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            
            model_names = []
            for model in models:
                # Chỉ lấy generative models, bỏ qua embedding models
                if 'generate' in model.supported_generation_methods:
                    # Lấy tên model từ model.name (vd: "models/gemini-pro" -> "gemini-pro")
                    model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                    model_names.append(model_name)
            
            return sorted(model_names)
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy Google models: {e}")
            # Fallback models nếu API call thất bại
            return [
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest", 
                "gemini-1.5-pro",
                "gemini-1.5-pro-latest",
                "gemini-pro",
                "gemini-pro-vision"
            ]
    
    @staticmethod
    def get_openrouter_models(api_key: str) -> List[Dict]:
        """Lấy danh sách models từ OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/HoanCauAI",
                "X-Title": "HoanCauAI CV Processor"
            }
            
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model in data.get('data', []):
                    models.append({
                        'id': model.get('id', ''),
                        'name': model.get('name', ''),
                        'description': model.get('description', ''),
                        'pricing': model.get('pricing', {}),
                        'context_length': model.get('context_length', 0),
                        'architecture': model.get('architecture', {})
                    })
                
                # Sắp xếp theo tên
                return sorted(models, key=lambda x: x['id'])
            else:
                logger.error(f"OpenRouter API lỗi {response.status_code}: {response.text}")
                return ModelFetcher._get_fallback_openrouter_models()
                
        except Exception as e:
            logger.error(f"Lỗi khi lấy OpenRouter models: {e}")
            return ModelFetcher._get_fallback_openrouter_models()
    
    @staticmethod
    def _get_fallback_openrouter_models() -> List[Dict]:
        """Fallback models nếu OpenRouter API thất bại"""
        return [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "description": "Most capable model"},
            {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "description": "Fast and efficient"},
            {"id": "openai/gpt-4o", "name": "GPT-4 Omni", "description": "Latest GPT-4 model"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4 Omni Mini", "description": "Smaller GPT-4 model"},
            {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and affordable"},
            {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5", "description": "Google's latest model"},
            {"id": "google/gemini-flash-1.5", "name": "Gemini Flash 1.5", "description": "Fast Gemini model"},
            {"id": "meta-llama/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "description": "Small Llama model"},
            {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "description": "Large Llama model"},
            {"id": "qwen/qwen-2.5-72b-instruct", "name": "Qwen 2.5 72B", "description": "Alibaba's model"}
        ]
    
    @staticmethod
    def get_simple_openrouter_model_ids(api_key: str) -> List[str]:
        """Lấy chỉ danh sách ID models từ OpenRouter"""
        models = ModelFetcher.get_openrouter_models(api_key)
        return [model['id'] for model in models]
