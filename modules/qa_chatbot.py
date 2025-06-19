import json
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
from .dynamic_llm_client import DynamicLLMClient
from .config import CHAT_LOG_FILE


def _log_chat(question: str, answer: str, log_file: Path = CHAT_LOG_FILE) -> None:
    """Append a Q&A pair to the chat log file in JSON format."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer,
    }
    try:
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Không thể ghi log chat: {e}")


def answer_question(question: str, df: pd.DataFrame, provider: str, model: str, api_key: str) -> str:
    """Trả lời câu hỏi dựa trên DataFrame CV."""
    if df is None or df.empty:
        raise ValueError("Dataset trống")

    preview = df.to_csv(index=False)
    messages = [
        "Bạn là trợ lý AI phân tích dữ liệu CV từ file CSV.",
        "Dưới đây là toàn bộ dữ liệu:\n" + preview,
        f"Câu hỏi: {question}"
    ]
    client = DynamicLLMClient(provider=provider, model=model, api_key=api_key)
    answer = client.generate_content(messages)
    _log_chat(question, answer)
    return answer

