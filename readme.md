# HoanCau AI Resume Processor

HoanCau AI là bộ công cụ tự động trích xuất thông tin từ CV (.pdf, .docx) và hỗ trợ hỏi đáp trên dữ liệu đã xử lý. Ứng dụng có thể chạy qua CLI, giao diện web Streamlit hoặc API FastAPI.

## Tính năng chính
- Tải CV tự động từ tài khoản email IMAP
- Trích xuất thông tin qua LLM (Google Gemini/OpenRouter) với cơ chế fallback
- Lưu kết quả sang CSV và Excel
- Hỏi đáp thông tin tuyển dụng dựa trên dữ liệu đã xử lý
- Cung cấp API MCP server để tích hợp hệ thống khác

## Cài đặt nhanh
```bash
# Clone mã nguồn
git clone <repo_url>
cd HoanCauAI

# Tạo virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Cài các gói cần thiết
pip install -r requirements.txt
```

Copy file `.env.example` thành `.env` và điền các khoá API cần thiết (ví dụ `GOOGLE_API_KEY` hoặc `OPENROUTER_API_KEY`, `EMAIL_USER`, `EMAIL_PASS`).

## Sử dụng
### Chạy giao diện web
```bash
streamlit run src/main_engine/app.py
```

### Chạy CLI
```bash
python scripts/cli_agent.py --help
```

### Chạy MCP server (FastAPI)
```bash
uvicorn modules.mcp_server:app --reload
```

## Chạy test
```bash
pip install -r requirements-dev.txt
pytest
```

## License
Phần mềm phát hành theo giấy phép MIT.
