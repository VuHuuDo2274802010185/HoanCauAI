#!/usr/bin/env python3
"""
Simplified Gradio app for HoanCau AI CV Processor
"""

import sys
from pathlib import Path
import logging
import json
from datetime import datetime, date
from typing import Optional, Tuple

# Add project root to path
HERE = Path(__file__).parent
ROOT = HERE
SRC_DIR = ROOT / "src"

# Ensure proper Python path setup
for path in (ROOT, SRC_DIR):
    path_str = str(path.absolute())
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

print(f"🔍 Debug: ROOT = {ROOT}")
print(f"🔍 Debug: SRC_DIR = {SRC_DIR}")
print(f"🔍 Debug: SRC_DIR exists = {SRC_DIR.exists()}")
print(f"🔍 Debug: modules exists = {(SRC_DIR / 'modules').exists()}")
print(f"🔍 Debug: Python path first 3: {sys.path[:3]}")

try:
    import gradio as gr
    import pandas as pd
    from dotenv import load_dotenv
    
    # Test import step by step
    print("📦 Importing modules...")
    
    # Import project modules with error handling
    try:
        from modules.config import (
            LLM_CONFIG,
            get_models_for_provider,
            get_model_price,
            OUTPUT_CSV,
            GOOGLE_API_KEY,
            OPENROUTER_API_KEY,
            EMAIL_USER,
            EMAIL_PASS,
            ATTACHMENT_DIR,
        )
        print("✅ Config imported")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        raise
    
    try:
        from modules.dynamic_llm_client import DynamicLLMClient
        print("✅ LLM client imported")
    except ImportError as e:
        print(f"❌ LLM client import failed: {e}")
        raise
        
    try:
        from modules.cv_processor import CVProcessor
        print("✅ CV processor imported")
    except ImportError as e:
        print(f"❌ CV processor import failed: {e}")
        raise
        
    try:
        from modules.email_fetcher import EmailFetcher
        print("✅ Email fetcher imported")
    except ImportError as e:
        print(f"❌ Email fetcher import failed: {e}")
        raise
    
    MODULES_LOADED = True
    print("✅ All modules loaded successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    MODULES_LOADED = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAppState:
    """Simple app state management"""
    def __init__(self):
        self.provider = "google"
        self.model = "gemini-2.0-flash-exp"
        self.api_key = ""
        self.email_user = ""
        self.email_pass = ""
        self.conversation_history = []

# Global state
app_state = SimpleAppState()

def update_llm_config(provider: str, api_key: str, model: str):
    """Update LLM configuration"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly"
    
    app_state.provider = provider
    app_state.api_key = api_key
    app_state.model = model
    
    if api_key:
        try:
            # Test the configuration
            client = DynamicLLMClient(provider=provider, model=model, api_key=api_key)
            # Simple test query
            response = client.query("Test query - just respond with 'OK'")
            return f"✅ LLM configured: {provider}/{model} - Test response: {response[:50]}..."
        except Exception as e:
            return f"❌ LLM configuration error: {str(e)}"
    else:
        return "⚠️ API key is required"

def update_email_config(email_user: str, email_pass: str):
    """Update email configuration"""
    app_state.email_user = email_user
    app_state.email_pass = email_pass
    
    if email_user and email_pass:
        return "✅ Email configured"
    else:
        return "⚠️ Email and password required"

def process_single_file(file):
    """Process a single CV file"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly"
    
    if not app_state.api_key:
        return "❌ Please configure LLM first"
    
    if file is None:
        return "❌ Please select a file"
    
    try:
        # Save file temporarily
        temp_path = ATTACHMENT_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file content
        with open(temp_path, "wb") as f:
            if hasattr(file, 'read'):
                f.write(file.read())
            else:
                # Handle file path
                with open(file, "rb") as src:
                    f.write(src.read())
        
        # Process file
        client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        processor = CVProcessor(llm_client=client)
        
        # Extract and analyze
        text = processor.extract_text(str(temp_path))
        info = processor.extract_info_with_llm(text)
        
        # Cleanup
        temp_path.unlink(missing_ok=True)
        
        return json.dumps(info, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return f"❌ Error: {str(e)}"

def simple_fetch_emails(from_date: str, to_date: str):
    """Simple email fetching function"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly"
    
    if not app_state.email_user or not app_state.email_pass:
        return "❌ Please configure email first"
    
    if not app_state.api_key:
        return "❌ Please configure LLM first"
    
    try:
        # Create fetcher
        fetcher = EmailFetcher(
            "imap.gmail.com", 993, 
            app_state.email_user, 
            app_state.email_pass
        )
        fetcher.connect()
        
        # Create processor
        client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        processor = CVProcessor(fetcher=fetcher, llm_client=client)
        
        # Simple processing - use the correct method name
        df_results = processor.process(
            since=datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None,
            before=datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None,
            unseen_only=True
        )
        
        # Save results
        if not df_results.empty:
            processor.save_to_csv(df_results)
            processor.save_to_excel(df_results)
            
            processed_count = len(df_results)
            return f"✅ Processed {processed_count} CVs successfully"
        else:
            return "ℹ️ No CVs found to process"
        
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return f"❌ Error: {str(e)}"

def load_results():
    """Load processing results"""
    if not MODULES_LOADED:
        return "❌ Modules not loaded properly"
    
    try:
        csv_path = Path(OUTPUT_CSV)
        if not csv_path.exists():
            return "No results file found"
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if df.empty:
            return "Results file is empty"
        
        return df.to_string(index=False, max_rows=20)
        
    except Exception as e:
        return f"Error loading results: {str(e)}"

def chat_with_ai(message: str, history: list):
    """Simple chat with AI"""
    if not MODULES_LOADED:
        new_msg = {"role": "assistant", "content": "❌ Modules not loaded properly"}
        return history + [{"role": "user", "content": message}, new_msg], ""
    
    if not app_state.api_key:
        new_msg = {"role": "assistant", "content": "❌ Please configure LLM first"}
        return history + [{"role": "user", "content": message}, new_msg], ""
    
    if not message.strip():
        return history, ""
    
    try:
        client = DynamicLLMClient(
            provider=app_state.provider,
            model=app_state.model,
            api_key=app_state.api_key
        )
        
        # Simple prompt
        prompt = f"""You are a helpful AI assistant for CV analysis and recruitment.
        
        User question: {message}
        
        Please provide a helpful response in Vietnamese."""
        
        response = client.query(prompt)
        
        # Update history with message format
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ]
        return new_history, ""
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ]
        return new_history, ""

def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Load environment
    load_dotenv(ROOT / ".env")
    app_state.api_key = GOOGLE_API_KEY or OPENROUTER_API_KEY or ""
    app_state.email_user = EMAIL_USER or ""
    app_state.email_pass = EMAIL_PASS or ""
    
    with gr.Blocks(
        title="Hoàn Cầu AI CV Processor",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            font-family: 'Be Vietnam Pro', sans-serif;
        }
        .gr-button-primary {
            background: linear-gradient(135deg, #d4af37 0%, #ffeacc 100%) !important;
            border: none !important;
        }
        """
    ) as app:
        
        # Header
        gr.HTML("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #d4af37 0%, #ffeacc 100%); border-radius: 12px; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0;">🏢 Hoàn Cầu AI CV Processor</h1>
                <p style="color: white; margin: 10px 0 0 0;">Hệ thống xử lý CV thông minh với AI - Gradio Version</p>
            </div>
        """)
        
        with gr.Row():
            # Configuration Column
            with gr.Column(scale=1):
                gr.HTML("<h3>⚙️ Configuration</h3>")
                
                # LLM Config
                with gr.Group():
                    gr.HTML("<h4>🤖 LLM Settings</h4>")
                    provider = gr.Dropdown(
                        ["google", "openrouter", "vectorshift"],
                        value=app_state.provider,
                        label="Provider"
                    )
                    api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        value=app_state.api_key,
                        placeholder="Enter your API key..."
                    )
                    model = gr.Textbox(
                        label="Model",
                        value=app_state.model,
                        placeholder="e.g., gemini-2.0-flash-exp"
                    )
                    llm_status = gr.Textbox(
                        label="LLM Status",
                        interactive=False,
                        value="⚠️ Not configured"
                    )
                    test_llm_btn = gr.Button("🧪 Test LLM Config", variant="secondary")
                
                # Email Config
                with gr.Group():
                    gr.HTML("<h4>📧 Email Settings</h4>")
                    email_user = gr.Textbox(
                        label="Gmail",
                        value=app_state.email_user,
                        placeholder="your-email@gmail.com"
                    )
                    email_pass = gr.Textbox(
                        label="App Password",
                        type="password",
                        value=app_state.email_pass,
                        placeholder="Gmail app password..."
                    )
                    email_status = gr.Textbox(
                        label="Email Status",
                        interactive=False,
                        value="⚠️ Not configured"
                    )
                    test_email_btn = gr.Button("📧 Update Email Config", variant="secondary")
            
            # Status Column
            with gr.Column(scale=1):
                gr.HTML("<h3>📊 System Info</h3>")
                
                system_info = gr.HTML(f"""
                    <div style="background: #f0f0f0; padding: 15px; border-radius: 8px;">
                        <p><strong>📍 Project Root:</strong> {ROOT}</p>
                        <p><strong>🐍 Python Path:</strong> {sys.executable}</p>
                        <p><strong>📦 Modules Loaded:</strong> {'✅ Yes' if MODULES_LOADED else '❌ No'}</p>
                        <p><strong>🕐 Started:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                """)
        
        # Main Tabs
        with gr.Tabs():
            # Email Processing Tab
            with gr.TabItem("📧 Email & CV Processing"):
                gr.HTML("<h3>📧 Fetch and Process CVs from Email</h3>")
                
                with gr.Row():
                    from_date = gr.Textbox(
                        label="From Date (YYYY-MM-DD)",
                        placeholder="2024-01-01"
                    )
                    to_date = gr.Textbox(
                        label="To Date (YYYY-MM-DD)",
                        value=date.today().strftime("%Y-%m-%d")
                    )
                
                fetch_btn = gr.Button("🚀 Fetch & Process", variant="primary", size="lg")
                fetch_result = gr.Textbox(
                    label="Result",
                    lines=5,
                    interactive=False
                )
            
            # Single File Tab
            with gr.TabItem("📄 Single File"):
                gr.HTML("<h3>📄 Process Single CV File</h3>")
                
                file_upload = gr.File(
                    label="Upload CV File",
                    file_types=[".pdf", ".docx"]
                )
                process_btn = gr.Button("🔍 Process CV", variant="primary")
                file_result = gr.Textbox(
                    label="Analysis Result",
                    lines=15,
                    interactive=False
                )
            
            # Results Tab
            with gr.TabItem("📊 Results"):
                gr.HTML("<h3>📊 Processing Results</h3>")
                
                refresh_btn = gr.Button("🔄 Refresh Results")
                results_display = gr.Textbox(
                    label="CV Data",
                    lines=20,
                    interactive=False,
                    value=load_results()
                )
            
            # Chat Tab
            with gr.TabItem("💬 AI Chat"):
                gr.HTML("<h3>💬 Chat with AI about CVs</h3>")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    type="messages"  # Use modern message format
                )
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="Message",
                        placeholder="Ask about CVs, recruitment, etc...",
                        scale=4
                    )
                    send_btn = gr.Button("📤 Send", scale=1, variant="primary")
                
                clear_btn = gr.Button("🗑️ Clear Chat")
        
        # Event Handlers
        test_llm_btn.click(
            fn=update_llm_config,
            inputs=[provider, api_key, model],
            outputs=[llm_status]
        )
        
        test_email_btn.click(
            fn=update_email_config,
            inputs=[email_user, email_pass],
            outputs=[email_status]
        )
        
        fetch_btn.click(
            fn=simple_fetch_emails,
            inputs=[from_date, to_date],
            outputs=[fetch_result]
        )
        
        process_btn.click(
            fn=process_single_file,
            inputs=[file_upload],
            outputs=[file_result]
        )
        
        refresh_btn.click(
            fn=load_results,
            outputs=[results_display]
        )
        
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
        
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, chat_input]
        )
    
    return app

def main():
    """Main entry point"""
    logger.info("🚀 Starting Simplified Gradio CV Processor...")
    
    if not MODULES_LOADED:
        print("❌ Could not load required modules. Please check your installation.")
        print("Run: pip install -r requirements.txt")
        return
    
    try:
        app = create_gradio_interface()
        
        print("✅ Gradio interface created successfully!")
        print("🌐 Starting server...")
        
        app.launch(
            server_name="0.0.0.0",
            server_port=7862,  # Try different port
            share=False,
            debug=True,
            show_error=True,
            inbrowser=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Gradio app: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
