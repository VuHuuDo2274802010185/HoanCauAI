from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from ..utils import (
    handle_error,
    safe_session_state_get,
    safe_session_state_set,
)
from modules.config import OUTPUT_CSV

logger = logging.getLogger(__name__)


@handle_error
def load_dataset_for_chat():
    """Load CV dataset for chat context."""
    try:
        csv_path = OUTPUT_CSV
        if not csv_path.exists():
            return None
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if df.empty:
            return None
        modified = datetime.fromtimestamp(csv_path.stat().st_mtime)
        return {
            "count": len(df),
            "file": csv_path.name,
            "modified": modified.strftime("%Y-%m-%d %H:%M:%S"),
            "data": df,
        }
    except Exception as e:  # pragma: no cover - runtime safety
        logger.error("Error loading dataset for chat: %s", e)
        return None


@handle_error
def render_chat_statistics() -> None:
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
            user_msgs = len([m for m in history if m.get("role") == "user"])
            st.metric("Tin nhắn của bạn", user_msgs)
        with col3:
            ai_msgs = len([m for m in history if m.get("role") == "assistant"])
            st.metric("Phản hồi AI", ai_msgs)
        with col4:
            if history:
                first = history[0].get("timestamp", "N/A")
                st.metric("Bắt đầu lúc", first[:19] if first != "N/A" else "N/A")


@handle_error
def render_chat_history() -> None:
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
                <div style='display:flex;justify-content:flex-end;margin:10px 0;'>
                    <div class='chat-message' style='background:linear-gradient(135deg,{st.session_state.get('accent_color','#d4af37')} 0%,{st.session_state.get('secondary_color','#f4e09c')} 100%);color:white;margin-left:20%;'>
                        <strong>👤 Bạn:</strong><br>{content}
                        <div style='font-size:0.8em;opacity:0.8;margin-top:5px;'>
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
                <div style='display:flex;justify-content:flex-start;margin:10px 0;'>
                    <div class='chat-message' style='background:linear-gradient(135deg,{st.session_state.get('background_color','#fffbf0')} 0%,{st.session_state.get('secondary_color','#f4e09c')}44 100%);color:{st.session_state.get('text_color','#000')};border:2px solid {st.session_state.get('secondary_color','#f4e09c')};margin-right:20%;'>
                        <strong>🤖 AI:</strong><br>{content}
                        <div style='font-size:0.8em;opacity:0.7;margin-top:5px;'>
                            {timestamp[:19] if timestamp else ''}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


@handle_error
def process_chat_message(user_input: str) -> None:
    try:
        timestamp = datetime.now().isoformat()
        st.session_state.conversation_history.append(
            {"role": "user", "content": user_input, "timestamp": timestamp}
        )
        with st.spinner("🤖 AI đang suy nghĩ..."):
            from modules.qa_chatbot import QAChatbot
            provider = st.session_state.get("selected_provider", "google")
            model = st.session_state.get("selected_model", "gemini-2.0-flash")
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
            context = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.conversation_history[-10:-1]
            ]
            response = chatbot.ask_question(
                user_input,
                df,
                context={"history": context} if context else None,
            )
            if response:
                st.session_state.conversation_history.append(
                    {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
                )
                st.rerun()
            else:
                st.error("❌ Không thể lấy phản hồi từ AI. Vui lòng thử lại.")
    except Exception as e:  # pragma: no cover - runtime safety
        logger.error("Unexpected chat error: %s", e)
        st.error(f"❌ Lỗi không mong muốn: {e}")


@handle_error
def render_chat_input_form() -> None:
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_area(
                "💬 Nhập câu hỏi của bạn:",
                placeholder="Ví dụ: Tóm tắt thông tin các ứng viên có kinh nghiệm AI...",
                height=100,
                help="Nhấn Ctrl+Enter để gửi nhanh",
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("📨 Gửi", use_container_width=True)
    if submit and user_input.strip():
        process_chat_message(user_input.strip())


@handle_error
def export_chat_history() -> None:
    history = st.session_state.get("conversation_history", [])
    if not history:
        st.warning("Không có lịch sử chat để xuất.")
        return
    content = "# Lịch sử Chat - Hoàn Cầu AI CV Processor\n\n"
    content += f"Xuất lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Tổng số tin nhắn: {len(history)}\n\n"
    content += "---\n\n"
    for i, message in enumerate(history, 1):
        role = "👤 Bạn" if message["role"] == "user" else "🤖 AI"
        ts = message.get("timestamp", "")[:19]
        text = message.get("content", "")
        content += f"## Tin nhắn {i} - {role}\n"
        content += f"**Thời gian:** {ts}\n\n{text}\n\n---\n\n"
    st.download_button(
        label="💾 Tải xuống lịch sử chat",
        data=content,
        file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )


@handle_error
def render_chat_help() -> None:
    with st.expander("❓ Hướng dẫn sử dụng Chat AI", expanded=True):
        st.markdown(
            """
        ### 🎯 Tính năng chính:
        - **Chat thông minh** với AI về dữ liệu CV
        - **Lưu lịch sử** cuộc trò chuyện tự động
        - **Xuất file** lịch sử chat
        - **Thống kê** chi tiết cuộc trò chuyện
        - **Giao diện đẹp** với theme tùy chỉnh

        ### 💡 Cách sử dụng:
        1. **Xử lý CV trước:** Hãy xử lý CV ở tab "Xử lý CV" để có dữ liệu
        2. **Đặt câu hỏi:** Nhập câu hỏi vào ô bên dưới
        3. **Gửi tin nhắn:** Nhấn "Gửi" hoặc Ctrl+Enter
        4. **Theo dõi lịch sử:** Tất cả cuộc trò chuyện được lưu tự động

        ### 🔥 Câu hỏi mẫu:
        - "Tóm tắt thông tin các ứng viên có kinh nghiệm AI"
        - "Ứng viên nào có kỹ năng Python tốt nhất?"
        - "Phân tích điểm mạnh của từng ứng viên"
        - "Gợi ý ứng viên phù hợp cho vị trí Senior Developer"

        ### ⚡ Mẹo sử dụng:
        - **Câu hỏi cụ thể** sẽ cho kết quả tốt hơn
        - **Sử dụng ngữ cảnh** từ cuộc trò chuyện trước
        - **Xuất lịch sử** để lưu trữ thông tin quan trọng
        - **Xóa lịch sử** khi muốn bắt đầu cuộc trò chuyện mới

        ### 🛠️ Cấu hình:
        - **API Key:** Cấu hình ở sidebar bên trái
        - **Model:** Chọn model phù hợp (Gemini, GPT, v.v.)
        - **Theme:** Tùy chỉnh giao diện theo sở thích
        """
        )


@handle_error
def render_enhanced_chat_tab() -> None:
    st.header("🤖 Chat với AI - Trợ lý thông minh")
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    dataset_info = load_dataset_for_chat()
    if dataset_info:
        with st.expander("📊 Thông tin dataset hiện tại", expanded=False):
            st.success(
                f"✅ Đã tải {dataset_info['count']} CV từ file: `{dataset_info['file']}`"
            )
            st.info(f"📅 Last modified: {dataset_info['modified']}")
    else:
        st.warning("⚠️ Chưa có dataset CV. Hãy xử lý CV ở tab 'Xử lý CV' trước.")
    render_chat_statistics()
    container = st.container()
    with container:
        render_chat_history()
    render_chat_input_form()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🗑️ Xóa lịch sử"):
            st.session_state.conversation_history = []
            st.rerun()
    with col2:
        if st.button("📥 Xuất chat"):
            export_chat_history()
    with col3:
        if st.button("📊 Thống kê"):
            st.session_state["show_chat_stats"] = not st.session_state.get("show_chat_stats", False)
            st.rerun()
    with col4:
        if st.button("❓ Hướng dẫn"):
            render_chat_help()
