# main_engine/gradio_app.py

import sys
from pathlib import Path
import logging
import traceback
import time
from typing import Optional, Dict, Any, Tuple
import json
from datetime import datetime, date, timezone

# Đưa thư mục gốc (chứa `modules/`) vào sys.path để import modules
HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SRC_DIR = ROOT / "src"
for path in (ROOT, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import gradio as gr
import pandas as pd
import requests
from dotenv import set_key, load_dotenv

# Import cấu hình và modules
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

from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor, format_sent_time_display
from modules.dynamic_llm_client import DynamicLLMClient
from modules.sent_time_store import load_sent_times
from modules.progress_manager import progress_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Global state để lưu trữ thông tin phiên
class AppState:
    def __init__(self):
        self.conversation_history = []
        self.provider = "google"
        self.model = "gemini-2.0-flash-exp"
        self.api_key = ""
        self.email_user = ""
        self.email_pass = ""
        self.available_models = []
        self.last_results = None
        
    def to_dict(self):
        return {
            "conversation_history": self.conversation_history,
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key[:10] + "..." if self.api_key else "",
            "email_user": self.email_user,
            "email_pass": "***" if self.email_pass else "",
            "models_count": len(self.available_models),
        }

# Global app state
app_state = AppState()

# --- Helper Functions ---
def detect_platform(api_key: str) -> Optional[str]:
    """Enhanced platform detection"""
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

    # API-based detection
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

    for platform, url, headers in endpoints.items():
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info(f"API verification successful for platform: {platform}")
                return platform
        except requests.RequestException as e:
            logger.debug(f"API check failed for {platform}: {e}")
            continue

    return None

def get_available_models(provider: str, api_key: str) -> list:
    """Get available models for the provider"""
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

# --- UI Components ---
def update_provider_and_models(provider: str, api_key: str):
    """Update provider and refresh available models"""
    app_state.provider = provider
    app_state.api_key = api_key
    
    if api_key:
        detected_provider = detect_platform(api_key)
        if detected_provider and detected_provider != provider:
            app_state.provider = detected_provider
            provider = detected_provider
        
        save_env_config(f"{provider.upper()}_API_KEY", api_key)
    
    # Get available models
    app_state.available_models = get_available_models(provider, api_key)
    
    if app_state.available_models:
        app_state.model = app_state.available_models[0]
    
    return (
        gr.Dropdown(choices=app_state.available_models, value=app_state.model),
        f"✅ Provider: {provider} | Models: {len(app_state.available_models)}",
        provider
    )

def update_model(model: str):
    """Update selected model"""
    app_state.model = model
    price = get_model_price(model)
    price_text = f" ({price})" if price != "unknown" else ""
    return f"✅ Model: {model}{price_text}"

def update_email_config(email_user: str, email_pass: str):
    """Update email configuration"""
    app_state.email_user = email_user
    app_state.email_pass = email_pass
    
    if email_user:
        save_env_config("EMAIL_USER", email_user)
    if email_pass:
        save_env_config("EMAIL_PASS", email_pass)
    
    status = "✅ Email configured" if email_user and email_pass else "❌ Email not configured"
    return status

def fetch_and_process_cvs(from_date: str, to_date: str, unseen_only: bool, progress=gr.Progress()):
    """Fetch and process CVs from email"""
    try:
        if not app_state.email_user or not app_state.email_pass:
            return "❌ Cần cấu hình email trước", ""
        
        if not app_state.api_key:
            return "❌ Cần cấu hình API key trước", ""
        
        progress(0.1, desc="🔌 Đang kết nối email...")
        
        # Parse dates
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.combine(
                    datetime.strptime(from_date, "%Y-%m-%d").date(),
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày From không hợp lệ (YYYY-MM-DD)", ""
        
        if to_date:
            try:
                to_dt = datetime.combine(
                    datetime.strptime(to_date, "%Y-%m-%d").date(),
                    datetime.max.time(),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                return "❌ Định dạng ngày To không hợp lệ (YYYY-MM-DD)", ""
        
        since = from_dt.date() if from_dt else None
        before = to_dt.date() if to_dt else None
        
        # Create fetcher and processor
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, app_state.email_user, app_state.email_pass)
        fetcher.connect()
        
        llm_client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        
        processor = CVProcessor(fetcher=fetcher, llm_client=llm_client)
        
        progress(0.2, desc="📧 Đang tải emails...")
        
        # Fetch and process with progress tracking
        def progress_callback(current, total, message):
            if total > 0:
                progress_value = 0.2 + (current / total) * 0.8
                progress(progress_value, desc=f"{message} ({current}/{total})")
        
        results = processor.fetch_and_process(
            since=since,
            before=before,
            unseen_only=unseen_only,
            progress_callback=progress_callback
        )
        
        progress(1.0, desc="✅ Hoàn thành!")
        
        app_state.last_results = results
        
        if results.get("processed_count", 0) > 0:
            return (
                f"✅ Xử lý thành công {results['processed_count']} CV từ {results['email_count']} emails",
                load_results_data()
            )
        else:
            return "ℹ️ Không tìm thấy CV nào để xử lý", ""
            
    except Exception as e:
        logger.error(f"Error in fetch_and_process_cvs: {e}")
        return f"❌ Lỗi: {str(e)}", ""

def process_single_cv(file):
    """Process a single CV file"""
    try:
        if not app_state.api_key:
            return "❌ Cần cấu hình API key trước"
        
        if file is None:
            return "❌ Vui lòng chọn file CV"
        
        # Save uploaded file temporarily
        temp_path = ATTACHMENT_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(file.read())
        
        # Process the file
        llm_client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        
        processor = CVProcessor(llm_client=llm_client)
        text = processor.extract_text(str(temp_path))
        info = processor.extract_info_with_llm(text)
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return json.dumps(info, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in process_single_cv: {e}")
        return f"❌ Lỗi xử lý file: {str(e)}"

def load_results_data():
    """Load and format results data for display"""
    try:
        csv_path = Path(OUTPUT_CSV)
        if not csv_path.exists():
            return "Chưa có kết quả nào được lưu."
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if df.empty:
            return "File kết quả trống."
        
        # Format for display
        return df.to_string(index=False, max_rows=50)
        
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return f"Lỗi tải kết quả: {str(e)}"

def chat_with_ai(message: str, history: list):
    """Chat with AI about CV data"""
    try:
        if not app_state.api_key:
            return history, ""
        
        if not message.strip():
            return history, ""
        
        # Load CV data for context
        try:
            csv_path = Path(OUTPUT_CSV)
            context = ""
            if csv_path.exists():
                df = pd.read_csv(csv_path, encoding="utf-8-sig")
                if not df.empty:
                    context = f"Dữ liệu CV hiện có ({len(df)} bản CV):\n{df.to_string(max_rows=10)}\n\n"
        except Exception:
            context = ""
        
        # Create LLM client
        llm_client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        
        # Prepare prompt
        system_prompt = f"""Bạn là trợ lý AI chuyên về phân tích CV và tuyển dụng. 
        {context}
        Hãy trả lời câu hỏi của người dùng dựa trên dữ liệu CV trên (nếu có) và kiến thức chuyên môn của bạn.
        Trả lời bằng tiếng Việt, ngắn gọn và chính xác."""
        
        full_prompt = f"{system_prompt}\n\nCâu hỏi: {message}"
        
        # Get AI response
        response = llm_client.query(full_prompt)
        
        # Update history
        history.append([message, response])
        
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
        
        return history, ""
        
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {e}")
        error_msg = f"❌ Lỗi: {str(e)}"
        history.append([message, error_msg])
        return history, ""

def get_system_status():
    """Get current system status"""
    status = {
        "Provider": app_state.provider,
        "Model": app_state.model,
        "API Key": "✅ Configured" if app_state.api_key else "❌ Not configured",
        "Email": "✅ Configured" if app_state.email_user and app_state.email_pass else "❌ Not configured",
        "Available Models": len(app_state.available_models),
        "Conversation History": len(app_state.conversation_history),
    }
    return "\n".join([f"{k}: {v}" for k, v in status.items()])

# --- Create Gradio Interface ---
def create_interface():
    """Create the main Gradio interface"""
    
    # Custom CSS for styling
    css = """
    .gradio-container {
        font-family: 'Be Vietnam Pro', sans-serif;
        background: linear-gradient(135deg, #fff7e6 0%, #ffeacc 100%);
    }
    .gr-button-primary {
        background: linear-gradient(135deg, #d4af37 0%, #ffeacc 100%);
        border: none;
        color: white;
        font-weight: 600;
    }
    .gr-button-primary:hover {
        background: linear-gradient(135deg, #c19b26 0%, #ffd700 100%);
    }
    .gr-form {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    """
    
    with gr.Blocks(css=css, title="Hoàn Cầu AI CV Processor", theme=gr.themes.Soft()) as app:
        
        # Header
        gr.HTML("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #d4af37 0%, #ffeacc 100%); border-radius: 12px; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    🏢 Hoàn Cầu AI CV Processor
                </h1>
                <p style="color: white; margin: 10px 0 0 0; opacity: 0.9;">Hệ thống xử lý CV thông minh với AI</p>
            </div>
        """)
        
        # Configuration Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>⚙️ Cấu hình hệ thống</h3>")
                
                with gr.Group():
                    gr.HTML("<h4>🤖 LLM Configuration</h4>")
                    provider_dropdown = gr.Dropdown(
                        choices=["google", "openrouter", "vectorshift"],
                        value=app_state.provider,
                        label="Provider",
                        interactive=True
                    )
                    api_key_input = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Nhập API key...",
                        value=app_state.api_key
                    )
                    model_dropdown = gr.Dropdown(
                        choices=app_state.available_models,
                        value=app_state.model,
                        label="Model",
                        interactive=True
                    )
                    provider_status = gr.Textbox(
                        label="Status",
                        interactive=False,
                        value="❌ Chưa cấu hình"
                    )
                
                with gr.Group():
                    gr.HTML("<h4>📧 Email Configuration</h4>")
                    email_user_input = gr.Textbox(
                        label="Gmail",
                        placeholder="your-email@gmail.com",
                        value=app_state.email_user
                    )
                    email_pass_input = gr.Textbox(
                        label="App Password",
                        type="password",
                        placeholder="App password...",
                        value=app_state.email_pass
                    )
                    email_status = gr.Textbox(
                        label="Email Status",
                        interactive=False,
                        value="❌ Chưa cấu hình"
                    )
            
            with gr.Column(scale=1):
                gr.HTML("<h3>📊 System Status</h3>")
                system_status_display = gr.Textbox(
                    label="Current Status",
                    lines=8,
                    interactive=False,
                    value=get_system_status()
                )
                refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
        
        # Main Tabs
        with gr.Tabs():
            
            # Tab 1: Fetch & Process CVs
            with gr.TabItem("📧 Lấy & Xử lý CV"):
                gr.HTML("<h3>📧 Lấy CV từ Email và Xử lý</h3>")
                
                with gr.Row():
                    from_date = gr.Textbox(
                        label="Từ ngày (YYYY-MM-DD)",
                        placeholder="2024-01-01",
                        scale=1
                    )
                    to_date = gr.Textbox(
                        label="Đến ngày (YYYY-MM-DD)", 
                        placeholder=date.today().strftime("%Y-%m-%d"),
                        scale=1
                    )
                
                unseen_only = gr.Checkbox(
                    label="👁️ Chỉ quét email chưa đọc",
                    value=True
                )
                
                fetch_process_btn = gr.Button(
                    "🚀 Fetch & Process CVs",
                    variant="primary",
                    size="lg"
                )
                
                fetch_result = gr.Textbox(
                    label="Kết quả",
                    lines=3,
                    interactive=False
                )
                
                processing_output = gr.Textbox(
                    label="Chi tiết xử lý",
                    lines=10,
                    interactive=False
                )
            
            # Tab 2: Single File Processing
            with gr.TabItem("📄 Single File"):
                gr.HTML("<h3>📄 Xử lý một CV đơn lẻ</h3>")
                
                single_file_upload = gr.File(
                    label="Chọn file CV (.pdf, .docx)",
                    file_types=[".pdf", ".docx"]
                )
                
                process_single_btn = gr.Button(
                    "🔍 Phân tích CV",
                    variant="primary"
                )
                
                single_result = gr.Textbox(
                    label="Kết quả phân tích",
                    lines=15,
                    interactive=False
                )
            
            # Tab 3: Results
            with gr.TabItem("📊 Kết quả"):
                gr.HTML("<h3>📊 Kết quả xử lý CV</h3>")
                
                refresh_results_btn = gr.Button("🔄 Tải lại kết quả")
                
                results_display = gr.Textbox(
                    label="Dữ liệu CV đã xử lý",
                    lines=20,
                    interactive=False,
                    value=load_results_data()
                )
                
                with gr.Row():
                    download_csv_btn = gr.Button("📥 Tải CSV")
                    download_excel_btn = gr.Button("📥 Tải Excel")
            
            # Tab 4: AI Chat
            with gr.TabItem("💬 Hỏi AI"):
                gr.HTML("<h3>💬 Trò chuyện với AI về CV</h3>")
                
                chatbot = gr.Chatbot(
                    label="Cuộc trò chuyện",
                    height=400,
                    placeholder="Bắt đầu cuộc trò chuyện bằng cách gửi tin nhắn bên dưới..."
                )
                
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="Tin nhắn",
                        placeholder="Hỏi về CV, tuyển dụng, hoặc bất kỳ điều gì...",
                        scale=4
                    )
                    send_btn = gr.Button("📤 Gửi", scale=1, variant="primary")
                
                clear_chat_btn = gr.Button("🗑️ Xóa lịch sử chat")
        
        # Event handlers
        
        # Provider and model updates
        api_key_input.change(
            fn=update_provider_and_models,
            inputs=[provider_dropdown, api_key_input],
            outputs=[model_dropdown, provider_status, provider_dropdown]
        )
        
        provider_dropdown.change(
            fn=update_provider_and_models,
            inputs=[provider_dropdown, api_key_input],
            outputs=[model_dropdown, provider_status, provider_dropdown]
        )
        
        model_dropdown.change(
            fn=update_model,
            inputs=[model_dropdown],
            outputs=[provider_status]
        )
        
        # Email configuration
        email_pass_input.change(
            fn=update_email_config,
            inputs=[email_user_input, email_pass_input],
            outputs=[email_status]
        )
        
        # Fetch and process
        fetch_process_btn.click(
            fn=fetch_and_process_cvs,
            inputs=[from_date, to_date, unseen_only],
            outputs=[fetch_result, processing_output]
        )
        
        # Single file processing
        process_single_btn.click(
            fn=process_single_cv,
            inputs=[single_file_upload],
            outputs=[single_result]
        )
        
        # Results
        refresh_results_btn.click(
            fn=load_results_data,
            outputs=[results_display]
        )
        
        # Chat
        send_btn.click(
            fn=chat_with_ai,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        chat_input.submit(
            fn=chat_with_ai,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        clear_chat_btn.click(
            fn=lambda: ([], []),
            outputs=[chatbot, gr.State([])]
        )
        
        # Status refresh
        refresh_status_btn.click(
            fn=get_system_status,
            outputs=[system_status_display]
        )
        
        # Download buttons (placeholder)
        download_csv_btn.click(
            fn=lambda: gr.File(value=OUTPUT_CSV if Path(OUTPUT_CSV).exists() else None),
            outputs=[]
        )
    
    return app

# --- Main Application ---
def main():
    """Main application entry point"""
    logger.info("Starting Gradio CV Processor App")
    
    # Load environment variables
    load_dotenv(ROOT / ".env")
    
    # Initialize app state with environment values
    app_state.api_key = GOOGLE_API_KEY or OPENROUTER_API_KEY or ""
    app_state.email_user = EMAIL_USER or ""
    app_state.email_pass = EMAIL_PASS or ""
    
    # Detect provider from API key
    if app_state.api_key:
        detected_provider = detect_platform(app_state.api_key)
        if detected_provider:
            app_state.provider = detected_provider
        
        # Load available models
        app_state.available_models = get_available_models(app_state.provider, app_state.api_key)
        if app_state.available_models:
            app_state.model = app_state.available_models[0]
    
    # Create and launch interface
    app = create_interface()
    
    # Launch the app
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
