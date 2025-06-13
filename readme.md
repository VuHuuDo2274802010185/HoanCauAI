# README.md

## 🧠 Trình Trích Xuất Thông Tin CV - phiên bản MCP Server

Ứng dụng này hoạt động như một server backend (MCP), cung cấp các API để một AI Agent có thể ra lệnh thực hiện việc đọc, trích xuất thông tin từ CV (.pdf, .docx) bằng Google Gemini.

---

## 🏗️ Cấu trúc dự án
```
.
├── mcp_server.py # API Server chính (FastAPI)
├── main.py # Script chạy từ command-line
├── modules/
│ ├── config.py
│ ├── cv_processor.py
│ ├── email_fetcher.py
│ └── prompts.py
├── attachments/ # Lưu các file CV tải về
├── cv_summary.csv # Kết quả trích xuất
├── .env
└── requirements.txt
```

---

## 🚀 Hướng dẫn cài đặt

### 1. Clone và cài đặt thư viện
```bash
uv venv venv
uv pip install -r requirements.txt
```

### 2. Tạo file .env
```
GOOGLE_API_KEY=your_gemini_api_key
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

### 3. Chạy ứng dụng
``` bash Chế độ API Server (dành cho AI Agent)
uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload

Sau đó, truy cập http://localhost:8000/docs để xem tài liệu API tương tác.
```
Chế độ Command-line (chạy 1 lần)

```python main.py```

### ✨ Các API Endpoint chính
POST /run-full-process: Kích hoạt toàn bộ quy trình: quét email, tải CV, xử lý AI, lưu ra file CSV.

GET /results: Tải về file cv_summary.csv.

POST /process-single-cv: Upload một file CV duy nhất và nhận lại ngay kết quả trích xuất dạng JSON.