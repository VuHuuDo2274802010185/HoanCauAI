from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ensure package imports work when executed via ``streamlit run``
HERE = Path(__file__).parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if __package__ is None:
    __package__ = "main_engine"

from .utils import (
    ROOT,
    initialize_app,
    logger,
)
from .ui.sidebar import render_sidebar, render_email_config
from .ui.chat import render_enhanced_chat_tab
from .tabs import fetch_tab, process_tab, single_tab, results_tab

# attempt optional external chat tab
try:
    from .tabs import chat_tab  # type: ignore
    HAS_EXTERNAL_CHAT_TAB = True
except Exception:
    HAS_EXTERNAL_CHAT_TAB = False
    logger.info("Using built-in chat tab implementation")


# -------- initialization ---------
initialize_app()

# theme adjustments
theme = st.get_option("theme.base") or "light"
st.markdown(
    f"<script>document.documentElement.setAttribute('data-theme', '{theme}');</script>",
    unsafe_allow_html=True,
)
if theme == "dark":
    st.session_state["text_color"] = "#f0f0f0"
    st.session_state["background_color"] = "#121212"
    st.session_state["secondary_color"] = "#333333"
else:
    st.session_state["text_color"] = "#000000"
    st.session_state["background_color"] = "#fffbf0"
    st.session_state["secondary_color"] = "#f4e09c"
st.session_state["accent_color"] = "#d4af37"

# sidebar configuration
provider, api_key, model = render_sidebar()
email_user, email_pass, unseen_only = render_email_config()

# style preferences
background_color = st.session_state.get("background_color", "#fffbf0")
text_color = st.session_state.get("text_color", "#000000")
accent_color = st.session_state.get("accent_color", "#d4af37")
secondary_color = st.session_state.get("secondary_color", "#f4e09c")
font_options = [
    "Be Vietnam Pro",
    "Poppins",
    "Roboto",
    "Open Sans",
    "Lato",
    "Montserrat",
    "Inter",
    "Arial",
    "Verdana",
    "Times New Roman",
    "Georgia",
]
font_family = font_options[st.session_state.get("font_family_index", 0)]
font_size = st.session_state.get("font_size", 14)
border_radius = st.session_state.get("border_radius", 8)
layout_compact = st.session_state.get("layout_compact", False)

padding = "0.5rem" if layout_compact else "1rem"
custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&family=Open+Sans:wght@300;400;500;600;700&family=Lato:wght@300;400;700&family=Montserrat:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    .main .block-container {{
        padding-top: {padding};
        padding-bottom: {padding};
        background: linear-gradient(135deg, {background_color} 0%, {secondary_color}22 100%);
        min-height: 100vh;
    }}
    .stApp {{
        background: linear-gradient(135deg, {background_color} 0%, {secondary_color}22 100%);
        color: {text_color};
        font-family: '{font_family}', sans-serif;
        font-size: {font_size}px;
    }}
    .stSidebar {{
        background: linear-gradient(180deg, {background_color} 0%, {secondary_color}33 100%);
        border-right: 2px solid {accent_color}22;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, {accent_color} 0%, {secondary_color} 100%);
        color: var(--btn-text-color);
        border-radius: {border_radius}px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        font-family: '{font_family}', sans-serif;
        box-shadow: 0 4px 15px {accent_color}33;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, {accent_color}dd 0%, {secondary_color}dd 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px {accent_color}44;
    }}
    .stSelectbox > div > div {{
        background-color: {background_color};
        color: {text_color};
        border: 2px solid {secondary_color};
        border-radius: {border_radius}px;
    }}
    .stTextInput > div > div > input {{
        background-color: {background_color};
        color: {text_color};
        border: 2px solid {secondary_color};
        border-radius: {border_radius}px;
        font-family: '{font_family}', sans-serif;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {accent_color};
        box-shadow: 0 0 0 2px {accent_color}33;
    }}
    .stTextArea > div > div > textarea {{
        background-color: {background_color};
        color: {text_color};
        border: 2px solid {secondary_color};
        border-radius: {border_radius}px;
        font-family: '{font_family}', sans-serif;
    }}
    .stTextArea > div > div > textarea:focus {{
        border-color: {accent_color};
        box-shadow: 0 0 0 2px {accent_color}33;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {accent_color};
        font-family: '{font_family}', sans-serif;
        font-weight: 600;
        text-shadow: 1px 1px 2px {accent_color}22;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        width: 100%;
        display: flex;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: linear-gradient(135deg, {secondary_color}44 0%, {background_color} 100%);
        border-radius: {border_radius}px;
        color: {text_color};
        border: 2px solid {secondary_color}66;
        flex: 1;
        text-align: center;
        padding: 0.75rem 0;
        font-size: 1.1rem;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {accent_color} 0%, {secondary_color} 100%);
        color: white;
        border-color: {accent_color};
    }}
    .chat-message {{
        margin: 10px 0;
        padding: 12px 18px;
        border-radius: {border_radius + 10}px;
        max-width: 70%;
        word-wrap: break-word;
        font-family: '{font_family}', sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {secondary_color}33;
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {accent_color};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {accent_color}dd;
    }}
    .stForm {{
        background: linear-gradient(135deg, {background_color}aa 0%, {secondary_color}22 100%);
        border: 2px solid {secondary_color}66;
        border-radius: {border_radius}px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ----- main UI -----
tab_fetch, tab_process, tab_single, tab_results, tab_chat = st.tabs(
    ["Lấy CV từ Email", "Xử lý CV", "Single File", "Kết quả", "Hỏi AI"]
)
with tab_fetch:
    fetch_tab.render(email_user, email_pass, unseen_only)
with tab_process:
    process_tab.render(provider, model, api_key)
with tab_single:
    single_tab.render(provider, model, api_key, ROOT)
with tab_results:
    results_tab.render()
with tab_chat:
    if HAS_EXTERNAL_CHAT_TAB:
        chat_tab.render(provider, model, api_key)  # type: ignore
    else:
        render_enhanced_chat_tab()

st.markdown("---")
st.markdown(
    f"<center><small>Powered by Hoàn Cầu AI CV Processor | {provider} / {model}</small></center>",
    unsafe_allow_html=True,
)
