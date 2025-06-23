from __future__ import annotations

import logging
import threading
import streamlit as st

from ..utils import (
    handle_error,
    validate_configuration,
    safe_session_state_get,
    safe_session_state_set,
    get_available_models,
    detect_platform,
    ROOT,
)
from modules.config import (
    LLM_CONFIG,
    get_model_price,
    OUTPUT_CSV,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASS,
    EMAIL_UNSEEN_ONLY,
)
from modules.auto_fetcher import watch_loop

logger = logging.getLogger(__name__)


@handle_error
def render_sidebar():
    logo_path = ROOT / "static" / "logo.png"
    if logo_path.exists():
        try:
            st.sidebar.image(str(logo_path), use_container_width=True)
        except Exception as e:  # pragma: no cover - best effort
            logger.warning("Failed to load logo: %s", e)
            st.sidebar.markdown("**🏢 Hoàn Cầu AI CV Processor**")
    with st.sidebar.expander("📊 Trạng thái hệ thống", expanded=False):
        cfg = validate_configuration()
        for comp, status in cfg.items():
            emoji = "✅" if status else "❌"
            st.write(f"{emoji} {comp.replace('_', ' ').title()}")
    st.sidebar.header("⚙️ Cấu hình LLM")
    provider = st.sidebar.selectbox(
        "🔧 Provider",
        options=["google", "openrouter"],
        key="selected_provider",
        help="Chọn nhà cung cấp LLM",
    )
    if provider == "google":
        api_key = st.sidebar.text_input(
            "🔑 Google API Key",
            type="password",
            value=safe_session_state_get("google_api_key", GOOGLE_API_KEY),
            key="google_api_key",
            help="Khóa API dùng cho Google Gemini",
        )
    else:
        api_key = st.sidebar.text_input(
            "🔑 OpenRouter API Key",
            type="password",
            value=safe_session_state_get("openrouter_api_key", OPENROUTER_API_KEY),
            key="openrouter_api_key",
            help="Khóa API cho OpenRouter",
        )
    if api_key:
        detected_platform = detect_platform(api_key)
        if detected_platform and detected_platform != provider:
            st.sidebar.warning(f"⚠️ API key có vẻ thuộc về {detected_platform}, không phải {provider}")
        elif detected_platform == provider:
            st.sidebar.success(f"✅ API key hợp lệ cho {provider}")
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        if st.button("🔄 Lấy models"):
            if not api_key:
                st.sidebar.warning("⚠️ Vui lòng nhập API Key trước khi lấy models")
            else:
                with st.spinner("Đang lấy danh sách models..."):
                    models = get_available_models(provider, api_key)
                    if models:
                        safe_session_state_set("available_models", models)
                        st.sidebar.success(f"✅ Đã lấy {len(models)} models")
                    else:
                        st.sidebar.error("❌ Không thể lấy models")
    with col2:
        if st.button("🗑️"):
            cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.sidebar.info("Cache đã được xóa")
    models = safe_session_state_get("available_models", get_available_models(provider, api_key))
    if not models:
        st.sidebar.error("❌ Không lấy được models, vui lòng kiểm tra API Key.")
        models = [LLM_CONFIG.get("model", "gemini-2.0-flash")]
    default_model = LLM_CONFIG.get("model", "gemini-2.0-flash")
    if default_model not in models and models:
        default_model = models[0]
    if not safe_session_state_get("selected_model") or safe_session_state_get("selected_model") not in models:
        safe_session_state_set("selected_model", default_model)
    def format_model_option(model: str) -> str:
        try:
            price = get_model_price(model)
            return f"{model} ({price})" if price != "unknown" else model
        except Exception:
            return model
    model = st.sidebar.selectbox(
        "🤖 Model",
        options=models,
        key="selected_model",
        help="Chọn mô hình LLM",
        format_func=format_model_option,
    )
    try:
        price = get_model_price(model)
        label = f"{model} ({price})" if price != "unknown" else model
    except Exception:
        label = model
    st.sidebar.markdown(f"**🎯 Đang dùng:** `{provider}` / `{label}`")
    return provider, api_key, model


@handle_error
def manage_auto_fetcher(email_user: str, email_pass: str, unseen_only: bool):
    if not (email_user and email_pass):
        return
    if safe_session_state_get("auto_fetcher_thread"):
        st.sidebar.success("✅ Auto fetcher đang chạy")
        if st.sidebar.button("🛑 Dừng auto fetcher"):
            safe_session_state_set("auto_fetcher_thread", None)
            st.sidebar.info("Auto fetcher đã được dừng")
            st.rerun()
        return
    try:
        def auto_fetch_worker():
            try:
                logger.info("Starting auto fetcher thread")
                watch_loop(
                    600,
                    host=EMAIL_HOST,
                    port=EMAIL_PORT,
                    user=email_user,
                    password=email_pass,
                    unseen_only=unseen_only,
                )
            except Exception as e:
                logger.error("Auto fetcher error: %s", e)
                safe_session_state_set("auto_fetcher_error", str(e))
        thread = threading.Thread(target=auto_fetch_worker, daemon=True)
        thread.start()
        safe_session_state_set("auto_fetcher_thread", thread)
        st.sidebar.info("🔄 Đang tự động lấy CV từ email...")
    except Exception as e:
        logger.error("Failed to start auto fetcher: %s", e)
        st.sidebar.error(f"Lỗi khởi động auto fetcher: {e}")


@handle_error
def render_email_config():
    st.sidebar.header("📧 Thông tin Email")
    email_user = st.sidebar.text_input(
        "📮 Gmail",
        value=safe_session_state_get("email_user", EMAIL_USER),
        key="email_user",
        help="Địa chỉ Gmail dùng để tự động tải CV",
    )
    email_pass = st.sidebar.text_input(
        "🔐 Mật khẩu",
        type="password",
        value=safe_session_state_get("email_pass", EMAIL_PASS),
        key="email_pass",
        help="Mật khẩu hoặc App Password của Gmail",
    )
    unseen_only = st.sidebar.checkbox(
        "👁️ Chỉ quét email chưa đọc",
        value=safe_session_state_get("unseen_only", EMAIL_UNSEEN_ONLY),
        key="unseen_only",
        help="Nếu bỏ chọn, hệ thống sẽ quét toàn bộ hộp thư",
    )
    if email_user and "@" not in email_user:
        st.sidebar.warning("⚠️ Địa chỉ email không hợp lệ")
    manage_auto_fetcher(email_user, email_pass, unseen_only)
    return email_user, email_pass, unseen_only
