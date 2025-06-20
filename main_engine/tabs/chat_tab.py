import logging
import os
import pandas as pd
import streamlit as st
from typing import cast

from modules.qa_chatbot import answer_question
from modules.config import OUTPUT_CSV


def render(provider: str, model: str, api_key: str) -> None:
    """Render UI for asking questions about the CV data."""
    st.subheader("Hỏi AI về dữ liệu CV")
    if 'trigger_ai' not in st.session_state:
        st.session_state.trigger_ai = False

    def submit_ai():
        st.session_state.trigger_ai = True

    question = st.text_input(
        "Nhập câu hỏi và nhấn Enter để gửi", key="ai_question", on_change=submit_ai
    )

    if st.session_state.trigger_ai:
        st.session_state.trigger_ai = False
        if not question.strip():
            st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
        elif not os.path.exists(OUTPUT_CSV):
            st.warning("Chưa có dữ liệu CSV để hỏi.")
        else:
            df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
            with st.spinner("Đang hỏi AI..."):
                try:
                    logging.info("Đang gửi câu hỏi tới AI")
                    answer = answer_question(
                        question,
                        df,
                        cast(str, provider),
                        cast(str, model),
                        cast(str, api_key)
                    )
                    st.markdown(answer)
                except Exception as e:
                    logging.error(f"Lỗi hỏi AI: {e}")
                    st.error(f"Lỗi khi hỏi AI: {e}")
