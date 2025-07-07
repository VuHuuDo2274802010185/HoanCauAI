#!/usr/bin/env python3
"""
Complete Gradio app for HoanCau AI CV Processor
Logic and presentation exactly replicated from Streamlit app
"""

import sys
from pathlib import Path
import logging
import json
import time
import base64
import os
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, Tuple, List

# Add project root to path
HERE = Path(__file__).parent
ROOT = HERE
SRC_DIR = ROOT / "src"

# Ensure proper Python path setup
for path in (ROOT, SRC_DIR):
    path_str = str(path.absolute())
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

try:
    import gradio as gr
    import pandas as pd
    import requests
    from dotenv import load_dotenv, set_key
    
    # Import project modules
    from modules.config import (
        LLM_CONFIG,
        get_models_for_provider,
        get_model_price,
        OUTPUT_CSV,
        OUTPUT_EXCEL,
        GOOGLE_API_KEY,
        OPENROUTER_API_KEY,
        EMAIL_HOST,
        EMAIL_PORT,
        EMAIL_USER,
        EMAIL_PASS,
        EMAIL_UNSEEN_ONLY,
        ATTACHMENT_DIR,
        SENT_TIME_FILE,
        LOG_FILE,
    )
    
    from modules.dynamic_llm_client import DynamicLLMClient
    from modules.cv_processor import CVProcessor, format_sent_time_display
    from modules.email_fetcher import EmailFetcher
    from modules.sent_time_store import load_sent_times
    from modules.progress_manager import GradioProgressBar
    
    # Import QA chatbot if available
    try:
        from modules.qa_chatbot import QAChatbot
        HAS_QA_CHATBOT = True
    except ImportError:
        HAS_QA_CHATBOT = False
        QAChatbot = None
    
    MODULES_LOADED = True
    print("✅ All modules loaded successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    MODULES_LOADED = False

# Configure logging (same as Streamlit app)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Global application state (replacing Streamlit session state)
class AppState:
    def __init__(self):
        # Initialize with defaults like Streamlit app
        self.conversation_history = []
        self.background_color = "#fff7e6"
        self.text_color = "#222222"
        self.accent_color = "#d4af37"
        self.secondary_color = "#ffeacc"
        self.font_family_index = 0
        self.font_size = 14
        self.border_radius = 8
        self.layout_compact = False
        self.app_initialized = False
        self.last_error = None
        self.error_count = 0
        self.logs = []
        
        # LLM Configuration
        self.selected_provider = "google"
        self.selected_model = LLM_CONFIG.get("model", "gemini-2.0-flash-exp")
        self.google_api_key = GOOGLE_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.available_models = []
        
        # Email Configuration  
        self.email_user = EMAIL_USER
        self.email_pass = EMAIL_PASS
        self.unseen_only = EMAIL_UNSEEN_ONLY
        
        # UI state flags
        self.confirm_delete = False
        self.show_chat_stats = False
        self.show_chat_help = False
        self.enhanced_log_handler_installed = False

# Global app state instance
app_state = AppState()

# Error handling utilities (replicated from Streamlit utils.py)
def handle_error(func):
    """Decorator for error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            app_state.error_count += 1
            app_state.last_error = str(e)
            return f"❌ Lỗi trong {func.__name__}: {e}"
    return wrapper

def safe_get(attr: str, default: Any = None) -> Any:
    """Safely get attribute from app state"""
    try:
        return getattr(app_state, attr, default)
    except Exception as e:
        logger.warning(f"Error accessing app state '{attr}': {e}")
        return default

def safe_set(attr: str, value: Any) -> bool:
    """Safely set attribute in app state"""
    try:
        setattr(app_state, attr, value)
        return True
    except Exception as e:
        logger.warning(f"Error setting app state '{attr}': {e}")
        return False

# Configuration validation (replicated from Streamlit app.py)
def validate_configuration() -> Dict[str, bool]:
    """Validate application configuration"""
    config_status = {
        "env_file": (ROOT / ".env").exists(),
        "config_module": True,
        "static_files": (ROOT / "static").exists(),
        "modules": True,
    }
    
    # Check if required modules are importable
    try:
        import modules.qa_chatbot
        config_status["qa_module"] = True
    except ImportError:
        config_status["qa_module"] = False
    
    return config_status

# Platform detection (replicated from Streamlit app.py)
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
        "vectorshift": ["vs-", "vectorshift"],
    }
    
    for platform, prefixes in patterns.items():
        if any(api_key.lower().startswith(prefix.lower()) for prefix in prefixes):
            logger.info(f"Detected platform: {platform}")
            return platform
    
    # API-based detection with timeout and retry
    endpoints = [
        (
            "openrouter",
            "https://openrouter.ai/api/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        (
            "google",
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            {},
        ),
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

# Model management (replicated from Streamlit app.py)
@handle_error
def get_available_models(provider: str, api_key: str) -> list:
    """Get available models with caching and error handling"""
    try:
        models = get_models_for_provider(provider, api_key)
        if models:
            app_state.available_models = models
            logger.info(f"Retrieved {len(models)} models for {provider}")
            return models
    except Exception as e:
        logger.error(f"Failed to get models for {provider}: {e}")
    
    # Fallback to default model
    default_model = LLM_CONFIG.get("model", "gemini-2.0-flash-exp")
    return [default_model]

# ============================================================================
# SIDEBAR FUNCTIONS (replicated from sidebar.py)
# ============================================================================

def create_sidebar_ui():
    """Create sidebar UI components"""
    
    # System status section
    with gr.Accordion("📊 Trạng thái hệ thống", open=False):
        status_text = gr.Textbox(
            value=get_system_status(),
            label="System Status",
            interactive=False,
            max_lines=10
        )
    
    # LLM Configuration section
    gr.Markdown("### ⚙️ Cấu hình LLM")
    
    provider_dropdown = gr.Dropdown(
        choices=["google", "openrouter"],
        value=app_state.selected_provider,
        label="🔧 Provider",
        info="Chọn nhà cung cấp LLM"
    )
    
    # API Key input (conditional based on provider)
    api_key_input = gr.Textbox(
        value=get_current_api_key(),
        label="🔑 API Key",
        type="password",
        info="Khóa API để xác thực"
    )
    
    # Models section
    with gr.Row():
        refresh_models_btn = gr.Button("🔄 Lấy models", scale=3)
        clear_cache_btn = gr.Button("🗑️", scale=1)
    
    models_dropdown = gr.Dropdown(
        choices=get_available_models(app_state.selected_provider, get_current_api_key()),
        value=app_state.selected_model,
        label="🤖 Model",
        info="Chọn mô hình LLM"
    )
    
    current_config_text = gr.Textbox(
        value=f"🎯 Đang dùng: {app_state.selected_provider} / {app_state.selected_model}",
        label="Current Configuration",
        interactive=False
    )
    
    # Email Configuration section
    gr.Markdown("### 📧 Thông tin Email")
    
    email_user_input = gr.Textbox(
        value=app_state.email_user,
        label="📮 Gmail",
        info="Địa chỉ Gmail dùng để tự động tải CV"
    )
    
    email_pass_input = gr.Textbox(
        value=app_state.email_pass,
        label="🔐 Mật khẩu",
        type="password",
        info="Mật khẩu hoặc App Password của Gmail"
    )
    
    save_config_btn = gr.Button("💾 Lưu cấu hình")
    email_status_text = gr.Textbox(
        value=get_email_status(),
        label="Email Status",
        interactive=False
    )
    
    return {
        'status_text': status_text,
        'provider_dropdown': provider_dropdown,
        'api_key_input': api_key_input,
        'refresh_models_btn': refresh_models_btn,
        'clear_cache_btn': clear_cache_btn,
        'models_dropdown': models_dropdown,
        'current_config_text': current_config_text,
        'email_user_input': email_user_input,
        'email_pass_input': email_pass_input,
        'save_config_btn': save_config_btn,
        'email_status_text': email_status_text
    }

def get_system_status():
    """Get system status text"""
    config_status = validate_configuration()
    status_lines = []
    for component, status in config_status.items():
        emoji = "✅" if status else "❌"
        status_lines.append(f"{emoji} {component.replace('_', ' ').title()}")
    return "\n".join(status_lines)

def get_current_api_key():
    """Get current API key based on provider"""
    if app_state.selected_provider == "google":
        return app_state.google_api_key
    else:
        return app_state.openrouter_api_key

def get_email_status():
    """Get email connection status"""
    if not app_state.email_user or not app_state.email_pass:
        return "⚠️ Email and password required"
    
    try:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.connect()
        last_uid = fetcher.get_last_processed_uid()
        uid_info = f" | Last UID: {last_uid}" if last_uid else " | No previous UID"
        return f"✅ Email configured{uid_info}"
    except Exception as e:
        return f"⚠️ Email configured but connection failed: {str(e)}"

# ============================================================================
# TAB FUNCTIONS (replicated from tabs/)
# ============================================================================

# FETCH & PROCESS TAB (replicated from fetch_process_tab.py)
def create_fetch_process_tab():
    """Create fetch and process CV tab UI"""
    
    gr.Markdown("## Lấy & Xử lý CV")
    
    # Display current LLM info
    llm_info = get_llm_info_display()
    gr.Markdown(llm_info)
    
    # Date range inputs
    with gr.Row():
        from_date_input = gr.Textbox(
            label="From (DD/MM/YYYY)",
            value="",
            info="Ngày bắt đầu tìm kiếm"
        )
        to_date_input = gr.Textbox(
            label="To (DD/MM/YYYY)", 
            value="",
            placeholder=date.today().strftime("%d/%m/%Y"),
            info="Ngày kết thúc tìm kiếm"
        )
    
    # Checkboxes
    unseen_only_checkbox = gr.Checkbox(
        label="👁️ Chỉ quét email chưa đọc",
        value=app_state.unseen_only,
        info="Nếu bỏ chọn, hệ thống sẽ quét toàn bộ hộp thư"
    )
    
    ignore_uid_checkbox = gr.Checkbox(
        label="🔄 Bỏ qua UID đã lưu (xử lý lại tất cả email)",
        value=False,
        info="Bỏ qua UID đã lưu và xử lý lại tất cả email từ đầu"
    )
    
    # Action buttons
    with gr.Row():
        fetch_btn = gr.Button("📥 Fetch", variant="secondary")
        process_btn = gr.Button("⚙️ Process", variant="secondary") 
        reset_uid_btn = gr.Button("🗑️ Reset UID", variant="secondary")
    
    # Results and status
    operation_status = gr.Textbox(
        label="Trạng thái",
        value="Sẵn sàng",
        interactive=False,
        max_lines=10
    )
    
    # Attachments display
    gr.Markdown("### 📁 File đã tải về")
    attachments_display = gr.HTML(value=get_attachments_html())
    
    # Delete attachments section
    delete_attachments_btn = gr.Button("Xóa toàn bộ attachments", variant="stop")
    delete_status = gr.Textbox(
        label="Delete Status",
        value="",
        interactive=False,
        visible=False
    )
    
    return {
        'from_date_input': from_date_input,
        'to_date_input': to_date_input,
        'unseen_only_checkbox': unseen_only_checkbox,
        'ignore_uid_checkbox': ignore_uid_checkbox,
        'fetch_btn': fetch_btn,
        'process_btn': process_btn,
        'reset_uid_btn': reset_uid_btn,
        'operation_status': operation_status,
        'attachments_display': attachments_display,
        'delete_attachments_btn': delete_attachments_btn,
        'delete_status': delete_status
    }

def get_llm_info_display():
    """Get LLM info display string"""
    try:
        price = get_model_price(app_state.selected_model)
        label = f"{app_state.selected_model} ({price})" if price != "unknown" else app_state.selected_model
        return f"**LLM:** `{app_state.selected_provider}` / `{label}`"
    except Exception:
        return f"**LLM:** `{app_state.selected_provider}` / `{app_state.selected_model}`"

def get_attachments_html():
    """Get HTML for attachments display (replicated from fetch_process_tab.py)"""
    if not MODULES_LOADED:
        return "<p>❌ Modules not loaded</p>"
    
    # Get list of attachment files
    attachments = [
        p for p in ATTACHMENT_DIR.glob("*")
        if p.is_file()
        and p != SENT_TIME_FILE
        and p.suffix.lower() in (".pdf", ".docx")
    ]
    
    if not attachments:
        return "<p>Chưa có CV nào được tải về.</p>"
    
    sent_map = load_sent_times()
    
    # Sort files by sent time (newest first)
    def sort_key(p: Path) -> float:
        ts = sent_map.get(p.name)
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
        return p.stat().st_mtime
    
    attachments.sort(key=sort_key, reverse=True)
    
    # Create download links
    def make_link(path: Path) -> str:
        data = base64.b64encode(path.read_bytes()).decode()
        mime = (
            "application/pdf"
            if path.suffix.lower() == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return f'<a download="{path.name}" href="data:{mime};base64,{data}">{path.name}</a>'
    
    # Create table rows
    rows = []
    for p in attachments:
        sent = format_sent_time_display(sent_map.get(p.name, ""))
        size_kb = p.stat().st_size / 1024
        rows.append({
            "File": make_link(p),
            "Dung lượng": f"{size_kb:.1f} KB",
            "Gửi lúc": sent,
        })
    
    # Create DataFrame and convert to HTML
    df = pd.DataFrame(rows, columns=["File", "Dung lượng", "Gửi lúc"])
    table_html = df.to_html(escape=False, index=False)
    
    return f"""
    <div style='max-height: 400px; overflow: auto; border: 1px solid #ddd; padding: 10px;'>
        {table_html}
    </div>
    """

# SINGLE TAB (replicated from single_tab.py)
def create_single_tab():
    """Create single CV processing tab UI"""
    
    gr.Markdown("## Xử lý một CV đơn lẻ")
    
    # Display current LLM info
    llm_info = get_llm_info_display()
    gr.Markdown(llm_info)
    
    # File upload
    file_upload = gr.File(
        label="Chọn file CV (.pdf, .docx)",
        file_types=[".pdf", ".docx"],
        type="filepath"
    )
    
    # Process button
    process_single_btn = gr.Button("⚙️ Xử lý CV", variant="primary")
    
    # Results display
    single_status = gr.Textbox(
        label="Trạng thái",
        value="Chưa có file nào được chọn",
        interactive=False
    )
    
    single_results = gr.JSON(
        label="Kết quả phân tích",
        value=None
    )
    
    return {
        'file_upload': file_upload,
        'process_single_btn': process_single_btn,
        'single_status': single_status,
        'single_results': single_results
    }

# RESULTS TAB (replicated from results_tab.py)
def create_results_tab():
    """Create results viewing tab UI"""
    
    gr.Markdown("## Xem và tải kết quả")
    
    # Results display
    results_html = gr.HTML(value=get_results_html())
    
    # Download buttons
    with gr.Row():
        download_csv_btn = gr.Button("Tải xuống CSV", variant="secondary")
        download_excel_btn = gr.Button("Tải xuống Excel", variant="secondary")
    
    # Download files
    csv_download = gr.File(
        label="CSV File",
        value=str(OUTPUT_CSV) if OUTPUT_CSV.exists() else None,
        visible=False
    )
    
    excel_download = gr.File(
        label="Excel File", 
        value=str(OUTPUT_EXCEL) if OUTPUT_EXCEL.exists() else None,
        visible=False
    )
    
    return {
        'results_html': results_html,
        'download_csv_btn': download_csv_btn,
        'download_excel_btn': download_excel_btn,
        'csv_download': csv_download,
        'excel_download': excel_download
    }

def get_results_html():
    """Get HTML for results display (replicated from results_tab.py)"""
    if not OUTPUT_CSV.exists():
        return "<p>Chưa có kết quả. Vui lòng chạy Batch hoặc Single.</p>"
    
    try:
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig", keep_default_na=False)
        df.fillna("", inplace=True)
        
        # Create download links for CV files
        def make_link(fname: str) -> str:
            if not fname:
                return ""
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
        
        # Apply links to "Nguồn" column if exists
        if "Nguồn" in df.columns:
            df["Nguồn"] = df["Nguồn"].apply(make_link)
        
        # Wrap content for scrolling
        for col in df.columns:
            df[col] = df[col].apply(
                lambda v: f"<div style='max-width: 300px; word-wrap: break-word;'>{v}</div>" if pd.notna(v) else ""
            )
        
        table_html = df.to_html(escape=False, index=False)
        
        return f"""
        <div style='max-height: 60vh; overflow: auto; border: 1px solid #ddd; padding: 10px;'>
            {table_html}
        </div>
        """
        
    except Exception as e:
        return f"<p>❌ Lỗi đọc kết quả: {e}</p>"

# CHAT TAB (replicated from chat.py)
def create_chat_tab():
    """Create chat tab UI"""
    
    gr.Markdown("## 🤖 Chat với AI - Trợ lý thông minh")
    
    # Dataset info
    dataset_info = load_dataset_for_chat()
    if dataset_info:
        dataset_status = f"✅ Đã tải {dataset_info['count']} CV từ file: `{dataset_info['file']}`\n📅 Last modified: {dataset_info['modified']}"
    else:
        dataset_status = "⚠️ Chưa có dataset CV. Hãy xử lý CV ở tab 'Lấy & Xử lý CV' trước."
    
    gr.Markdown(f"**Dataset Status:** {dataset_status}")
    
    # Chat interface
    chatbot = gr.Chatbot(
        label="Cuộc trò chuyện",
        height=400,
        show_label=True
    )
    
    # Chat input
    with gr.Row():
        chat_input = gr.Textbox(
            label="💬 Nhập câu hỏi của bạn",
            placeholder="Ví dụ: Tóm tắt thông tin các ứng viên có kinh nghiệm AI...",
            scale=4
        )
        send_btn = gr.Button("📨 Gửi", scale=1, variant="primary")
    
    # Chat controls
    with gr.Row():
        export_chat_btn = gr.Button("📥 Xuất chat", scale=1)
        clear_chat_btn = gr.Button("🗑️ Xóa lịch sử", scale=1)
        stats_btn = gr.Button("📊 Thống kê", scale=1)
        help_btn = gr.Button("❓ Hướng dẫn", scale=1)
    
    # Chat help (initially hidden)
    with gr.Accordion("❓ Hướng dẫn sử dụng Chat AI", open=False, visible=False) as chat_help:
        gr.Markdown("""
        ### 📋 Prompt gợi ý
        - "Tóm tắt kinh nghiệm 5 ứng viên hàng đầu cho vị trí Data Scientist"
        - "Liệt kê những ứng viên có trên 3 năm kinh nghiệm Python"
        - "So sánh kỹ năng giữa ứng viên A và B"  
        - "Phân tích điểm mạnh của từng ứng viên"
        - "Gợi ý ứng viên phù hợp cho vị trí Machine Learning Engineer"
        - "Tạo email mời phỏng vấn ứng viên xuất sắc nhất"
        """)
    
    # Chat statistics (initially hidden)
    chat_stats = gr.Textbox(
        label="Thống kê chat",
        value="",
        interactive=False,
        visible=False
    )
    
    return {
        'chatbot': chatbot,
        'chat_input': chat_input,
        'send_btn': send_btn,
        'export_chat_btn': export_chat_btn,
        'clear_chat_btn': clear_chat_btn,
        'stats_btn': stats_btn,
        'help_btn': help_btn,
        'chat_help': chat_help,
        'chat_stats': chat_stats
    }

def load_dataset_for_chat():
    """Load CV dataset for chat context (replicated from chat.py)"""
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

# ============================================================================
# EVENT HANDLERS (Business Logic)
# ============================================================================

def handle_provider_change(provider):
    """Handle provider change"""
    app_state.selected_provider = provider
    api_key = get_current_api_key()
    
    # Update models list
    models = get_available_models(provider, api_key)
    
    # Update current model if not in new list
    if app_state.selected_model not in models and models:
        app_state.selected_model = models[0]
    
    # Detect platform
    platform_info = ""
    if api_key:
        detected = detect_platform(api_key)
        if detected and detected != provider:
            platform_info = f"\n⚠️ API key có vẻ thuộc về {detected}, không phải {provider}"
        elif detected == provider:
            platform_info = f"\n✅ API key hợp lệ cho {provider}"
    
    return (
        gr.Dropdown(choices=models, value=app_state.selected_model),  # models_dropdown
        f"🎯 Đang dùng: {provider} / {app_state.selected_model}{platform_info}",  # current_config_text
        get_llm_info_display()  # Update LLM info in tabs
    )

def handle_api_key_change(api_key):
    """Handle API key change"""
    if app_state.selected_provider == "google":
        app_state.google_api_key = api_key
    else:
        app_state.openrouter_api_key = api_key
    
    # Detect platform
    platform_info = ""
    if api_key:
        detected = detect_platform(api_key)
        if detected and detected != app_state.selected_provider:
            platform_info = f"\n⚠️ API key có vẻ thuộc về {detected}, không phải {app_state.selected_provider}"
        elif detected == app_state.selected_provider:
            platform_info = f"\n✅ API key hợp lệ cho {app_state.selected_provider}"
    
    return f"🎯 Đang dùng: {app_state.selected_provider} / {app_state.selected_model}{platform_info}"

def handle_refresh_models(provider, api_key):
    """Handle refresh models button"""
    if not api_key:
        return (
            gr.Dropdown(choices=[], value=""),
            "⚠️ Vui lòng nhập API Key trước khi lấy models"
        )
    
    models = get_available_models(provider, api_key)
    if models:
        if app_state.selected_model not in models:
            app_state.selected_model = models[0]
        return (
            gr.Dropdown(choices=models, value=app_state.selected_model),
            f"✅ Đã lấy {len(models)} models"
        )
    else:
        return (
            gr.Dropdown(choices=[], value=""),
            "❌ Không thể lấy models"
        )

def handle_model_change(model):
    """Handle model change"""
    app_state.selected_model = model
    return (
        f"🎯 Đang dùng: {app_state.selected_provider} / {model}",
        get_llm_info_display()
    )

def handle_email_config_change(email_user, email_pass):
    """Handle email configuration change"""
    app_state.email_user = email_user
    app_state.email_pass = email_pass
    return get_email_status()

def handle_save_config(provider, api_key, email_user, email_pass):
    """Handle save configuration"""
    try:
        env_path = ROOT / ".env"
        env_path.touch(exist_ok=True)
        load_dotenv(env_path)
        
        set_key(str(env_path), "EMAIL_USER", email_user)
        set_key(str(env_path), "EMAIL_PASS", email_pass)
        set_key(str(env_path), "LLM_PROVIDER", provider)
        
        if provider == "google":
            set_key(str(env_path), "GOOGLE_API_KEY", api_key)
        else:
            set_key(str(env_path), "OPENROUTER_API_KEY", api_key)
        
        return "✅ Đã lưu thông tin email và API vào .env"
    except Exception as e:
        return f"❌ Lỗi khi lưu file .env: {e}"

def handle_fetch_cvs(from_date, to_date, unseen_only, ignore_uid, progress=gr.Progress()):
    """Handle fetch CVs (replicated from fetch_process_tab.py fetch logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", get_attachments_html()
    
    if not app_state.email_user or not app_state.email_pass:
        return "❌ Cần nhập Gmail và mật khẩu trong sidebar để fetch CV.", get_attachments_html()
    
    try:
        progress(0.1, desc="🔌 Đang kết nối email...")
        
        # Parse dates
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.combine(
                    datetime.strptime(from_date, "%d/%m/%Y").date(),
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày From không hợp lệ (DD/MM/YYYY)", get_attachments_html()
        
        if to_date:
            try:
                to_dt = datetime.combine(
                    datetime.strptime(to_date, "%d/%m/%Y").date(),
                    datetime.max.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày To không hợp lệ (DD/MM/YYYY)", get_attachments_html()
        
        since = from_dt.date() if from_dt else None
        before = to_dt.date() if to_dt else None
        
        progress(0.3, desc="📧 Đang khởi tạo fetcher...")
        
        # Create fetcher and connect
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.connect()
        
        progress(0.5, desc="🔍 Đang tìm kiếm email...")
        
        # Fetch CV attachments
        new_files = fetcher.fetch_cv_attachments(
            since=since,
            before=before,
            unseen_only=unseen_only,
            ignore_last_uid=ignore_uid,
        )
        
        progress(1.0, desc="✅ Hoàn thành!")
        
        if new_files:
            file_list = "\n".join([f"- {Path(f).name}" for f in new_files])
            status = f"✅ Đã tải xuống {len(new_files)} file CV mới:\n{file_list}"
            
            # Show new UID
            new_uid = fetcher.get_last_processed_uid()
            if new_uid:
                status += f"\n📧 Updated last processed UID: {new_uid}"
        else:
            status = "📧 Không tìm thấy CV mới để tải về"
        
        return status, get_attachments_html()
        
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return f"❌ Lỗi khi fetch email: {e}", get_attachments_html()

def handle_process_cvs(from_date, to_date, progress=gr.Progress()):
    """Handle process CVs (replicated from fetch_process_tab.py process logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", get_attachments_html()
    
    if not get_current_api_key():
        return "❌ Cần cấu hình API key trước", get_attachments_html()
    
    try:
        progress(0.1, desc="⚙️ Đang khởi tạo xử lý CV...")
        
        # Parse dates for filtering
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.combine(
                    datetime.strptime(from_date, "%d/%m/%Y").date(),
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày From không hợp lệ (DD/MM/YYYY)", get_attachments_html()
        
        if to_date:
            try:
                to_dt = datetime.combine(
                    datetime.strptime(to_date, "%d/%m/%Y").date(),
                    datetime.max.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày To không hợp lệ (DD/MM/YYYY)", get_attachments_html()
        
        progress(0.2, desc="🤖 Đang khởi tạo LLM client...")
        
        # Create LLM client
        llm_client = DynamicLLMClient(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=get_current_api_key()
        )
        
        # Create processor
        processor = CVProcessor(
            fetcher=None,  # No fetch, just process existing files
            llm_client=llm_client,
        )
        
        progress(0.3, desc="📊 Đang xử lý CV...")
        
        # Progress callback
        def progress_callback(current, message):
            progress_value = 0.3 + (current / 100) * 0.6
            progress(progress_value, desc=message)
        
        # Process CVs
        df = processor.process(
            unseen_only=False,  # Process all files in directory
            since=None,  # No email date filtering when processing existing files
            before=None,
            from_time=from_dt,  # Time filtering for processing
            to_time=to_dt,
            progress_callback=progress_callback,
            ignore_last_uid=False,  # Not relevant when fetcher is None
        )
        
        progress(0.9, desc="💾 Đang lưu kết quả...")
        
        if df.empty:
            progress(1.0, desc="📁 Không có CV nào để xử lý")
            return "📁 Không có CV nào trong thư mục attachments để xử lý.", get_attachments_html()
        else:
            # Save results
            processor.save_to_csv(df, str(OUTPUT_CSV))
            processor.save_to_excel(df, str(OUTPUT_EXCEL))
            
            progress(1.0, desc="✅ Xử lý CV hoàn tất!")
            
            logger.info("Đã xử lý %s CV và lưu kết quả", len(df))
            return (
                f"✅ Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`.",
                get_attachments_html()
            )
        
    except Exception as e:
        logger.error(f"Process error: {e}")
        return f"❌ Lỗi khi xử lý CV: {e}", get_attachments_html()

def handle_reset_uid():
    """Handle reset UID"""
    if not app_state.email_user or not app_state.email_pass:
        return "❌ Cần kết nối email trước", get_email_status()
    
    try:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.reset_uid_store()
        return "✅ Đã reset UID store!", get_email_status()
    except Exception as e:
        return f"❌ Lỗi khi reset UID: {e}", get_email_status()

def handle_delete_attachments():
    """Handle delete all attachments"""
    try:
        attachments = list(ATTACHMENT_DIR.iterdir())
        count = sum(1 for f in attachments if f.is_file())
        
        for f in attachments:
            try:
                if f.is_file():
                    f.unlink()
            except Exception:
                pass
        
        logger.info(f"Đã xóa {count} file trong attachments")
        return f"✅ Đã xóa {count} file trong thư mục attachments.", get_attachments_html()
    except Exception as e:
        return f"❌ Lỗi khi xóa file: {e}", get_attachments_html()

def handle_process_single_cv(file_path, progress=gr.Progress()):
    """Handle single CV processing (replicated from single_tab.py)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", None
    
    if not file_path:
        return "❌ Vui lòng chọn file CV", None
    
    if not get_current_api_key():
        return "❌ Cần cấu hình API key trước", None
    
    try:
        progress(0.2, desc="🤖 Đang khởi tạo LLM client...")
        
        # Create LLM client
        llm_client = DynamicLLMClient(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=get_current_api_key()
        )
        
        # Create processor
        processor = CVProcessor(llm_client=llm_client)
        
        progress(0.4, desc="📄 Đang trích xuất text...")
        
        # Extract text
        text = processor.extract_text(file_path)
        
        progress(0.7, desc="🧠 Đang phân tích với LLM...")
        
        # Extract info with LLM
        info = processor.extract_info_with_llm(text)
        
        progress(1.0, desc="✅ Hoàn tất!")
        
        logger.info(f"Xử lý file đơn {Path(file_path).name}")
        
        return f"✅ Đã phân tích CV: {Path(file_path).name}", info
        
    except Exception as e:
        logger.error(f"Single CV processing error: {e}")
        return f"❌ Lỗi khi xử lý CV: {e}", None

def handle_chat_message(message, history):
    """Handle chat message (replicated from chat.py)"""
    if not MODULES_LOADED or not HAS_QA_CHATBOT:
        return history, ""
    
    if not message.strip():
        return history, ""
    
    if not get_current_api_key():
        history.append([message, "❌ API Key chưa được cấu hình!"])
        return history, ""
    
    # Load dataset
    dataset_info = load_dataset_for_chat()
    if not dataset_info or dataset_info.get("data") is None:
        history.append([message, "❌ Chưa có dataset CV để chat. Hãy xử lý CV trước."])
        return history, ""
    
    try:
        df = dataset_info["data"]
        
        # Create chatbot
        chatbot = QAChatbot(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=get_current_api_key()
        )
        
        # Build conversation context
        conversation_context = []
        for user_msg, bot_msg in history[-5:]:  # Last 5 exchanges
            if user_msg:
                conversation_context.append({"role": "user", "content": user_msg})
            if bot_msg:
                conversation_context.append({"role": "assistant", "content": bot_msg})
        
        context = {"history": conversation_context} if conversation_context else None
        
        # Get response
        response = chatbot.ask_question(message, df, context=context)
        
        if response:
            # Update conversation history in app state
            timestamp = datetime.now().isoformat()
            app_state.conversation_history.extend([
                {"role": "user", "content": message, "timestamp": timestamp},
                {"role": "assistant", "content": response, "timestamp": timestamp}
            ])
            
            history.append([message, response])
            logger.info(f"Chat processed successfully. History length: {len(app_state.conversation_history)}")
        else:
            history.append([message, "❌ Không thể lấy phản hồi từ AI. Vui lòng thử lại."])
        
        return history, ""
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        history.append([message, f"❌ Lỗi xử lý chat: {e}"])
        return history, ""

def handle_clear_chat():
    """Handle clear chat history"""
    app_state.conversation_history = []
    return [], "Đã xóa lịch sử chat!"

def handle_export_chat():
    """Handle export chat history"""
    try:
        history = app_state.conversation_history
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
        
        # Save to temporary file for download
        export_file = ROOT / f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        export_file.write_text(export_content, encoding="utf-8")
        
        return str(export_file)
    except Exception as e:
        logger.error(f"Export error: {e}")
        return None

def handle_chat_stats():
    """Handle chat statistics display"""
    history = app_state.conversation_history
    if not history:
        return "Chưa có cuộc trò chuyện nào."
    
    user_messages = len([msg for msg in history if msg["role"] == "user"])
    ai_messages = len([msg for msg in history if msg["role"] == "assistant"])
    first_message = history[0].get("timestamp", "N/A")[:19] if history else "N/A"
    
    stats = f"""
📊 Thống kê chat:
- Tổng tin nhắn: {len(history)}
- Tin nhắn của bạn: {user_messages}
- Phản hồi AI: {ai_messages}
- Bắt đầu lúc: {first_message}
    """
    return stats.strip()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def create_gradio_app():
    """Create the main Gradio application"""
    
    # Custom CSS (similar to Streamlit styling)
    custom_css = f"""
    .gradio-container {{
        background: linear-gradient(135deg, {app_state.background_color} 0%, {app_state.secondary_color}22 100%);
        font-family: 'Be Vietnam Pro', sans-serif;
    }}
    
    .gr-button {{
        background: linear-gradient(135deg, {app_state.accent_color} 0%, {app_state.secondary_color} 100%);
        border: none;
        border-radius: {app_state.border_radius}px;
        box-shadow: 0 4px 15px {app_state.accent_color}33;
        transition: all 0.3s ease;
    }}
    
    .gr-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px {app_state.accent_color}44;
    }}
    
    h1, h2, h3 {{
        color: {app_state.accent_color};
        font-weight: 600;
    }}
    """
    
    with gr.Blocks(
        title="Hoàn Cầu AI CV Processor", 
        css=custom_css,
        theme=gr.themes.Soft()
    ) as app:
        
        # Header
        gr.Markdown("# 🏢 Hoàn Cầu AI CV Processor")
        gr.Markdown("Hệ thống xử lý CV tự động với AI - Phiên bản Gradio")
        
        # Main layout with sidebar and tabs
        with gr.Row():
            # Sidebar (Left column)
            with gr.Column(scale=1, min_width=300):
                sidebar_components = create_sidebar_ui()
            
            # Main content (Right column)
            with gr.Column(scale=3):
                with gr.Tabs():
                    # Tab 1: Fetch & Process
                    with gr.Tab("Lấy & Xử lý CV"):
                        fetch_tab_components = create_fetch_process_tab()
                    
                    # Tab 2: Single File
                    with gr.Tab("Single File"):
                        single_tab_components = create_single_tab()
                    
                    # Tab 3: Results
                    with gr.Tab("Kết quả"):
                        results_tab_components = create_results_tab()
                    
                    # Tab 4: Chat
                    with gr.Tab("Hỏi AI"):
                        chat_tab_components = create_chat_tab()
        
        # Footer
        gr.Markdown("---")
        gr.Markdown(
            f"<center><small>Powered by Hoàn Cầu AI CV Processor | {app_state.selected_provider} / {app_state.selected_model}</small></center>",
            elem_id="footer"
        )
        
        # ======================================================================
        # EVENT BINDINGS
        # ======================================================================
        
        # Sidebar events
        sidebar_components['provider_dropdown'].change(
            handle_provider_change,
            inputs=[sidebar_components['provider_dropdown']],
            outputs=[
                sidebar_components['models_dropdown'],
                sidebar_components['current_config_text']
            ]
        )
        
        sidebar_components['api_key_input'].change(
            handle_api_key_change,
            inputs=[sidebar_components['api_key_input']],
            outputs=[sidebar_components['current_config_text']]
        )
        
        sidebar_components['refresh_models_btn'].click(
            handle_refresh_models,
            inputs=[sidebar_components['provider_dropdown'], sidebar_components['api_key_input']],
            outputs=[sidebar_components['models_dropdown'], sidebar_components['current_config_text']]
        )
        
        sidebar_components['models_dropdown'].change(
            handle_model_change,
            inputs=[sidebar_components['models_dropdown']],
            outputs=[sidebar_components['current_config_text']]
        )
        
        sidebar_components['email_user_input'].change(
            handle_email_config_change,
            inputs=[sidebar_components['email_user_input'], sidebar_components['email_pass_input']],
            outputs=[sidebar_components['email_status_text']]
        )
        
        sidebar_components['email_pass_input'].change(
            handle_email_config_change,
            inputs=[sidebar_components['email_user_input'], sidebar_components['email_pass_input']],
            outputs=[sidebar_components['email_status_text']]
        )
        
        sidebar_components['save_config_btn'].click(
            handle_save_config,
            inputs=[
                sidebar_components['provider_dropdown'],
                sidebar_components['api_key_input'],
                sidebar_components['email_user_input'],
                sidebar_components['email_pass_input']
            ],
            outputs=[sidebar_components['email_status_text']]
        )
        
        # Fetch & Process tab events
        fetch_tab_components['fetch_btn'].click(
            handle_fetch_cvs,
            inputs=[
                fetch_tab_components['from_date_input'],
                fetch_tab_components['to_date_input'],
                fetch_tab_components['unseen_only_checkbox'],
                fetch_tab_components['ignore_uid_checkbox']
            ],
            outputs=[
                fetch_tab_components['operation_status'],
                fetch_tab_components['attachments_display']
            ]
        )
        
        fetch_tab_components['process_btn'].click(
            handle_process_cvs,
            inputs=[
                fetch_tab_components['from_date_input'],
                fetch_tab_components['to_date_input']
            ],
            outputs=[
                fetch_tab_components['operation_status'],
                fetch_tab_components['attachments_display']
            ]
        )
        
        fetch_tab_components['reset_uid_btn'].click(
            handle_reset_uid,
            outputs=[
                fetch_tab_components['operation_status'],
                sidebar_components['email_status_text']
            ]
        )
        
        fetch_tab_components['delete_attachments_btn'].click(
            handle_delete_attachments,
            outputs=[
                fetch_tab_components['operation_status'],
                fetch_tab_components['attachments_display']
            ]
        )
        
        # Single tab events
        single_tab_components['process_single_btn'].click(
            handle_process_single_cv,
            inputs=[single_tab_components['file_upload']],
            outputs=[
                single_tab_components['single_status'],
                single_tab_components['single_results']
            ]
        )
        
        # Results tab events
        results_tab_components['download_csv_btn'].click(
            lambda: str(OUTPUT_CSV) if OUTPUT_CSV.exists() else None,
            outputs=[results_tab_components['csv_download']]
        )
        
        results_tab_components['download_excel_btn'].click(
            lambda: str(OUTPUT_EXCEL) if OUTPUT_EXCEL.exists() else None,
            outputs=[results_tab_components['excel_download']]
        )
        
        # Chat tab events
        chat_tab_components['send_btn'].click(
            handle_chat_message,
            inputs=[chat_tab_components['chat_input'], chat_tab_components['chatbot']],
            outputs=[chat_tab_components['chatbot'], chat_tab_components['chat_input']]
        )
        
        chat_tab_components['chat_input'].submit(
            handle_chat_message,
            inputs=[chat_tab_components['chat_input'], chat_tab_components['chatbot']],
            outputs=[chat_tab_components['chatbot'], chat_tab_components['chat_input']]
        )
        
        chat_tab_components['clear_chat_btn'].click(
            handle_clear_chat,
            outputs=[chat_tab_components['chatbot'], chat_tab_components['chat_stats']]
        )
        
        chat_tab_components['export_chat_btn'].click(
            handle_export_chat,
            outputs=[gr.File(label="Exported Chat")]
        )
        
        chat_tab_components['stats_btn'].click(
            handle_chat_stats,
            outputs=[chat_tab_components['chat_stats']]
        )
        
        # Toggle help visibility
        def toggle_help_visibility(current_state):
            return gr.Accordion(visible=not current_state)
        
        chat_tab_components['help_btn'].click(
            toggle_help_visibility,
            inputs=[chat_tab_components['chat_help']],
            outputs=[chat_tab_components['chat_help']]
        )
    
    return app

def main():
    """Main function to run the Gradio app"""
    if not MODULES_LOADED:
        print("❌ Cannot start app: modules not loaded properly")
        return
    
    print("🚀 Starting Hoàn Cầu AI CV Processor - Gradio Version")
    print(f"📁 Working directory: {ROOT}")
    print(f"📊 Log file: {LOG_FILE}")
    
    # Create and launch app
    app = create_gradio_app()
    
    # Find available port
    import socket
    def find_free_port(start_port=7860):
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return start_port
    
    port = find_free_port(7860)
    
    print(f"🌐 Launching on http://localhost:{port}")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        debug=False,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    main()
