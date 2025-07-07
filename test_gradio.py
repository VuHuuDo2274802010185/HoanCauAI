#!/usr/bin/env python3
"""
Simple Gradio test app for HoanCau AI CV Processor
"""

import sys
from pathlib import Path
import gradio as gr

# Add project root to path
HERE = Path(__file__).parent
ROOT = HERE.parent
SRC_DIR = ROOT / "src"

for path in (ROOT, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

def test_function(text):
    """Simple test function"""
    return f"✅ Test successful! Input: {text}"

def create_test_interface():
    """Create a simple test interface"""
    with gr.Blocks(title="HoanCau AI CV Processor - Gradio Test") as app:
        gr.HTML("<h1>🏢 Hoàn Cầu AI CV Processor - Gradio Test</h1>")
        
        with gr.Row():
            input_text = gr.Textbox(label="Test Input", placeholder="Enter test text...")
            output_text = gr.Textbox(label="Test Output")
        
        test_btn = gr.Button("🧪 Test", variant="primary")
        
        test_btn.click(
            fn=test_function,
            inputs=[input_text],
            outputs=[output_text]
        )
    
    return app

def main():
    """Main entry point"""
    print("🚀 Starting Gradio test interface...")
    
    app = create_test_interface()
    
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
