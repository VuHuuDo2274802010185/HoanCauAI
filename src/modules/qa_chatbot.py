"""Hỗ trợ hỏi đáp dữ liệu CV bằng API LLM."""

import json
import logging
import re
from datetime import datetime, timezone
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from .dynamic_llm_client import DynamicLLMClient
from .config import CHAT_LOG_FILE, ATTACHMENT_DIR
import base64


class QAChatbot:
    """Simple wrapper around :func:`answer_question`."""

    def __init__(self, provider: str, model: str, api_key: str) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def ask_question(
        self,
        question: str,
        df: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Delegate answering to :func:`answer_question`."""
        return answer_question(
            question,
            df,
            self.provider,
            self.model,
            self.api_key,
            context=context,
        )

# Enhanced logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _make_file_link(fname: str) -> str:
    """Return an HTML download link for a CV file if it exists."""
    path = (ATTACHMENT_DIR / fname).resolve()
    if not path.exists():
        return fname
    data = base64.b64encode(path.read_bytes()).decode()
    mime = (
        "application/pdf"
        if path.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return f'<a download="{fname}" href="data:{mime};base64,{data}">{fname}</a>'


def _log_chat(question: str, answer: str, log_file: Path = CHAT_LOG_FILE) -> None:
    """Append a Q&A pair to the chat log file in JSON format with enhanced metadata."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "question_length": len(question),
        "answer_length": len(answer),
        "question_type": _classify_question(question)
    }
    try:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Chat log corrupted, recreating")
                data = []
        else:
            data = []
            
        data.append(entry)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(data) > 1000:
            data = data[-800:]  # Keep last 800 entries
            
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Chat logged: Q-type={entry['question_type']}, Q-len={entry['question_length']}, A-len={entry['answer_length']}")
    except Exception as e:
        logger.warning(f"Không thể ghi log chat: {e}")


def _classify_question(question: str) -> str:
    """Classify question type for better analytics."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["tìm", "kiếm", "search", "find"]):
        return "search"
    elif any(word in question_lower for word in ["thống kê", "stats", "count", "số lượng"]):
        return "statistics"
    elif any(word in question_lower for word in ["so sánh", "compare", "khác nhau"]):
        return "comparison"
    elif any(word in question_lower for word in ["tóm tắt", "summary", "overview"]):
        return "summary"
    elif any(word in question_lower for word in ["kỹ năng", "skill", "năng lực"]):
        return "skills"
    elif any(word in question_lower for word in ["kinh nghiệm", "experience", "công việc"]):
        return "experience"
    elif any(word in question_lower for word in ["học vấn", "education", "bằng cấp"]):
        return "education"
    else:
        return "general"


def _is_time_question(question: str) -> bool:
    """Detect if the user is asking about current time or date."""
    question_lower = question.lower()
    patterns = [
        r"bây giờ", r"mấy giờ", r"thời gian hiện tại", r"current time",
        r"current date", r"ngày bao nhiêu", r"hôm nay" 
    ]
    return any(re.search(p, question_lower) for p in patterns)


def _create_enhanced_prompt(question: str, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> list:
    """Create enhanced prompt with better context and instructions."""
    
    # Get data summary
    total_records = len(df)
    columns = list(df.columns)
    
    # Sample data for context
    
    # Create enhanced system prompt
    system_prompt = f"""Bạn là Trợ lý AI chuyên nghiệp phân tích dữ liệu CV và tuyển dụng.

THÔNG TIN DỮ LIỆU:
- Tổng số hồ sơ: {total_records}
- Các trường dữ liệu: {', '.join(columns)}

NHIỆM VỤ:
- Phân tích và trả lời câu hỏi dựa trên dữ liệu CV
- Cung cấp thông tin chính xác, chi tiết và hữu ích
- Sử dụng định dạng markdown khi cần thiết
- Đưa ra số liệu cụ thể khi có thể

QUY TẮC:
- Luôn trả lời bằng tiếng Việt
- Nếu không tìm thấy thông tin, hãy nói rõ
- Cung cấp gợi ý khi phù hợp
- Sử dụng emoji để làm cho câu trả lời sinh động hơn"""
    
    # Data context - use entire dataset instead of a preview
    data_context = f"Toàn bộ dữ liệu ({total_records} hồ sơ):\n\n{df.to_csv(index=False)}"
    
    # Question with context
    question_with_context = f"Câu hỏi: {question}"
    
    if context:
        question_with_context += f"\n\nThông tin bổ sung: {context}"
    
    return [system_prompt, data_context, question_with_context]


def answer_question(question: str, df: pd.DataFrame, provider: str, model: str, api_key: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Enhanced question answering with better error handling and context."""
    
    # Input validation
    if not question or not question.strip():
        raise ValueError("Câu hỏi không được để trống")
    
    if df is None or df.empty:
        raise ValueError("Dataset CV trống. Vui lòng xử lý CV trước khi sử dụng tính năng chat.")
    
    if not api_key or not api_key.strip():
        raise ValueError("API key không hợp lệ")
    
    question = question.strip()
    logger.info(f"Processing question: {question[:100]}... (Total records: {len(df)})")

    # Return system time immediately if asked
    if _is_time_question(question):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        answer = f"Bây giờ là {now}"
        _log_chat(question, answer)
        return answer
    
    try:
        # Create enhanced prompt
        messages = _create_enhanced_prompt(question, df, context)
        
        # Generate response
        client = DynamicLLMClient(provider=provider, model=model, api_key=api_key)
        answer = client.generate_content(messages)
        
        if not answer or not answer.strip():
            raise ValueError("AI không trả về kết quả")
        
        answer = answer.strip()
        
        # Post-process answer
        answer = _post_process_answer(answer)
        
        # Log the interaction
        _log_chat(question, answer)
        
        logger.info(f"Question answered successfully. Answer length: {len(answer)}")
        return answer
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        error_msg = f"Xin lỗi, tôi không thể trả lời câu hỏi này. Lỗi: {str(e)}"
        _log_chat(question, error_msg)
        return error_msg


def _post_process_answer(answer: str) -> str:
    """Post-process AI answer to improve formatting and readability."""
    
    # Clean up extra whitespace
    answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer)
    answer = answer.strip()
    
    # Add proper spacing around headers
    answer = re.sub(r'^(#{1,6})\s*(.+)', r'\1 \2', answer, flags=re.MULTILINE)
    
    # Ensure proper bullet point formatting
    answer = re.sub(r'^\s*[-*+]\s*', '• ', answer, flags=re.MULTILINE)

    # Add emoji if not present and answer is positive
    if not re.search(r'[😀-🙏]', answer) and len(answer) > 50:
        if any(word in answer.lower() for word in ['tìm thấy', 'có', 'thành công', 'được']):
            answer = "✅ " + answer
        elif any(word in answer.lower() for word in ['không', 'chưa', 'thiếu']):
            answer = "ℹ️ " + answer

    # Replace file names with download links
    file_pattern = re.compile(r'([\w\s.-]+\.(?:pdf|docx?))', re.IGNORECASE)

    def repl(match: re.Match) -> str:
        fname = match.group(1).strip()
        return _make_file_link(fname)

    answer = file_pattern.sub(repl, answer)

    return answer


def get_chat_statistics(log_file: Path = CHAT_LOG_FILE) -> Dict[str, Any]:
    """Get chat statistics from log file."""
    try:
        if not log_file.exists():
            return {"total_chats": 0, "question_types": {}, "average_lengths": {}}
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Chat log corrupted, ignoring statistics")
            return {"total_chats": 0, "question_types": {}, "average_lengths": {}}
        
        if not data:
            return {"total_chats": 0, "question_types": {}, "average_lengths": {}}
        
        # Calculate statistics
        total_chats = len(data)
        question_types = {}
        total_question_length = 0
        total_answer_length = 0
        
        for entry in data:
            q_type = entry.get("question_type", "general")
            question_types[q_type] = question_types.get(q_type, 0) + 1
            total_question_length += entry.get("question_length", 0)
            total_answer_length += entry.get("answer_length", 0)
        
        avg_question_length = total_question_length / total_chats if total_chats > 0 else 0
        avg_answer_length = total_answer_length / total_chats if total_chats > 0 else 0
        
        return {
            "total_chats": total_chats,
            "question_types": question_types,
            "average_lengths": {
                "question": round(avg_question_length, 1),
                "answer": round(avg_answer_length, 1)
            },
            "last_chat": data[-1]["timestamp"] if data else None
        }
        
    except Exception as e:
        logger.error(f"Error getting chat statistics: {e}")
        return {"total_chats": 0, "question_types": {}, "average_lengths": {}, "error": str(e)}

