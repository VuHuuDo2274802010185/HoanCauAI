#!/usr/bin/env python3
"""
Full-featured Gradio app for HoanCau AI CV Processor
Complete logic and presentation replication from Streamlit app
"""

import sys
from pathlib import Path
import logging
import json
import time
import base64
import os
import requests
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, Tuple, List

# Add project root to path
HERE = Path(__file__).parent
ROOT = HERE
SRC_DIR = ROOT / "src"

# Ensure proper Python path setup for modules
for path in (ROOT, SRC_DIR):
    path_str = str(path.absolute())
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

try:
    import gradio as gr
    import pandas as pd
    from dotenv import load_dotenv, set_key
    
    # Import project modules (same structure as Streamlit)
    from src.modules.config import (
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
    
    from src.modules.dynamic_llm_client import DynamicLLMClient
    from src.modules.cv_processor import CVProcessor, format_sent_time_display
    from src.modules.email_fetcher import EmailFetcher
    from src.modules.sent_time_store import load_sent_times
    from src.modules.progress_manager import GradioProgressBar
    
    # Import QA chatbot if available
    try:
        from src.modules.qa_chatbot import QAChatbot
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

# Global application state (mirroring Streamlit session state functionality)
class AppState:
    def __init__(self):
        # Initialize with same defaults as Streamlit app
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
        
        # LLM Configuration (from sidebar state)
        self.selected_provider = "google"
        self.selected_model = LLM_CONFIG.get("model", "gemini-2.0-flash-exp")
        self.google_api_key = GOOGLE_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.available_models = []
        
        # Email Configuration (from sidebar state)
        self.email_user = EMAIL_USER
        self.email_pass = EMAIL_PASS
        self.unseen_only = EMAIL_UNSEEN_ONLY
        
        # UI state flags (from session state)
        self.confirm_delete = False
        self.show_chat_stats = False
        self.show_chat_help = False
        self.enhanced_log_handler_installed = False
        
        # Caching mechanism for models (like Streamlit session state)
        self.models_cache = {}
        self.last_uid_info = ""

# Global app state (replaces st.session_state)
app_state = AppState()

# --- Helper Functions (mirrored from Streamlit) ---

def validate_configuration() -> Dict[str, bool]:
    """Validate application configuration (same as Streamlit app)"""
    config_status = {
        "env_file": (ROOT / ".env").exists(),
        "config_module": True,
        "static_files": (ROOT / "static").exists(),
        "modules": True,
    }
    
    # Check if required modules are importable
    try:
        import src.modules.qa_chatbot
        config_status["qa_module"] = True
    except ImportError:
        config_status["qa_module"] = False
    
    return config_status

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
            import requests
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info(f"API verification successful for platform: {platform}")
                return platform
        except Exception as e:
            logger.debug(f"API check failed for {platform}: {e}")
            continue

    logger.warning(f"Could not detect platform for API key: {api_key[:10]}...")
    return None

def get_available_models(provider: str, api_key: str) -> list:
    """Get available models with caching and error handling"""
    try:
        models = get_models_for_provider(provider, api_key)
        if models:
            logger.info(f"Retrieved {len(models)} models for {provider}")
            return models
    except Exception as e:
        logger.error(f"Failed to get models for {provider}: {e}")

    # Fallback to default model
    default_model = LLM_CONFIG.get("model", "gemini-2.0-flash-exp")
    return [default_model]

def save_env_config(key: str, value: str):
    """Save configuration to .env file"""
    try:
        env_path = ROOT / ".env"
        set_key(str(env_path), key, value)
        logger.info(f"Saved {key} to .env file")
    except Exception as e:
        logger.error(f"Failed to save {key} to .env: {e}")

# --- Core Processing Functions (replicating Streamlit tab logic) ---

def update_llm_config(provider: str, api_key: str, model: str = None):
    """Update LLM configuration (from Streamlit sidebar logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", gr.Dropdown(choices=[]), provider, ""
    
    # Update state (mimics Streamlit session state)
    app_state.selected_provider = provider
    
    # Set API key based on provider
    if provider == "google":
        app_state.google_api_key = api_key
    else:
        app_state.openrouter_api_key = api_key
    
    if api_key:
        # Detect platform (same logic as Streamlit)
        detected_provider = detect_platform(api_key)
        if detected_provider and detected_provider != provider:
            provider = detected_provider
            app_state.selected_provider = detected_provider
        
        # Save to .env (same as Streamlit)
        save_env_config(f"{provider.upper()}_API_KEY", api_key)
        
        # Get available models with caching (same as Streamlit)
        cache_key = f"models_{provider}_{hash(api_key) if api_key else 'none'}"
        cached_models = app_state.models_cache.get(cache_key, None)
        
        # Use cached models if available and recent (5 minutes cache like Streamlit)
        if cached_models and isinstance(cached_models, dict):
            cache_time = cached_models.get("timestamp", 0)
            if time.time() - cache_time < 300:
                app_state.available_models = cached_models.get("models", [])
            else:
                app_state.available_models = get_available_models(provider, api_key)
                app_state.models_cache[cache_key] = {
                    "models": app_state.available_models,
                    "timestamp": time.time()
                }
        else:
            app_state.available_models = get_available_models(provider, api_key)
            app_state.models_cache[cache_key] = {
                "models": app_state.available_models,
                "timestamp": time.time()
            }
        
        # Set default model if not provided or not in list
        if not model or model not in app_state.available_models:
            if app_state.available_models:
                app_state.selected_model = app_state.available_models[0]
            else:
                app_state.selected_model = LLM_CONFIG.get("model", "gemini-2.0-flash-exp")
        else:
            app_state.selected_model = model
        
        # Format price display (same as Streamlit)
        price = get_model_price(app_state.selected_model)
        price_text = f" ({price})" if price != "unknown" else ""
        
        status_msg = f"✅ LLM configured: {provider}/{app_state.selected_model}{price_text}"
        
        return (
            status_msg,
            gr.Dropdown(choices=app_state.available_models, value=app_state.selected_model),
            provider,
            f"{provider}/{app_state.selected_model}{price_text}"
        )
    else:
        return "⚠️ API key is required", gr.Dropdown(choices=[]), provider, ""

def clear_models_cache():
    """Clear models cache (like Streamlit cache clear)"""
    app_state.models_cache.clear()
    return "Cache cleared", gr.Dropdown(choices=[])

def update_email_config(email_user: str, email_pass: str):
    """Update email configuration (from Streamlit sidebar logic)"""
    app_state.email_user = email_user
    app_state.email_pass = email_pass
    
    # Save to .env (same as Streamlit)
    if email_user:
        save_env_config("EMAIL_USER", email_user)
    if email_pass:
        save_env_config("EMAIL_PASS", email_pass)
    
    if email_user and email_pass:
        # Test connection (same as Streamlit)
        try:
            fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
            fetcher.connect()
            last_uid = fetcher.get_last_processed_uid()
            uid_info = f" | Last UID: {last_uid}" if last_uid else " | No previous UID"
            app_state.last_uid_info = uid_info
            return f"✅ Email configured{uid_info}"
        except Exception as e:
            return f"⚠️ Email configured but connection failed: {str(e)}"
    else:
        return "⚠️ Email and password required"

def fetch_cvs_from_email(from_date: str, to_date: str, unseen_only: bool, ignore_last_uid: bool, progress=gr.Progress()):
    """Fetch CVs from email (replicating Streamlit fetch logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", ""
    
    if not app_state.email_user or not app_state.email_pass:
        return "❌ Cần cấu hình email trước", ""
    
    try:
        progress(0.1, desc="🔌 Đang kết nối email...")
        
        # Parse dates with same format as Streamlit (DD/MM/YYYY)
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.combine(
                    datetime.strptime(from_date, "%d/%m/%Y").date(),
                    datetime.min.time,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày From không hợp lệ (DD/MM/YYYY)", ""
        
        if to_date:
            try:
                to_dt = datetime.combine(
                    datetime.strptime(to_date, "%d/%m/%Y").date(),
                    datetime.max.time,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày To không hợp lệ (DD/MM/YYYY)", ""
        
        since = from_dt.date() if from_dt else None
        before = to_dt.date() if to_dt else None
        
        progress(0.3, desc="📧 Đang khởi tạo fetcher...")
        
        # Create fetcher (same as Streamlit)
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.connect()
        
        # Handle ignore_last_uid option (same as Streamlit)
        if ignore_last_uid:
            fetcher.reset_uid_store()
        
        progress(0.5, desc="📥 Đang tải email...")
        
        # Fetch CV attachments (same logic as Streamlit)
        new_files = fetcher.fetch_cv_attachments(
            since=since,
            before=before,
            unseen_only=unseen_only,
            ignore_last_uid=ignore_last_uid,
        )
        
        progress(1.0, desc="✅ Hoàn thành fetch!")
        
        # Format results (same as Streamlit)
        if new_files:
            result_text = f"✅ Đã tải xuống {len(new_files)} file CV mới:"
            file_list = ""
            for file_path in new_files:
                file_list += f"- {Path(file_path).name}\n"
            
            # Update UID info (same as Streamlit)
            new_uid = fetcher.get_last_processed_uid()
            if new_uid:
                result_text += f"\n📧 Updated last processed UID: {new_uid}"
                app_state.last_uid_info = f" | Last UID: {new_uid}"
            
            return result_text, file_list
        else:
            return "📧 Không tìm thấy CV mới để tải về", ""
            
    except Exception as e:
        logger.error(f"Error in fetch_cvs_from_email: {e}")
        return f"❌ Lỗi khi fetch email: {str(e)}", ""

def process_cvs(from_date: str, to_date: str, progress=gr.Progress()):
    """Process CVs from attachments folder (replicating Streamlit process logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly", "", ""
    
    if not app_state.selected_provider or not (app_state.google_api_key or app_state.openrouter_api_key):
        return "❌ Cần cấu hình LLM trước", "", ""
    
    try:
        progress(0.1, desc="⚙️ Đang khởi tạo xử lý CV...")
        
        # Parse dates for filtering (same logic as Streamlit)
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.combine(
                    datetime.strptime(from_date, "%d/%m/%Y").date(),
                    datetime.min.time,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày From không hợp lệ (DD/MM/YYYY)", "", ""
        
        if to_date:
            try:
                to_dt = datetime.combine(
                    datetime.strptime(to_date, "%d/%m/%Y").date(),
                    datetime.max.time,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày To không hợp lệ (DD/MM/YYYY)", "", ""
        
        # Get API key based on provider
        api_key = app_state.google_api_key if app_state.selected_provider == "google" else app_state.openrouter_api_key
        
        # Create LLM client (same as Streamlit)
        llm_client = DynamicLLMClient(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=api_key
        )
        
        progress(0.3, desc="🤖 Đang khởi tạo CV processor...")
        
        # Create processor (same as Streamlit)
        processor = CVProcessor(
            fetcher=None,  # No fetch, just process existing files
            llm_client=llm_client
        )
        
        # Progress callback for processor
        def progress_callback(current, total, message):
            if total > 0:
                progress_value = 0.3 + (current / total) * 0.6
                progress(progress_value, desc=f"{message} ({current}/{total})")
        
        progress(0.4, desc="📊 Đang xử lý CV...")
        
        # Process CVs (same logic as Streamlit)
        df_results = processor.process(
            unseen_only=False,  # Process all files in attachments folder
            since=None,  # Don't filter by email date when processing files
            before=None,
            from_time=from_dt,  # Filter by time range for processing
            to_time=to_dt,
            progress_callback=progress_callback,
            ignore_last_uid=False,  # Not relevant when fetcher is None
        )
        
        progress(0.9, desc="💾 Đang lưu kết quả...")
        
        # Save results (same as Streamlit)
        if not df_results.empty:
            processor.save_to_csv(df_results, str(OUTPUT_CSV))
            processor.save_to_excel(df_results, str(OUTPUT_EXCEL))
            
            processed_count = len(df_results)
            
            progress(1.0, desc="✅ Hoàn thành!")
            
            result_text = f"✅ Đã xử lý {processed_count} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`"
            
            return result_text, load_results_data(), load_processing_logs()
        else:
            progress(1.0, desc="ℹ️ Không tìm thấy CV")
            return "📁 Không có CV nào trong thư mục attachments để xử lý.", "", ""
            
    except Exception as e:
        logger.error(f"Error in process_cvs: {e}")
        return f"❌ Lỗi xử lý CV: {str(e)}", "", ""

def reset_uid_store():
    """Reset UID store (same as Streamlit reset logic)"""
    if not app_state.email_user or not app_state.email_pass:
        return "❌ Cần kết nối email trước"
    
    try:
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.connect()
        fetcher.reset_uid_store()
        app_state.last_uid_info = " | No previous UID"
        return "✅ Đã reset UID store!"
    except Exception as e:
        return f"❌ Lỗi reset UID: {str(e)}"

def get_attachments_list():
    """Get list of attachments with download links (same as Streamlit display)"""
    # Get list of attachment files (same logic as Streamlit)
    attachments = [
        p for p in ATTACHMENT_DIR.glob("*")
        if p.is_file()
        and p != SENT_TIME_FILE
        and p.suffix.lower() in (".pdf", ".docx")
    ]
    
    if not attachments:
        return "Chưa có CV nào được tải về."
    
    # Load sent times map (same as Streamlit)
    sent_map = load_sent_times()
    
    # Sort by time function (same as Streamlit)
    def sort_key(p: Path) -> float:
        ts = sent_map.get(p.name)
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
        return p.stat().st_mtime
    
    # Sort files by time descending (newest first) - same as Streamlit
    attachments.sort(key=sort_key, reverse=True)
    
    # Create attachment list HTML (simplified version of Streamlit table)
    html_content = "<div style='max-height: 300px; overflow-y: auto;'>"
    html_content += "<table style='width: 100%; border-collapse: collapse;'>"
    html_content += "<tr style='background-color: #f0f0f0;'><th style='padding: 8px; border: 1px solid #ddd;'>File</th><th style='padding: 8px; border: 1px solid #ddd;'>Dung lượng</th><th style='padding: 8px; border: 1px solid #ddd;'>Gửi lúc</th></tr>"
    
    for p in attachments:
        sent_time = format_sent_time_display(sent_map.get(p.name, ""))
        size_kb = p.stat().st_size / 1024
        
        # Create download data URL
        data = base64.b64encode(p.read_bytes()).decode()
        mime = "application/pdf" if p.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        download_link = f'<a href="data:{mime};base64,{data}" download="{p.name}" style="text-decoration: none; color: #0066cc;">{p.name}</a>'
        
        html_content += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{download_link}</td><td style='padding: 8px; border: 1px solid #ddd;'>{size_kb:.1f} KB</td><td style='padding: 8px; border: 1px solid #ddd;'>{sent_time}</td></tr>"
    
    html_content += "</table></div>"
    
    return html_content

def delete_all_attachments():
    """Delete all attachments (same logic as Streamlit)"""
    try:
        attachments = list(ATTACHMENT_DIR.iterdir())
        count = sum(1 for f in attachments if f.is_file())
        
        # Delete all files (same as Streamlit)
        for f in attachments:
            try:
                if f.is_file():
                    f.unlink()
            except Exception:
                pass
        
        logger.info(f"Đã xóa {count} file trong attachments")
        return f"✅ Đã xóa {count} file trong thư mục attachments.", get_attachments_list()
    except Exception as e:
        return f"❌ Lỗi xóa file: {str(e)}", get_attachments_list()

def load_results_data():
    """Load and format results data for display (from results_tab)"""
    try:
        csv_path = Path(OUTPUT_CSV)
        if not csv_path.exists():
            return "Chưa có kết quả nào được lưu."
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if df.empty:
            return "File kết quả trống."
        
        # Format for display with summary
        summary = f"📊 **Tổng quan kết quả:**\n"
        summary += f"- Tổng số CV: {len(df)}\n"
        summary += f"- File: {csv_path.name}\n"
        summary += f"- Cập nhật: {datetime.fromtimestamp(csv_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Display data table
        summary += "📋 **Chi tiết dữ liệu:**\n\n"
        summary += df.to_string(index=False, max_rows=50)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return f"Lỗi tải kết quả: {str(e)}"

def load_processing_logs():
    """Load processing logs for display"""
    try:
        logs = app_state.logs[-20:]  # Last 20 logs
        if not logs:
            return "Chưa có log xử lý nào."
        
        log_text = "📋 **Log xử lý gần đây:**\n\n"
        for log_entry in logs:
            if isinstance(log_entry, dict):
                timestamp = log_entry.get("timestamp", "")
                level = log_entry.get("level", "INFO")
                message = log_entry.get("message", "")
                log_text += f"[{timestamp}] {level}: {message}\n"
            else:
                log_text += f"{log_entry}\n"
        
        return log_text
        
    except Exception as e:
        return f"Lỗi tải logs: {str(e)}"

def chat_with_ai(message: str, history: list):
    """Chat with AI about CV data (from chat_tab logic)"""
    if not MODULES_LOADED:
        new_msg = {"role": "assistant", "content": "❌ Modules not loaded properly"}
        return history + [{"role": "user", "content": message}, new_msg], ""
    
    api_key = app_state.google_api_key if app_state.selected_provider == "google" else app_state.openrouter_api_key
    if not api_key:
        new_msg = {"role": "assistant", "content": "❌ Please configure LLM first"}
        return history + [{"role": "user", "content": message}, new_msg], ""
    
    if not message.strip():
        return history, ""
    
    try:
        # Load CV data for context (like Streamlit chat)
        try:
            csv_path = Path(OUTPUT_CSV)
            context = ""
            if csv_path.exists():
                df = pd.read_csv(csv_path, encoding="utf-8-sig")
                if not df.empty:
                    context = f"Dữ liệu CV hiện có ({len(df)} bản CV):\n{df.head(10).to_string()}\n\n"
        except Exception:
            context = ""
        
        # Create LLM client
        client = DynamicLLMClient(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=api_key
        )
        
        # Prepare prompt (similar to Streamlit chat logic)
        system_prompt = f"""Bạn là trợ lý AI chuyên về phân tích CV và tuyển dụng của Hoàn Cầu Group. 
        {context}
        Hãy trả lời câu hỏi của người dùng dựa trên dữ liệu CV trên (nếu có) và kiến thức chuyên môn của bạn.
        Trả lời bằng tiếng Việt, chuyên nghiệp và hữu ích."""
        
        full_prompt = f"{system_prompt}\n\nCâu hỏi: {message}"
        
        # Get AI response
        response = client.query(full_prompt)
        
        # Update conversation history in app state
        app_state.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        app_state.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update history with message format
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ]
        return new_history, ""
        
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {e}")
        error_msg = f"❌ Lỗi: {str(e)}"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ]
        return new_history, ""

def get_system_status():
    """Get current system status (from Streamlit app status display)"""
    config_status = validate_configuration()
    
    status_text = "📊 **Trạng thái hệ thống:**\n\n"
    
    # System components
    for component, status in config_status.items():
        emoji = "✅" if status else "❌"
        status_text += f"{emoji} {component.replace('_', ' ').title()}\n"
    
    status_text += "\n🤖 **Cấu hình LLM:**\n"
    status_text += f"- Provider: {app_state.selected_provider}\n"
    status_text += f"- Model: {app_state.selected_model}\n"
    api_key = app_state.google_api_key if app_state.selected_provider == "google" else app_state.openrouter_api_key
    status_text += f"- API Key: {'✅ Configured' if api_key else '❌ Not configured'}\n"
    status_text += f"- Available Models: {len(app_state.available_models)}\n"
    
    status_text += "\n📧 **Cấu hình Email:**\n"
    status_text += f"- Email: {'✅ Configured' if app_state.email_user else '❌ Not configured'}\n"
    status_text += f"- Password: {'✅ Configured' if app_state.email_pass else '❌ Not configured'}\n"
    
    status_text += "\n💬 **Chat History:**\n"
    status_text += f"- Messages: {len(app_state.conversation_history)}\n"
    status_text += f"- Errors: {app_state.error_count}\n"
    
    return status_text

# --- Create Gradio Interface (mirroring exact Streamlit layout and behavior) ---

def create_gradio_interface():
    """Create the main Gradio interface replicating Streamlit app exactly"""
    
    # Load environment variables (same as Streamlit app initialization)
    load_dotenv(ROOT / ".env")
    
    # Initialize API keys from environment
    app_state.google_api_key = GOOGLE_API_KEY or ""
    app_state.openrouter_api_key = OPENROUTER_API_KEY or ""
    app_state.email_user = EMAIL_USER or ""
    app_state.email_pass = EMAIL_PASS or ""
    
    # Detect provider from existing API keys (same logic as Streamlit)
    if app_state.google_api_key:
        app_state.selected_provider = "google"
        detected_provider = detect_platform(app_state.google_api_key)
        if detected_provider:
            app_state.selected_provider = detected_provider
    elif app_state.openrouter_api_key:
        app_state.selected_provider = "openrouter"
        detected_provider = detect_platform(app_state.openrouter_api_key)
        if detected_provider:
            app_state.selected_provider = detected_provider
    
    # Load available models if we have API key
    current_api_key = app_state.google_api_key if app_state.selected_provider == "google" else app_state.openrouter_api_key
    if current_api_key:
        app_state.available_models = get_available_models(app_state.selected_provider, current_api_key)
        if app_state.available_models:
            app_state.selected_model = app_state.available_models[0]
    
    # Custom CSS (enhanced from Streamlit styling with same color scheme)
    css = f"""
    .gradio-container {{
        font-family: 'Be Vietnam Pro', sans-serif;
        background: linear-gradient(135deg, {app_state.background_color} 0%, {app_state.secondary_color}22 100%);
        min-height: 100vh;
    }}
    .gr-button-primary {{
        background: linear-gradient(135deg, {app_state.accent_color} 0%, {app_state.secondary_color} 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: {app_state.border_radius}px !important;
        box-shadow: 0 4px 15px {app_state.accent_color}33 !important;
        transition: all 0.3s ease !important;
    }}
    .gr-button-primary:hover {{
        background: linear-gradient(135deg, #c19b26 0%, #ffd700 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px {app_state.accent_color}44 !important;
    }}
    .gr-form {{
        background: linear-gradient(135deg, {app_state.background_color}aa 0%, {app_state.secondary_color}22 100%) !important;
        border: 2px solid {app_state.secondary_color}66 !important;
        border-radius: {app_state.border_radius}px !important;
        padding: 1rem !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
    }}
    .gr-textbox, .gr-dropdown {{
        background-color: {app_state.background_color} !important;
        color: {app_state.text_color} !important;
        border: 2px solid {app_state.secondary_color} !important;
        border-radius: {app_state.border_radius}px !important;
    }}
    .gr-textbox:focus, .gr-dropdown:focus {{
        border-color: {app_state.accent_color} !important;
        box-shadow: 0 0 0 2px {app_state.accent_color}33 !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {app_state.accent_color} !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px {app_state.accent_color}22 !important;
    }}
    .sidebar {{
        background: linear-gradient(180deg, {app_state.background_color} 0%, {app_state.secondary_color}33 100%) !important;
        border-right: 2px solid {app_state.accent_color}22 !important;
    }}
    """
    
    with gr.Blocks(
        css=css,
        title="Hoàn Cầu AI CV Processor",
        theme=gr.themes.Soft()
    ) as app:
        
        # Header (same as Streamlit page title)
        gr.HTML(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {app_state.accent_color} 0%, {app_state.secondary_color} 100%); border-radius: 12px; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    🏢 Hoàn Cầu AI CV Processor
                </h1>
                <p style="color: white; margin: 10px 0 0 0; opacity: 0.9;">Hệ thống xử lý CV thông minh với AI - Enhanced Gradio Version</p>
            </div>
        """)
        
        # Layout: Sidebar + Main Content (exact same structure as Streamlit)
        with gr.Row():
            # Left Sidebar (replicating st.sidebar exactly)
            with gr.Column(scale=1, elem_classes=["sidebar"]):
                # Logo display (same as Streamlit sidebar)
                logo_path = ROOT / "static" / "logo.png"
                if logo_path.exists():
                    gr.Image(str(logo_path), height=120, show_label=False, container=False)
                else:
                    gr.HTML("<h3>🏢 Hoàn Cầu AI CV Processor</h3>")
                
                # System Status Section (same as Streamlit expandable status)
                with gr.Accordion("📊 Trạng thái hệ thống", open=False):
                    system_status_display = gr.HTML(
                        value=get_system_status(),
                        elem_id="system_status"
                    )
                    refresh_status_btn = gr.Button("🔄 Refresh", size="sm")
                
                gr.Markdown("### ⚙️ Cấu hình LLM")
                
                # LLM Configuration (exact same as Streamlit sidebar)
                provider_dropdown = gr.Dropdown(
                    choices=["google", "openrouter"],
                    value=app_state.selected_provider,
                    label="🔧 Provider",
                    interactive=True,
                    info="Chọn nhà cung cấp LLM"
                )
                
                # API Key input that changes based on provider (same logic as Streamlit)
                api_key_input = gr.Textbox(
                    label="🔑 API Key",
                    type="password",
                    value=current_api_key,
                    placeholder="Nhập API key...",
                    lines=1,
                    info="Khóa API để xác thực với LLM"
                )
                
                # Model management buttons (same as Streamlit two-column layout)
                with gr.Row():
                    refresh_models_btn = gr.Button("🔄 Lấy models", scale=2, size="sm")
                    clear_cache_btn = gr.Button("🗑️", scale=1, size="sm")
                
                model_dropdown = gr.Dropdown(
                    choices=app_state.available_models,
                    value=app_state.selected_model,
                    label="🤖 Model",
                    interactive=True,
                    info="Chọn mô hình LLM"
                )
                
                # LLM Status display
                llm_status_display = gr.HTML(
                    value=f"**🎯 Đang dùng:** `{app_state.selected_provider}` / `{app_state.selected_model}`"
                )
                
                gr.Markdown("### 📧 Thông tin Email")
                
                # Email Configuration (same as Streamlit sidebar)
                email_user_input = gr.Textbox(
                    label="Gmail",
                    value=app_state.email_user,
                    placeholder="your-email@gmail.com",
                    lines=1,
                    info="Tài khoản Gmail"
                )
                email_pass_input = gr.Textbox(
                    label="App Password",
                    type="password",
                    value=app_state.email_pass,
                    placeholder="Gmail app password...",
                    lines=1,
                    info="Mật khẩu ứng dụng Gmail"
                )
                email_status = gr.HTML(
                    value="⚠️ Chưa cấu hình" + app_state.last_uid_info
                )
                test_email_btn = gr.Button("📧 Test Email", variant="secondary")
            
            # Main Content Area (same structure as Streamlit main area)
            with gr.Column(scale=2):
                # Main Tabs (exact same as Streamlit tabs)
                with gr.Tabs():
                    
                    # Tab 1: Lấy & Xử lý CV (exact replica of Streamlit fetch_process_tab)
                    with gr.TabItem("📧 Lấy & Xử lý CV"):
                        gr.HTML("<h3>📧 Lấy CV từ Email và Xử lý</h3>")
                        
                        # Current LLM display (same as Streamlit)
                        current_llm_display = gr.HTML(
                            value=f"**LLM:** `{app_state.selected_provider}` / `{app_state.selected_model}`"
                        )
                        
                        # Date range inputs (same as Streamlit columns)
                        with gr.Row():
                            from_date = gr.Textbox(
                                label="From (DD/MM/YYYY)",
                                placeholder="01/01/2024",
                                scale=1,
                                info="Ngày bắt đầu tìm kiếm"
                            )
                            to_date = gr.Textbox(
                                label="To (DD/MM/YYYY)", 
                                placeholder=date.today().strftime("%d/%m/%Y"),
                                scale=1,
                                info="Ngày kết thúc tìm kiếm"
                            )
                        
                        # Options (same as Streamlit checkboxes)
                        unseen_only = gr.Checkbox(
                            label="👁️ Chỉ quét email chưa đọc",
                            value=EMAIL_UNSEEN_ONLY,
                            info="Nếu bỏ chọn, hệ thống sẽ quét toàn bộ hộp thư"
                        )
                        ignore_last_uid = gr.Checkbox(
                            label="🔄 Bỏ qua UID đã lưu (xử lý lại tất cả email)",
                            value=False,
                            info="Bỏ qua UID đã lưu và xử lý lại tất cả email từ đầu"
                        )
                        
                        gr.HTML("<hr>")
                        
                        # Action buttons (same as Streamlit 3-column layout)
                        with gr.Row():
                            fetch_btn = gr.Button(
                                "📥 Fetch",
                                variant="primary",
                                scale=1
                            )
                            process_btn = gr.Button(
                                "⚙️ Process",
                                variant="primary",
                                scale=1
                            )
                            reset_uid_btn = gr.Button(
                                "🔄 Reset UID",
                                variant="secondary",
                                scale=1
                            )
                        
                        # Results display
                        fetch_result = gr.HTML(
                            label="Kết quả",
                            value="",
                            visible=True
                        )
                        
                        # Attachments section (same as Streamlit attachments display)
                        gr.HTML("<h4>📁 CV Attachments</h4>")
                        attachments_display = gr.HTML(
                            value=get_attachments_list(),
                            label="CV đã tải về"
                        )
                        
                        # Delete all attachments section (same as Streamlit confirm delete logic)
                        with gr.Row():
                            delete_all_btn = gr.Button(
                                "🗑️ Xóa toàn bộ attachments",
                                variant="stop",
                                scale=1
                            )
                        
                        # Confirmation dialog will be handled via gr.State
                        delete_confirm_state = gr.State(False)
                    
                    # Tab 2: Single File (exact replica of Streamlit single_tab)
                    with gr.TabItem("📄 Single File"):
                        gr.HTML("<h3>📄 Xử lý một CV đơn lẻ</h3>")
                        
                        # LLM info display (same as Streamlit)
                        single_llm_display = gr.HTML(
                            value=f"**LLM:** `{app_state.selected_provider}` / `{app_state.selected_model}`"
                        )
                        
                        # File upload (same as Streamlit file uploader)
                        single_file_upload = gr.File(
                            label="Chọn file CV (.pdf, .docx)",
                            file_types=[".pdf", ".docx"],
                            file_count="single"
                        )
                        
                        process_single_btn = gr.Button(
                            "🔍 Phân tích CV",
                            variant="primary"
                        )
                        
                        single_result = gr.HTML(
                            label="Kết quả phân tích",
                            value="",
                            elem_id="single_result"
                        )
                    
                    # Tab 3: Kết quả (exact replica of Streamlit results_tab)
                    with gr.TabItem("📊 Kết quả"):
                        gr.HTML("<h3>📊 Kết quả xử lý CV</h3>")
                        
                        # Action buttons (same as Streamlit results tab)
                        with gr.Row():
                            refresh_results_btn = gr.Button("🔄 Tải lại kết quả", scale=1)
                            download_csv_btn = gr.DownloadButton(
                                "📥 Tải CSV",
                                value=str(OUTPUT_CSV) if OUTPUT_CSV.exists() else None,
                                scale=1
                            )
                            download_excel_btn = gr.DownloadButton(
                                "📥 Tải Excel",
                                value=str(OUTPUT_EXCEL) if OUTPUT_EXCEL.exists() else None,
                                scale=1
                            )
                        
                        results_display = gr.HTML(
                            label="Dữ liệu CV đã xử lý",
                            value=load_results_data(),
                            elem_id="results_display"
                        )
                    
                    # Tab 4: Hỏi AI (exact replica of Streamlit chat_tab)
                    with gr.TabItem("💬 Hỏi AI"):
                        gr.HTML("<h3>💬 Trò chuyện với AI về CV</h3>")
                        
                        # Chat interface (same structure as Streamlit chat)
                        chatbot = gr.Chatbot(
                            label="Cuộc trò chuyện",
                            height=500,
                            type="messages",
                            placeholder="Bắt đầu cuộc trò chuyện bằng cách gửi tin nhắn bên dưới...",
                            elem_id="chatbot"
                        )
                        
                        with gr.Row():
                            chat_input = gr.Textbox(
                                label="Tin nhắn",
                                placeholder="Hỏi về CV, tuyển dụng, hoặc bất kỳ điều gì...",
                                scale=4,
                                lines=2
                            )
                            send_btn = gr.Button("📤 Gửi", scale=1, variant="primary")
                        
                        # Chat controls (same as Streamlit chat controls)
                        with gr.Row():
                            clear_chat_btn = gr.Button("🗑️ Xóa lịch sử chat", scale=1)
                            save_chat_btn = gr.Button("💾 Lưu cuộc trò chuyện", scale=1)
        
        # Create components dictionary for event binding
        components = {
            "provider_dropdown": provider_dropdown,
            "api_key_input": api_key_input,
            "model_dropdown": model_dropdown,
            "refresh_models_btn": refresh_models_btn,
            "clear_cache_btn": clear_cache_btn,
            "llm_status_display": llm_status_display,
            "email_user_input": email_user_input,
            "email_pass_input": email_pass_input,
            "email_status": email_status,
            "test_email_btn": test_email_btn,
            "current_llm_display": current_llm_display,
            "from_date": from_date,
            "to_date": to_date,
            "unseen_only": unseen_only,
            "ignore_last_uid": ignore_last_uid,
            "fetch_btn": fetch_btn,
            "process_btn": process_btn,
            "reset_uid_btn": reset_uid_btn,
            "fetch_result": fetch_result,
            "attachments_display": attachments_display,
            "delete_all_btn": delete_all_btn,
            "single_llm_display": single_llm_display,
            "single_file_upload": single_file_upload,
            "process_single_btn": process_single_btn,
            "single_result": single_result,
            "refresh_results_btn": refresh_results_btn,
            "results_display": results_display,
            "chatbot": chatbot,
            "chat_input": chat_input,
            "send_btn": send_btn,
            "clear_chat_btn": clear_chat_btn,
            "save_chat_btn": save_chat_btn,
            "system_status_display": system_status_display,
            "refresh_status_btn": refresh_status_btn,
        }
        
        # Setup event handlers inside the Blocks context
        setup_event_handlers(components)
        
        return app, components

# --- Event Handler Functions ---

def process_cvs_handler(from_date: str, to_date: str):
    """Handler for process CVs button"""
    result, results_data, logs = process_cvs(from_date, to_date)
    return result, results_data, ""  # Return empty string for third output

def fetch_cvs_handler(from_date: str, to_date: str, unseen_only: bool, ignore_last_uid: bool):
    """Handler for fetch CVs button"""
    result, file_list = fetch_cvs_from_email(from_date, to_date, unseen_only, ignore_last_uid)
    attachments_html = get_attachments_list()
    return result, "", attachments_html  # Return empty string for second output

def process_single_cv(file):
    """Process a single CV file (from Streamlit single_tab logic)"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly"
    
    api_key = app_state.google_api_key if app_state.selected_provider == "google" else app_state.openrouter_api_key
    if not api_key:
        return "❌ Cần cấu hình LLM trước"
    
    if file is None:
        return "❌ Vui lòng chọn file CV"
    
    try:
        # Save uploaded file temporarily
        temp_path = ATTACHMENT_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(file.read())
        
        # Create LLM client (same as Streamlit)
        llm_client = DynamicLLMClient(
            provider=app_state.selected_provider,
            model=app_state.selected_model,
            api_key=api_key
        )
        
        # Process file (same logic as Streamlit)
        processor = CVProcessor(llm_client=llm_client)
        text = processor.extract_text(str(temp_path))
        info = processor.extract_info_with_llm(text)
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        # Format output like Streamlit
        price = get_model_price(app_state.selected_model)
        label = f"{app_state.selected_model} ({price})" if price != "unknown" else app_state.selected_model
        
        result = f"**LLM:** `{app_state.selected_provider}` / `{label}`\n\n"
        result += f"**File:** {file.name}\n\n"
        result += "**Kết quả phân tích:**\n\n"
        result += json.dumps(info, indent=2, ensure_ascii=False)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_single_cv: {e}")
        return f"❌ Lỗi xử lý file: {str(e)}"

def setup_event_handlers(components):
    """Setup all event handlers (replicating Streamlit interaction logic exactly)"""
    
    # LLM Configuration Events (same logic as Streamlit sidebar)
    components["provider_dropdown"].change(
        fn=lambda provider, api_key, model: update_llm_config(provider, api_key, model),
        inputs=[components["provider_dropdown"], components["api_key_input"], components["model_dropdown"]],
        outputs=[components["llm_status_display"], components["model_dropdown"], components["provider_dropdown"], components["current_llm_display"]]
    )
    
    components["api_key_input"].change(
        fn=lambda provider, api_key, model: update_llm_config(provider, api_key, model),
        inputs=[components["provider_dropdown"], components["api_key_input"], components["model_dropdown"]],
        outputs=[components["llm_status_display"], components["model_dropdown"], components["provider_dropdown"], components["current_llm_display"]]
    )
    
    components["refresh_models_btn"].click(
        fn=lambda provider, api_key, model: update_llm_config(provider, api_key, model),
        inputs=[components["provider_dropdown"], components["api_key_input"], components["model_dropdown"]],
        outputs=[components["llm_status_display"], components["model_dropdown"], components["provider_dropdown"], components["current_llm_display"]]
    )
    
    components["clear_cache_btn"].click(
        fn=clear_models_cache,
        outputs=[components["llm_status_display"], components["model_dropdown"]]
    )
    
    # Email Configuration Events (same logic as Streamlit sidebar)
    components["test_email_btn"].click(
        fn=update_email_config,
        inputs=[components["email_user_input"], components["email_pass_input"]],
        outputs=[components["email_status"]]
    )
    
    components["email_user_input"].change(
        fn=update_email_config,
        inputs=[components["email_user_input"], components["email_pass_input"]],
        outputs=[components["email_status"]]
    )
    
    components["email_pass_input"].change(
        fn=update_email_config,
        inputs=[components["email_user_input"], components["email_pass_input"]],
        outputs=[components["email_status"]]
    )
    
    # Fetch and Process Events (same logic as Streamlit fetch_process_tab)
    components["fetch_btn"].click(
        fn=fetch_cvs_handler,
        inputs=[components["from_date"], components["to_date"], components["unseen_only"], components["ignore_last_uid"]],
        outputs=[components["fetch_result"], gr.HTML(visible=False), components["attachments_display"]]  # Use HTML for file list
    )
    
    components["process_btn"].click(
        fn=process_cvs_handler,
        inputs=[components["from_date"], components["to_date"]],
        outputs=[components["fetch_result"], components["results_display"], gr.HTML(visible=False)]  # Use results_display for process output
    )
    
    components["reset_uid_btn"].click(
        fn=lambda: (reset_uid_store(), get_attachments_list()),
        outputs=[components["fetch_result"], components["attachments_display"]]
    )
    
    # Delete attachments event (same logic as Streamlit confirm delete)
    components["delete_all_btn"].click(
        fn=delete_all_attachments,
        outputs=[components["fetch_result"], components["attachments_display"]]
    )
    
    # Single File Processing Events (same logic as Streamlit single_tab)
    components["process_single_btn"].click(
        fn=process_single_cv,
        inputs=[components["single_file_upload"]],
        outputs=[components["single_result"]]
    )
    
    # Results Tab Events (same logic as Streamlit results_tab)
    components["refresh_results_btn"].click(
        fn=load_results_data,
        outputs=[components["results_display"]]
    )
    
    # Chat Events (same logic as Streamlit chat_tab)
    components["send_btn"].click(
        fn=chat_with_ai,
        inputs=[components["chat_input"], components["chatbot"]],
        outputs=[components["chatbot"], components["chat_input"]]
    )
    
    components["chat_input"].submit(
        fn=chat_with_ai,
        inputs=[components["chat_input"], components["chatbot"]],
        outputs=[components["chatbot"], components["chat_input"]]
    )
    
    components["clear_chat_btn"].click(
        fn=lambda: ([], ""),
        outputs=[components["chatbot"], components["chat_input"]]
    )
    
    components["save_chat_btn"].click(
        fn=lambda history: save_chat_history(history),
        inputs=[components["chatbot"]],
        outputs=[components["fetch_result"]]  # Show save result in fetch_result
    )
    
    # System Status Events
    components["refresh_status_btn"].click(
        fn=get_system_status,
        outputs=[components["system_status_display"]]
    )

def save_chat_history(history):
    """Save chat history to file (same as Streamlit chat save functionality)"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chat_file = ROOT / f"chat_history_{timestamp}.json"
        
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        return f"✅ Đã lưu cuộc trò chuyện vào {chat_file.name}"
    except Exception as e:
        return f"❌ Lỗi lưu cuộc trò chuyện: {str(e)}"

# --- Main Application ---
def main():
    """Main application entry point"""
    logger.info("Starting Full-Featured Gradio CV Processor App")
    
    if not MODULES_LOADED:
        print("❌ Could not load required modules. Please check your installation.")
        print("Run: pip install -r requirements.txt")
        return
    
    try:
        # Create interface and get components
        app, components = create_gradio_interface()
        
        print("✅ Full Gradio interface created successfully!")
        print("🌐 Starting server...")
        
        # Launch the app (same configuration approach as other Gradio apps)
        app.launch(
            server_name="0.0.0.0",
            server_port=7863,  # Different port from simple version
            share=False,
            debug=True,
            show_error=True,
            inbrowser=True,
            favicon_path=str(ROOT / "static" / "logo.png") if (ROOT / "static" / "logo.png").exists() else None
        )
        
    except Exception as e:
        logger.error(f"Failed to start Gradio app: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
