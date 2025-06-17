import pandas as pd
from .dynamic_llm_client import DynamicLLMClient


def answer_question(question: str, df: pd.DataFrame, provider: str, model: str, api_key: str) -> str:
    """Trả lời câu hỏi dựa trên DataFrame CV."""
    if df is None or df.empty:
        raise ValueError("Dataset trống")

    preview = df.head(20).to_csv(index=False)
    messages = [
        "Bạn là trợ lý AI phân tích dữ liệu CV từ file CSV.",
        "Dưới đây là 20 dòng đầu tiên của dữ liệu:\n" + preview,
        f"Câu hỏi: {question}"
    ]
    client = DynamicLLMClient(provider=provider, model=model, api_key=api_key)
    return client.generate_content(messages)

