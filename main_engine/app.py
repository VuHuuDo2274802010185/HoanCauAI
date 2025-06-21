# main_engine/app.py

import sys
from pathlib import Path
import logging
import traceback
import time
from typing import Optional, Dict, Any

# Đưa thư mục gốc (chứa `modules/`) vào sys.path để import modules
HERE = Path(__file__).parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure log directory exists
LOG_DIR = ROOT / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Khi chạy bằng `streamlit run`, __package__ sẽ là None dẫn tới lỗi khi
# dùng relative imports. Thiết lập thủ công để các import như
# `from .tabs import fetch_tab` hoạt động.
if __package__ is None:
    __package__ = "main_engine"

import streamlit as st

import requests
from datetime import datetime

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "app.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
from .chat_ui import render_enhanced_chat_tab

# Import cấu hình và modules with error handling
try:
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
    )
    from modules.auto_fetcher import watch_loop
    
    try:
        from .tabs import (
            fetch_tab,
            process_tab,
            single_tab,
            results_tab,
        )
        # Import chat_tab only if exists, otherwise use built-in
        try:
            from .tabs import chat_tab  # noqa: F401
            HAS_EXTERNAL_CHAT_TAB = True
        except ImportError:
            HAS_EXTERNAL_CHAT_TAB = False
            logger.info("Using built-in chat tab implementation")
    except ImportError as ie:
        logger.warning(f"Some tab imports failed: {ie}")
        # Set fallback flags
        HAS_EXTERNAL_CHAT_TAB = False
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    st.error(f"Lỗi import modules: {e}")
    st.stop()


# --- Error handling utilities ---
def handle_error(func):
    """Decorator for error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"Lỗi trong {func.__name__}: {str(e)}")
            return None
    return wrapper


def safe_session_state_get(key: str, default: Any = None) -> Any:
    """Safely get value from session state"""
    try:
        return st.session_state.get(key, default)
    except Exception as e:
        logger.warning(f"Error accessing session state key '{key}': {e}")
        return default


def safe_session_state_set(key: str, value: Any) -> bool:
    """Safely set value in session state"""
    try:
        st.session_state[key] = value
        return True
    except Exception as e:
        logger.warning(f"Error setting session state key '{key}': {e}")
        return False


# --- Configuration validation ---
def validate_configuration() -> Dict[str, bool]:
    """Validate application configuration"""
    config_status = {
        "env_file": (ROOT / ".env").exists(),
        "config_module": True,
        "static_files": (ROOT / "static").exists(),
        "modules": True
    }
    
    # Check if required modules are importable
    try:
        import modules.qa_chatbot  # noqa: F401
        config_status["qa_module"] = True
    except ImportError:
        config_status["qa_module"] = False
        
    return config_status





# --- Enhanced Streamlit logging handler ---
class StreamlitLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Check if Streamlit context exists
            ctx_exists = self._check_streamlit_context()
            if not ctx_exists:
                return

            msg = self.format(record)
            logs = safe_session_state_get("logs", [])
            
            # Limit log size to prevent memory issues
            if len(logs) > 500:
                logs = logs[-400:]  # Keep last 400 entries
                
            logs.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": record.levelname,
                "message": msg,
                "module": record.module
            })
            safe_session_state_set("logs", logs)
            
        except Exception as e:
            # Fallback to standard logging if Streamlit fails
            print(f"StreamlitLogHandler error: {e}")

    def _check_streamlit_context(self) -> bool:
        """Check if Streamlit context is available"""
        try:
            return bool(st.runtime.exists())
        except Exception:
            try:
                return (
                    st.runtime.scriptrunner.get_script_run_ctx(suppress_warning=True)
                    is not None
                )
            except Exception:
                return False


# Install enhanced logging handler
if not safe_session_state_get("enhanced_log_handler_installed", False):
    handler = StreamlitLogHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s - %(message)s"))
    logging.getLogger().addHandler(handler)
    safe_session_state_set("enhanced_log_handler_installed", True)


def update_log_display(container):
    """Update log display with enhanced formatting"""
    logs = safe_session_state_get("logs", [])
    if not logs:
        container.info("Chưa có log nào.")
        return
        
    # Display recent logs with color coding
    recent_logs = logs[-50:]  # Show last 50 logs
    log_text = ""
    
    for log_entry in recent_logs:
        if isinstance(log_entry, dict):
            timestamp = log_entry.get("timestamp", "")
            level = log_entry.get("level", "INFO")
            message = log_entry.get("message", "")
            log_text += f"[{timestamp}] {level}: {message}\n"
        else:
            log_text += f"{log_entry}\n"
    
    container.code(log_text, language="text")


# --- Cấu hình chung cho trang Streamlit ---
@handle_error
def configure_streamlit_page():
    """Configure Streamlit page with error handling"""
    try:
        st.set_page_config(
            page_title="Hoàn Cầu AI CV Processor",
            page_icon=str(ROOT / "static" / "logo.png"),
            layout="wide",
            initial_sidebar_state="expanded",
        )
        logger.info("Streamlit page configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Streamlit page: {e}")
        # Fallback configuration
        st.set_page_config(
            page_title="Hoàn Cầu AI CV Processor",
            layout="wide"
        )


# --- Enhanced platform detection ---
@handle_error  
def detect_platform(api_key: str) -> Optional[str]:
    """Enhanced platform detection with better error handling"""
    if not api_key or not isinstance(api_key, str):
        return None
        
    api_key = api_key.strip()
    
    # Pattern-based detection
    patterns = {
        "openrouter": ["sk-or-", "or-"],
        "google": ["AIza"],
        "vectorshift": ["vs-", "vectorshift"]
    }
    
    for platform, prefixes in patterns.items():
        if any(api_key.lower().startswith(prefix.lower()) for prefix in prefixes):
            logger.info(f"Detected platform: {platform}")
            return platform
    
    # API-based detection with timeout and retry
    endpoints = [
        ("openrouter", "https://openrouter.ai/api/v1/models", {"Authorization": f"Bearer {api_key}"}),
        ("google", f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}", {})
    ]
    
    for platform, url, headers in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info(f"API verification successful for platform: {platform}")
                return platform
        except requests.RequestException as e:
            logger.debug(f"API check failed for {platform}: {e}")
            continue
    
    logger.warning(f"Could not detect platform for API key: {api_key[:10]}...")
    return None


# --- Enhanced CSS loading ---
@handle_error
def load_css():
    """Load CSS with enhanced error handling"""
    css_path = ROOT / "static" / "style.css"
    
    if css_path.exists():
        try:
            css_content = css_path.read_text(encoding='utf-8')
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            logger.info("Custom CSS loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CSS: {e}")
            st.warning(f"Không thể tải CSS: {e}")
    else:
        logger.info(f"CSS file not found at: {css_path}")


# --- Enhanced model management ---
@handle_error
def get_available_models(provider: str, api_key: str) -> list:
    """Get available models with caching and error handling"""
    cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
    cached_models = safe_session_state_get(cache_key, None)
    
    # Use cached models if available and recent
    if cached_models and isinstance(cached_models, dict):
        cache_time = cached_models.get("timestamp", 0)
        if time.time() - cache_time < 300:  # 5 minutes cache
            return cached_models.get("models", [])
    
    try:
        models = get_models_for_provider(provider, api_key)
        if models:
            # Cache the results
            safe_session_state_set(cache_key, {
                "models": models,
                "timestamp": time.time()
            })
            logger.info(f"Retrieved {len(models)} models for {provider}")
            return models
    except Exception as e:
        logger.error(f"Failed to get models for {provider}: {e}")
    
    # Fallback to default model
    default_model = LLM_CONFIG.get("model", "gemini-2.0-flash")
    return [default_model]



# Initialize application
def initialize_app():
    """Initialize the application with comprehensive setup"""
    if safe_session_state_get("app_initialized", False):
        return
    
    logger.info("Initializing Hoàn Cầu AI CV Processor...")
    
    # Validate configuration
    config_status = validate_configuration()
    if not all(config_status.values()):
        st.warning("Một số cấu hình có thể chưa đầy đủ. Ứng dụng vẫn sẽ hoạt động nhưng có thể thiếu một số tính năng.")
        logger.warning(f"Configuration issues detected: {config_status}")
    
    # Configure page
    configure_streamlit_page()
    
    # Load CSS
    load_css()
    
    safe_session_state_set("app_initialized", True)
    logger.info("Application initialization completed")

# Initialize the application
initialize_app()

# --- Apply theme from Streamlit config ---
theme = st.get_option("theme.base")
if not theme:
    try:
        import darkdetect
        theme = "dark" if darkdetect.isDark() else "light"
    except Exception:
        theme = "light"
if theme:
    st.markdown(
        f"<script>document.documentElement.setAttribute('data-theme', '{theme}');</script>",
        unsafe_allow_html=True,
    )

# Adjust style variables based on chosen Streamlit theme
if theme == "dark":
    st.session_state["text_color"] = "#ffff33"
    st.session_state["background_color"] = "#000000"
    st.session_state["secondary_color"] = "#1e1e1e"
    st.session_state["accent_color"] = "#ffff33"
else:
    st.session_state["text_color"] = "#2d1810"
    st.session_state["background_color"] = "#fffbf0"
    st.session_state["secondary_color"] = "#f4e09c"
    st.session_state["accent_color"] = "#d4af37"

# --- Sidebar: logo và cấu hình LLM ---
@handle_error
def render_sidebar():
    """Render sidebar with enhanced error handling"""
    
    # Logo display
    logo_path = ROOT / "static" / "logo.png"
    if logo_path.exists():
        try:
            st.sidebar.image(str(logo_path), use_container_width=True)
        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
            st.sidebar.markdown("**🏢 Hoàn Cầu AI CV Processor**")
    
    # System status indicator
    with st.sidebar.expander("📊 Trạng thái hệ thống", expanded=False):
        config_status = validate_configuration()
        for component, status in config_status.items():
            emoji = "✅" if status else "❌"
            st.write(f"{emoji} {component.replace('_', ' ').title()}")
    
    st.sidebar.header("⚙️ Cấu hình LLM")

    # Provider selection with validation
    provider = st.sidebar.selectbox(
        "🔧 Provider",
        options=["google", "openrouter"],
        key="selected_provider",
        help="Chọn nhà cung cấp LLM",
    )

    # API key input with enhanced validation
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

    # API key validation
    if api_key:
        detected_platform = detect_platform(api_key)
        if detected_platform and detected_platform != provider:
            st.sidebar.warning(f"⚠️ API key có vẻ thuộc về {detected_platform}, không phải {provider}")
        elif detected_platform == provider:
            st.sidebar.success(f"✅ API key hợp lệ cho {provider}")

    # Model fetching with better error handling
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        if st.button("🔄 Lấy models", help="Lấy danh sách model từ API"):
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
        if st.button("🗑️", help="Xóa cache models"):
            cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.sidebar.info("Cache đã được xóa")

    # Model selection
    models = safe_session_state_get("available_models", get_available_models(provider, api_key))
    
    if not models:
        st.sidebar.error("❌ Không lấy được models, vui lòng kiểm tra API Key.")
        models = [LLM_CONFIG.get("model", "gemini-2.0-flash")]

    # Set default model
    default_model = LLM_CONFIG.get("model", "gemini-2.0-flash")
    if default_model not in models and models:
        default_model = models[0]
    
    if not safe_session_state_get("selected_model") or safe_session_state_get("selected_model") not in models:
        safe_session_state_set("selected_model", default_model)

    # Model selection with pricing
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

    # Display current configuration
    try:
        price = get_model_price(model)
        label = f"{model} ({price})" if price != "unknown" else model
    except Exception:
        label = model
        
    st.sidebar.markdown(f"**🎯 Đang dùng:** `{provider}` / `{label}`")
    
    return provider, api_key, model

# Render sidebar and get configuration
provider, api_key, model = render_sidebar()

# --- Email configuration with enhanced validation ---
@handle_error
def render_email_config():
    """Render email configuration section"""
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
    
    # Email validation
    if email_user and "@" not in email_user:
        st.sidebar.warning("⚠️ Địa chỉ email không hợp lệ")
    
    # Auto fetcher management
    manage_auto_fetcher(email_user, email_pass, unseen_only)
    
    return email_user, email_pass, unseen_only


@handle_error
def manage_auto_fetcher(email_user: str, email_pass: str, unseen_only: bool):
    """Manage auto fetcher thread with better error handling"""
    if not (email_user and email_pass):
        return
    
    # Check if auto fetcher is already running
    if safe_session_state_get("auto_fetcher_thread"):
        st.sidebar.success("✅ Auto fetcher đang chạy")
        
        if st.sidebar.button("🛑 Dừng auto fetcher"):
            safe_session_state_set("auto_fetcher_thread", None)
            st.sidebar.info("Auto fetcher đã được dừng")
            st.rerun()
        return
    
    # Start auto fetcher
    try:
        import threading
        
        def auto_fetch_worker():
            try:
                logger.info("Starting auto fetcher thread")
                watch_loop(
                    600,  # 10 minutes interval
                    host=EMAIL_HOST,
                    port=EMAIL_PORT,
                    user=email_user,
                    password=email_pass,
                    unseen_only=unseen_only,
                )
            except Exception as e:
                logger.error(f"Auto fetcher error: {e}")
                safe_session_state_set("auto_fetcher_error", str(e))

        thread = threading.Thread(target=auto_fetch_worker, daemon=True)
        thread.start()
        safe_session_state_set("auto_fetcher_thread", thread)
        
        logger.info("Auto fetcher started successfully")
        st.sidebar.info("🔄 Đang tự động lấy CV từ email...")
        
    except Exception as e:
        logger.error(f"Failed to start auto fetcher: {e}")
        st.sidebar.error(f"Lỗi khởi động auto fetcher: {e}")

# Render email configuration
email_user, email_pass, unseen_only = render_email_config()

# Load style preferences from session state
background_color = st.session_state.get("background_color", "#fffbf0")
text_color = st.session_state.get("text_color", "#000000")
accent_color = st.session_state.get("accent_color", "#d4af37")
secondary_color = st.session_state.get("secondary_color", "#f4e09c")
font_options = [
    "Be Vietnam Pro", "Poppins", "Roboto", "Open Sans", "Lato",
    "Montserrat", "Inter", "Arial", "Verdana", "Times New Roman", "Georgia"
]
font_family = font_options[st.session_state.get("font_family_index", 0)]
font_size = st.session_state.get("font_size", 14)
border_radius = st.session_state.get("border_radius", 8)
layout_compact = st.session_state.get("layout_compact", False)

# Apply custom styling with beautiful gradients and shadows
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
    
    /* Custom scrollbar */
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
    
    /* Form styling */
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

# --- Main UI: 3 Tabs ---
tab_fetch, tab_process, tab_single, tab_results, tab_chat = st.tabs(
    [
        "Lấy CV từ Email",
        "Xử lý CV",
        "Single File",
        "Kết quả",
        "Hỏi AI",
    ]
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
    render_enhanced_chat_tab()


# --- Footer ---
st.markdown("---")
st.markdown(
    f"<center><small>Powered by Hoàn Cầu AI CV Processor | {provider} / {model}</small></center>",
    unsafe_allow_html=True,
)
