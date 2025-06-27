"""Chat tab utilities extracted from app.py."""

import logging
from pathlib import Path
from datetime import datetime
from io import BytesIO

try:
    from audiorecorder import audiorecorder
except Exception:  # pragma: no cover - fallback if dependency missing
    audiorecorder = None
import speech_recognition as sr
from gtts import gTTS

import pandas as pd
import streamlit as st

from modules.config import OUTPUT_CSV
from modules.ui_utils import loading_logs
from .utils import handle_error, safe_session_state_get

logger = logging.getLogger(__name__)


@handle_error
def load_dataset_for_chat():
    """Load CV dataset for chat context."""
    try:
        csv_path = Path(OUTPUT_CSV)
        if not csv_path.exists():
            return None
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if df.empty:
            return None
        modified_time = datetime.fromtimestamp(csv_path.stat().st_mtime)
        return {
            "count": len(df),
            "file": csv_path.name,
            "modified": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": df,
        }
    except Exception as e:
        logger.error("Error loading dataset for chat: %s", e)
        return None


@handle_error
def render_chat_statistics():
    """Render chat statistics."""
    if not st.session_state.get("show_chat_stats", False):
        return
    history = st.session_state.get("conversation_history", [])
    if not history:
        st.info("Chưa có cuộc trò chuyện nào.")
        return
    with st.expander("📊 Thống kê chi tiết", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tổng tin nhắn", len(history))
        with col2:
            user_messages = len([msg for msg in history if msg["role"] == "user"])
            st.metric("Tin nhắn của bạn", user_messages)
        with col3:
            ai_messages = len([msg for msg in history if msg["role"] == "assistant"])
            st.metric("Phản hồi AI", ai_messages)
        with col4:
            if history:
                first_message = history[0].get("timestamp", "N/A")
                st.metric("Bắt đầu lúc", first_message[:19] if first_message != "N/A" else "N/A")


@handle_error
def render_chat_history():
    """Render chat conversation history."""
    history = st.session_state.get("conversation_history", [])
    if not history:
        st.info("💬 Bắt đầu cuộc trò chuyện bằng cách gửi tin nhắn bên dưới!")
        return
    for message in history:
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        if role == "user":
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                    <div class="chat-message" style="
                        background: linear-gradient(135deg, {st.session_state.get('accent_color', '#d4af37')} 0%, {st.session_state.get('secondary_color', '#ffeacc')} 100%);
                        color: white;
                        margin-left: 20%;
                    ">
                        <strong>👤 Bạn:</strong><br>
                        {content}
                        <div style="font-size: 0.8em; opacity: 0.8; margin-top:5px;">
                            {timestamp[:19] if timestamp else ''}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin:10px 0;">
                    <div class="chat-message" style="
                        background: linear-gradient(135deg, {st.session_state.get('background_color', '#fff7e6')} 0%, {st.session_state.get('secondary_color', '#ffeacc')}44 100%);
                        color: {st.session_state.get('text_color', '#222222')};
                        border: 2px solid {st.session_state.get('secondary_color', '#ffeacc')};
                        margin-right: 20%;
                    ">
                        <strong>🤖 AI:</strong><br>
                        {content}
                        <div style="font-size: 0.8em; opacity: 0.7; margin-top:5px;">
                            {timestamp[:19] if timestamp else ''}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


@handle_error
def render_chat_input_form():
    """Render chat input form."""
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_area(
                "💬 Nhập câu hỏi của bạn:",
                placeholder="Ví dụ: Tóm tắt thông tin các ứng viên có kinh nghiệm AI...",
                height=100,
                help="Nhấn Ctrl+Enter để gửi nhanh",
            )
            audio = audiorecorder("🎤 Bấm để thu âm", "⏹ Dừng") if audiorecorder else None
            if not audiorecorder:
                st.warning(
                    "Không tìm thấy thành phần ghi âm. Hãy kiểm tra cài đặt hoặc tải file âm thanh."
                )
            audio_file = st.file_uploader(
                "🎵 Hoặc tải lên file âm thanh", type=["wav", "mp3"], label_visibility="collapsed"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(
                "📨 Gửi",
                help="Gửi câu hỏi cho AI",
                use_container_width=True,
            )

    if audio and len(audio.raw_data) > 0:
        wav_bytes = BytesIO()
        audio.export(wav_bytes, format="wav")
        wav_bytes.seek(0)
        st.audio(wav_bytes.read(), format="audio/wav")
        wav_bytes.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_bytes) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="vi-VN")
            st.info(f"Bạn nói: {text}")
            process_chat_message(text)
        except Exception as e:
            st.error(f"Không nhận dạng được giọng nói: {e}")
    elif audio_file is not None:
        file_bytes = BytesIO(audio_file.read())
        file_bytes.seek(0)
        st.audio(
            file_bytes.read(),
            format="audio/wav" if audio_file.type == "audio/wav" else "audio/mp3",
        )
        file_bytes.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_bytes) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="vi-VN")
            st.info(f"Bạn nói: {text}")
            process_chat_message(text)
        except Exception as e:
            st.error(f"Không nhận dạng được giọng nói: {e}")

    if submit_button and user_input.strip():
        process_chat_message(user_input.strip())


@handle_error
def process_chat_message(user_input: str):
    """Process chat message and get AI response."""
    try:
        timestamp = datetime.now().isoformat()
        st.session_state.setdefault("conversation_history", []).append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp,
        })
        with loading_logs("🤖 AI đang suy nghĩ..."):
            from modules.qa_chatbot import QAChatbot
            provider = st.session_state.get("selected_provider", "google")
            model = st.session_state.get("selected_model", "gemini-2.5-flash-lite-preview-06-17")
            api_key = st.session_state.get(f"{provider}_api_key", "")
            if not api_key:
                st.error("❌ API Key chưa được cấu hình!")
                return
            dataset_info = load_dataset_for_chat()
            if not dataset_info or dataset_info.get("data") is None:
                st.error("❌ Chưa có dataset CV để chat. Hãy xử lý CV trước.")
                return
            df = dataset_info["data"]
            chatbot = QAChatbot(provider=provider, model=model, api_key=api_key)
            conversation_context = []
            recent_history = st.session_state.get("conversation_history", [])[-10:]
            for msg in recent_history[:-1]:
                conversation_context.append({"role": msg["role"], "content": msg["content"]})
            context = {"history": conversation_context} if conversation_context else None
            response = chatbot.ask_question(user_input, df, context=context)
            if response:
                st.session_state.setdefault("conversation_history", []).append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                })
                try:
                    audio_fp = BytesIO()
                    gTTS(text=response, lang="vi").write_to_fp(audio_fp)
                    audio_fp.seek(0)
                    st.audio(audio_fp.read(), format="audio/mp3")
                except Exception as e:
                    logger.error("TTS error: %s", e)
                logger.info(
                    "Chat processed successfully. History length: %s",
                    len(st.session_state.get("conversation_history", [])),
                )
                st.rerun()
            else:
                st.error("❌ Không thể lấy phản hồi từ AI. Vui lòng thử lại.")
    except Exception as e:
        st.error(f"❌ Lỗi xử lý chat: {e}")
        logger.error("Chat processing error: %s", e)


@handle_error
def export_chat_history() -> str | None:
    """Return chat history as Markdown for download."""
    try:
        history = st.session_state.get("conversation_history", [])
        if not history:
            return None
        export_content = "# Lịch sử Chat - Hoàn Cầu AI CV Processor\n\n"
        export_content += f"Xuất lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_content += f"Tổng số tin nhắn: {len(history)}\n\n"
        export_content += "---\n\n"
        for i, message in enumerate(history, 1):
            role = "👤 Bạn" if message["role"] == "user" else "🤖 AI"
            timestamp = message.get("timestamp", "")[:19]
            content = message.get("content", "")
            export_content += f"## Tin nhắn {i} - {role}\n"
            export_content += f"**Thời gian:** {timestamp}\n\n"
            export_content += f"{content}\n\n"
            export_content += "---\n\n"
        return export_content
    except Exception as e:
        st.error(f"❌ Lỗi xuất file: {e}")
        logger.error("Export error: %s", e)
        return None


@handle_error
def render_chat_help():
    """Render suggested prompts for the chat."""
    with st.expander("❓ Hướng dẫn sử dụng Chat AI", expanded=True):
        st.markdown(
            """
            ### 📋 Prompt gợi ý
            - "Tóm tắt kinh nghiệm 5 ứng viên hàng đầu cho vị trí Data Scientist"
            - "Liệt kê những ứng viên có trên 3 năm kinh nghiệm Python"
            - "So sánh kỹ năng giữa ứng viên A và B"
            - "Phân tích điểm mạnh của từng ứng viên"
            - "Gợi ý ứng viên phù hợp cho vị trí Machine Learning Engineer"
            - "Tạo email mời phỏng vấn ứng viên xuất sắc nhất"
            """
        )
        if st.button("Đóng hướng dẫn", key="close_chat_help"):
            st.session_state["show_chat_help"] = False
            st.rerun()


@handle_error
def render_enhanced_chat_tab():
    """Render enhanced chat tab with full functionality."""
    st.header("🤖 Chat với AI - Trợ lý thông minh")
    if "conversation_history" not in st.session_state:
        st.session_state["conversation_history"] = []
    if "show_chat_help" not in st.session_state:
        st.session_state["show_chat_help"] = False
    dataset_info = load_dataset_for_chat()
    if dataset_info:
        with st.expander("📊 Thông tin dataset hiện tại", expanded=False):
            st.success(f"✅ Đã tải {dataset_info['count']} CV từ file: `{dataset_info['file']}`")
            st.info(f"📅 Last modified: {dataset_info['modified']}")
    else:
        st.warning("⚠️ Chưa có dataset CV. Hãy xử lý CV ở tab 'Xử lý CV' trước.")
    render_chat_statistics()
    chat_container = st.container()
    with chat_container:
        render_chat_history()
    render_chat_input_form()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        export_data = export_chat_history()
        if export_data:
            st.download_button(
                label="📥 Xuất chat",
                data=export_data,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                help="Tải xuống lịch sử chat",
                use_container_width=True,
            )
        else:
            st.button(
                "📥 Xuất chat",
                disabled=True,
                help="Không có lịch sử chat để xuất",
                use_container_width=True,
            )
    with col2:
        if st.button("🗑️ Xóa lịch sử", help="Xóa toàn bộ lịch sử chat"):
            st.session_state["conversation_history"] = []
            st.success("Đã xóa lịch sử chat!")
            st.rerun()
    with col3:
        if st.button("📊 Thống kê", help="Xem thống kê chi tiết"):
            st.session_state["show_chat_stats"] = not st.session_state.get("show_chat_stats", False)
            st.rerun()
    with col4:
        if st.button("❓ Hướng dẫn", help="Xem hướng dẫn sử dụng"):
            st.session_state["show_chat_help"] = not st.session_state["show_chat_help"]
    if st.session_state["show_chat_help"]:
        render_chat_help()

__all__ = [
    "render_enhanced_chat_tab",
    "load_dataset_for_chat",
    "render_chat_statistics",
    "render_chat_history",
    "render_chat_input_form",
    "process_chat_message",
    "export_chat_history",
    "render_chat_help",
]
