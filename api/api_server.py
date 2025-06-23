# api_server.py - FastAPI server for embeddable API

import os
import sys
from pathlib import Path
import logging
import traceback
from typing import Optional, Dict, Any, List
import asyncio
import tempfile
import json
from datetime import datetime

# Add project root to path
HERE = Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import modules
try:
    from modules.config import LLM_CONFIG, get_models_for_provider
    from modules.cv_processor import CVProcessor
    from modules.llm_client import LLMClient
    from modules.dynamic_llm_client import DynamicLLMClient
    from modules.qa_chatbot import QAChatbot
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="HoanCau AI Resume Processor API",
    description="API for processing resumes and CV analysis",
    version="1.0.0"
)

# CORS middleware - Allow embedding from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="../static"), name="static")

# Pydantic models for API
class CVAnalysisRequest(BaseModel):
    provider: str = "google"
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.3

class ChatRequest(BaseModel):
    message: str
    provider: str = "google"
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7

class CVAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

# Global variables
cv_processor = None
chatbot = None

def initialize_services():
    """Initialize CV processor and chatbot"""
    global cv_processor, chatbot
    try:
        cv_processor = CVProcessor()
        chatbot = QAChatbot()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "cv_processor": cv_processor is not None,
            "chatbot": chatbot is not None
        }
    }

# CV Analysis endpoints
@app.post("/api/analyze-cv", response_model=CVAnalysisResponse)
async def analyze_cv(
    file: UploadFile = File(...),
    provider: str = Form("google"),
    model_name: str = Form("gemini-1.5-flash"),
    temperature: float = Form(0.3)
):
    """Analyze uploaded CV file"""
    start_time = datetime.now()
    
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process CV
        if cv_processor is None:
            raise HTTPException(status_code=500, detail="CV processor not initialized")
        
        # Configure LLM client
        llm_client = DynamicLLMClient(
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )
        
        # Analyze CV
        analysis_result = await asyncio.to_thread(
            cv_processor.process_single_file,
            tmp_file_path,
            llm_client
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CVAnalysisResponse(
            success=True,
            analysis=analysis_result,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CV: {e}")
        logger.error(traceback.format_exc())
        
        # Clean up temp file if exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        return CVAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with AI about CV analysis"""
    try:
        if chatbot is None:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
        
        # Configure LLM client for chat
        llm_client = DynamicLLMClient(
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature
        )
        
        # Get response from chatbot
        response = await asyncio.to_thread(
            chatbot.get_response,
            request.message,
            llm_client
        )
        
        return ChatResponse(
            success=True,
            message=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return ChatResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/models")
async def get_available_models():
    """Get available AI models"""
    try:
        models = {}
        for provider in LLM_CONFIG.keys():
            models[provider] = get_models_for_provider(provider)
        
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Embedded widget endpoint
@app.get("/widget")
async def get_widget():
    """Serve embedded widget HTML"""
    return FileResponse("../widget/widget.html")

@app.get("/widget.js")
async def get_widget_js():
    """Serve widget JavaScript"""
    return FileResponse("../widget/widget.js", media_type="application/javascript")

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services when the app starts"""
    try:
        initialize_services()
        logger.info("API server started successfully")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
