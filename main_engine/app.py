# main_engine/app.py

import os, sys
from pathlib import Path
import logging

# Đưa thư mục gốc (chứa `modules/`) vào sys.path để import modules
HERE = Path(__file__).parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Khi chạy bằng `streamlit run`, __package__ sẽ là None dẫn tới lỗi khi
# dùng relative imports. Thiết lập thủ công để các import như
# `from .tabs import fetch_tab` hoạt động.
if __package__ is None:
    __package__ = "main_engine"

import streamlit as st
from typing import cast
import requests
# Import cấu hình và modules
from modules.config import (
    LLM_CONFIG,
    get_models_for_provider,
    get_model_price,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASS,
    EMAIL_UNSEEN_ONLY,
    MCP_API_KEY,
)
from modules.auto_fetcher import watch_loop

from .tabs import (
    fetch_tab,
    process_tab,
    single_tab,
    results_tab,
    flow_tab,
    mcp_tab,
    chat_tab,
)

# --- Streamlit logging handler ---
class StreamlitLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Only attempt to access st.session_state when a ScriptRunContext exists
        try:
            ctx_exists = bool(st.runtime.exists())
        except Exception:
            try:
                ctx_exists = (
                    st.runtime.scriptrunner.get_script_run_ctx(
                        suppress_warning=True
                    )
                    is not None
                )
            except Exception:
                ctx_exists = False

        if not ctx_exists:
            return

        msg = self.format(record)
        logs = st.session_state.get("logs", [])
        logs.append(msg)
        st.session_state["logs"] = logs

if "streamlit_log_handler" not in st.session_state:
    _h = StreamlitLogHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(_h)
    st.session_state["streamlit_log_handler"] = True

def update_log(box):
    lines = st.session_state.get("logs", [])
    box.code("\n".join(lines[-100:]), language="text")

# --- Cấu hình chung cho trang Streamlit ---
st.set_page_config(
    page_title="Hoàn Cầu AI CV Processor",
    page_icon=str(ROOT / "static" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Tự nhận diện platform từ API key ---
def detect_platform(api_key: str) -> str | None:
    if not api_key:
        return None
    if api_key.startswith("sk-or-"):
        return "openrouter"
    if api_key.startswith("AIza"):
        return "google"
    if api_key.lower().startswith("vs-") or "vectorshift" in api_key.lower():
        return "vectorshift"
    # Thử gọi các endpoint đơn giản để nhận diện
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=3,
        )
        if r.status_code == 200:
            return "openrouter"
    except Exception:
        pass
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=3,
        )
        if r.status_code == 200:
            return "google"
    except Exception:
        pass
    return None

# --- Load CSS tuỳ chỉnh ---
def load_css():
    path = ROOT / "static" / "style.css"
    if path.exists():
        st.markdown(f"<style>{path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Không tìm thấy CSS tại: {path}")
load_css()

# --- Sidebar: logo và cấu hình LLM ---
logo_path = ROOT / "static" / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

st.sidebar.header("Cấu hình LLM")

# Chọn provider
provider = st.sidebar.selectbox(
    "Provider",
    options=["google", "openrouter"],
    key="selected_provider",
    help="Chọn nhà cung cấp LLM"
)

# Nhập API key theo provider
if provider == "google":
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        value=st.session_state.get("google_api_key", GOOGLE_API_KEY),
        key="google_api_key"
    )
else:
    api_key = st.sidebar.text_input(
        "OpenRouter API Key",
        type="password",
        value=st.session_state.get("openrouter_api_key", OPENROUTER_API_KEY),
        key="openrouter_api_key"
    )

if st.sidebar.button("Lấy models"):
    if not api_key:
        st.sidebar.warning("Vui lòng nhập API Key trước khi lấy models")
    else:
        st.session_state.available_models = get_models_for_provider(provider, api_key)

models = st.session_state.get("available_models", get_models_for_provider(provider, api_key))
if not models:
    st.sidebar.error("Không lấy được models, vui lòng kiểm tra API Key.")
    models = [LLM_CONFIG.get("model")]
# Đặt model mặc định "gemini-2.0-flask" khi khởi động lần đầu
default_model = LLM_CONFIG.get("model", "gemini-2.0-flask")
if default_model not in models:
    default_model = models[0]
if (
    "selected_model" not in st.session_state
    or st.session_state.selected_model not in models
):
    st.session_state.selected_model = default_model

# Chọn model, lưu tự động vào session_state
def _fmt_option(m: str) -> str:
    p = get_model_price(m)
    return f"{m} ({p})" if p != "unknown" else m

model = st.sidebar.selectbox(
    "Model",
    options=models,
    key="selected_model",
    help="Chọn mô hình LLM",
    format_func=_fmt_option,
)

price = get_model_price(model)
label = f"{model} ({price})" if price != "unknown" else model
# Hiển thị cấu hình đang dùng
st.sidebar.markdown(f"**Đang dùng:** `{provider}` / `{label}`")

st.sidebar.header("Thông tin Email")
email_user = st.sidebar.text_input(
    "Gmail",
    value=st.session_state.get("email_user", EMAIL_USER),
    key="email_user",
)
email_pass = st.sidebar.text_input(
    "Mật khẩu",
    type="password",
    value=st.session_state.get("email_pass", EMAIL_PASS),
    key="email_pass",
)
unseen_only = st.sidebar.checkbox(
    "Chỉ quét email chưa đọc",
    value=st.session_state.get("unseen_only", EMAIL_UNSEEN_ONLY),
    key="unseen_only",
)

# Tự động khởi động auto fetcher khi đã nhập đủ thông tin
if email_user and email_pass and "auto_fetcher_thread" not in st.session_state:
    import threading

    def _auto_fetch():
        watch_loop(
            600,
            host=EMAIL_HOST,
            port=EMAIL_PORT,
            user=email_user,
            password=email_pass,
            unseen_only=unseen_only,
        )

    t = threading.Thread(target=_auto_fetch, daemon=True)
    t.start()
    st.session_state.auto_fetcher_thread = t
    logging.info("Đã khởi động auto fetcher background thread")
    st.sidebar.info("Đang tự động lấy CV từ email...")

# --- Main UI: 5 Tabs ---
tab_fetch, tab_process, tab_single, tab_results, tab_flow, tab_mcp, tab_chat = st.tabs([
    "Lấy CV từ Email", "Xử lý CV", "Single File", "Kết quả", "Xây dựng flow", "MCP Server", "Hỏi AI"
])

with tab_fetch:
    fetch_tab.render(email_user, email_pass, unseen_only)

with tab_process:
    process_tab.render(provider, model, api_key)

with tab_single:
    single_tab.render(provider, model, api_key, ROOT)

with tab_results:
    results_tab.render()

with tab_flow:
    flow_tab.render(ROOT)

with tab_mcp:
    mcp_tab.render(detect_platform)

with tab_chat:
    chat_tab.render(provider, model, api_key)

# --- Log Viewer ---
log_expander = st.expander("Xem log xử lý", expanded=False)
with log_expander:
    log_box = st.empty()
    log_lines = st.session_state.get("logs", [])
    update_log(log_box)

# --- Footer ---
st.markdown("---")
st.markdown(
    f"<center><small>Powered by Hoàn Cầu AI CV Processor | {provider} / {label}</small></center>",
    unsafe_allow_html=True
)
