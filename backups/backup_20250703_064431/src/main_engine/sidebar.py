"""Sidebar related rendering utilities."""

# --- Thư viện chuẩn ---
import logging  # quản lý log
from pathlib import Path  # thao tác đường dẫn tệp

# --- Thư viện bên thứ ba ---
import streamlit as st  # giao diện web
from dotenv import set_key, load_dotenv  # đọc/ghi file .env

# --- Modules nội bộ ---
from modules.config import (
    LLM_CONFIG,
    get_model_price,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASS,
    EMAIL_UNSEEN_ONLY,
)
from modules.ui_utils import loading_logs
from .utils import handle_error, safe_session_state_get, safe_session_state_set

# Logger cho file này
logger = logging.getLogger(__name__)
@handle_error
def render_sidebar(validate_configuration, detect_platform, get_available_models):
    """Render the sidebar with provider and model selection."""
    # Đường dẫn tới logo trong thư mục static
    logo_path = Path(__file__).resolve().parents[2] / "static" / "logo.png"
    if logo_path.exists():
        try:
            # Hiển thị logo ở sidebar
            st.sidebar.image(str(logo_path), use_container_width=True, caption="Hoàn Cầu AI CV Processor")
        except Exception as e:
            # Nếu lỗi, ghi log và chỉ hiển thị text thay thế
            logger.warning("Failed to load logo: %s", e)
            st.sidebar.markdown("**🏢 Hoàn Cầu AI CV Processor**")

    # Hiển thị trạng thái cấu hình trong một expander
    with st.sidebar.expander("📊 Trạng thái hệ thống", expanded=False):
        config_status = validate_configuration()
        for component, status in config_status.items():
            # Dùng emoji để báo trạng thái từng thành phần
            emoji = "✅" if status else "❌"
            st.write(f"{emoji} {component.replace('_', ' ').title()}")

    st.sidebar.header("⚙️ Cấu hình LLM")
    # Chọn provider (Google hoặc OpenRouter)
    provider = st.sidebar.selectbox(
        "🔧 Provider",
        options=["google", "openrouter"],
        key="selected_provider",
        help="Chọn nhà cung cấp LLM",
    )

    # Nhập API key tùy vào provider
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

    # Hai cột: nút lấy models và xóa cache
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        # Nút gọi API để lấy danh sách model
        if st.button("🔄 Lấy models", help="Lấy danh sách model từ API"):
            if not api_key:
                st.sidebar.warning("⚠️ Vui lòng nhập API Key trước khi lấy models")
            else:
                with loading_logs("Đang lấy danh sách models..."):
                    models = get_available_models(provider, api_key)
                    if models:
                        safe_session_state_set("available_models", models)
                        st.sidebar.success(f"✅ Đã lấy {len(models)} models")
                    else:
                        st.sidebar.error("❌ Không thể lấy models")
    with col2:
        # Nút xóa cache models
        if st.button("🗑️", help="Xóa cache models"):
            cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.sidebar.info("Cache đã được xóa")

    # Lấy danh sách models từ cache hoặc API
    models = safe_session_state_get("available_models", get_available_models(provider, api_key))
    if not models:
        st.sidebar.error("❌ Không lấy được models, vui lòng kiểm tra API Key.")
        models = [LLM_CONFIG.get("model", "gemini-2.5-flash-lite-preview-06-17")]

    # Đặt model mặc định nếu model hiện tại không nằm trong danh sách
    default_model = LLM_CONFIG.get("model", "gemini-2.5-flash-lite-preview-06-17")
    if default_model not in models and models:
        default_model = models[0]
    if not safe_session_state_get("selected_model") or safe_session_state_get("selected_model") not in models:
        safe_session_state_set("selected_model", default_model)

    def format_model_option(model: str) -> str:
        """Hiển thị giá model (nếu có) bên cạnh tên"""
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
def render_email_config(root: Path, provider: str, api_key: str):
    """Render email configuration section."""
    st.sidebar.header("📧 Thông tin Email")
    # Nhập thông tin email để tự động tải CV
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
    # Lưu thông tin vào file .env khi nhấn nút
    if st.sidebar.button("💾 Lưu mật khẩu", key="save_email_pass"):
        env_path = root / ".env"
        try:
            env_path.touch(exist_ok=True)
            load_dotenv(env_path)
            set_key(str(env_path), "EMAIL_USER", email_user)
            set_key(str(env_path), "EMAIL_PASS", email_pass)
            set_key(str(env_path), "LLM_PROVIDER", provider)
            if provider == "google":
                set_key(str(env_path), "GOOGLE_API_KEY", api_key)
            else:
                set_key(str(env_path), "OPENROUTER_API_KEY", api_key)
            st.sidebar.success("Đã lưu thông tin email và API vào .env")
        except Exception as e:
            st.sidebar.error(f"Lỗi khi lưu file .env: {e}")

    if email_user and "@" not in email_user:
        st.sidebar.warning("⚠️ Địa chỉ email không hợp lệ")

    return email_user, email_pass


# Các hàm public của module
__all__ = [
    "render_sidebar",
    "render_email_config",
]
