# 🎯 HoanCau AI Resume Processor - Project Documentation

## 📋 Project Overview

The **HoanCau AI Resume Processor** is a comprehensive AI-powered system for fetching, processing, and analyzing CV/resume data from various sources. It combines multiple interfaces (web UI, CLI, API) with advanced LLM capabilities to automate resume processing workflows.

## 🏗️ Project Structure

### Core Components

#### 1. **Main Engine** (`main_engine/`)
- **Primary Interface**: Streamlit-based web application
- **Main Files**:
  - `app.py` - Main Streamlit application with multi-tab interface
  - `main.py` - Alternative entry point
  - `config_info.py` - CLI tool for configuration management
  - `select_top5.py` - Top candidate selection functionality

#### 2. **Modules** (`modules/`)
Core business logic and utilities:
- `config.py` - Configuration management and environment variables
- `cv_processor.py` - PDF/DOCX CV text extraction and AI processing
- `email_fetcher.py` - IMAP email fetching with attachment handling
- `llm_client.py` - LLM API client (Google/OpenRouter)
- `dynamic_llm_client.py` - Dynamic LLM provider switching
- `qa_chatbot.py` - Q&A chatbot for CV data queries
- `model_fetcher.py` - Available model discovery
- `mcp_server.py` - Model Context Protocol server
- `auto_fetcher.py` - Automated CV fetching daemon
- `prompts.py` - LLM prompt templates

#### 3. **Tab Components** (`main_engine/tabs/`)
Web UI tab implementations:
- `chat_tab.py` - AI chat interface for CV queries
- `process_tab.py` - CV processing and analysis
- `fetch_tab.py` - Email fetching interface
- `results_tab.py` - Processing results display
- `single_tab.py` - Single CV processing
- `flow_tab.py` - Processing flow visualization
- `mcp_tab.py` - MCP server management

### Support Files

#### 4. **Scripts & Entry Points**
- `cli_agent.py` - Command-line interface agent
- `simple_app.py` - Simplified Streamlit interface
- `start.sh` - Quick start script with environment setup
- `health_check.py` - System health validation
- `setup.cmd` / `run_resume_ai.cmd` - Windows batch scripts

#### 5. **Configuration & Data**
- `requirements.txt` - Python dependencies
- `flow_config.json` - Processing flow configuration
- `.env` - Environment variables (not in repo)
- `cv_summary.csv` - Processed CV output
- `attachments/` - CV file storage
- `csv/` - CSV data files
- `log/` - Application logs
- `static/` - CSS styles and assets

#### 6. **Testing** (`test/`)
- `test_app.py` - Basic Streamlit test
- `test_cv_processor.py` - CV processing tests
- `test_email_fetcher.py` - Email fetching tests
- `test_models.py` - Model integration tests

## 🚀 Key Features

### AI-Powered Processing
- **Multi-Provider LLM Support**: Google Gemini, OpenRouter models
- **Smart CV Extraction**: PDF/DOCX text extraction with AI parsing
- **Structured Data Output**: JSON/CSV formatted results
- **Question Answering**: Interactive chat about CV data

### Email Integration
- **IMAP Support**: Automated email fetching from Gmail/other providers
- **Attachment Processing**: Automatic CV file detection and download
- **Background Processing**: Daemon mode for continuous monitoring

### User Interfaces
- **Web UI**: Feature-rich Streamlit interface with multiple tabs
- **CLI Interface**: Command-line tools for automation
- **Simple Mode**: Streamlined interface for basic operations

### Advanced Features
- **Theme Customization**: 10+ UI themes with custom styling
- **Export Capabilities**: JSON, CSV, Markdown export options
- **Statistics & Analytics**: Processing metrics and insights
- **Error Handling**: Comprehensive error management and logging
- **Health Monitoring**: System validation and diagnostics

## 📊 Current Status

### Recent Improvements (Based on Fix Reports)
- ✅ **Chat Tab Enhancement**: Fixed `NameError` issues and enhanced chat interface
- ✅ **UI/UX Upgrades**: Modern themes, responsive design, improved styling
- ✅ **Error Handling**: Comprehensive error management with retry logic
- ✅ **Stability Improvements**: Session state management and resilience features
- ✅ **AI Processing**: Enhanced prompts and context management

### Documentation Files
- `FIX_REPORT.md` - Chat tab functionality fixes
- `CHAT_TAB_FIX_REPORT.md` - Detailed chat enhancement report
- `UPGRADE_REPORT.md` - Comprehensive system upgrades (236 lines)
- `SYNC_GUIDE.md` - Git synchronization instructions
- `readme.md` - Main project documentation

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.12+** - Primary language
- **Streamlit** - Web UI framework
- **Pandas** - Data processing
- **Click** - CLI framework
- **FastAPI/Uvicorn** - API server capabilities

### AI/ML Libraries
- **Google AI SDK** - Gemini model integration
- **OpenRouter API** - Multi-model access
- **Custom LLM Clients** - Abstracted model interaction

### Document Processing
- **PDFMiner/PyPDF2/PyMuPDF** - PDF text extraction
- **python-docx** - DOCX file processing
- **Regex & NLP** - Text parsing and extraction

### Infrastructure
- **IMAP** - Email integration
- **JSON/CSV** - Data serialization
- **Logging** - Application monitoring
- **Environment Management** - Configuration handling

## 🎯 Use Cases

1. **HR Departments**: Automated CV screening and candidate analysis
2. **Recruitment Agencies**: Bulk CV processing and matching
3. **Individual Recruiters**: CV organization and search capabilities
4. **Career Services**: Resume analysis and feedback
5. **Research**: CV data analysis and insights

## 📈 Future Considerations

Based on the current structure, potential areas for expansion:
- API-first architecture for external integrations
- Machine learning model training on CV data
- Advanced matching algorithms
- Integration with job posting platforms
- Real-time collaboration features
- Mobile application development

## 🔧 Development Setup

The project includes comprehensive setup scripts:
- `start.sh` - Automated environment setup and launch
- `health_check.py` - System validation
- Virtual environment management
- Dependency installation automation

This project represents a mature, production-ready system for automated resume processing with extensive documentation, error handling, and multiple interface options.
