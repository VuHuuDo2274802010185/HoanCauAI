# HoanCau AI Resume Processor

HoanCau AI Resume Processor là hệ thống tự động trích xuất thông tin quan trọng từ hồ sơ (.pdf, .docx), hỗ trợ chạy qua CLI, giao diện web (Streamlit) và API (FastAPI).

## 🌟 Tính năng

- Tự động quét email IMAP, tải file đính kèm và xử lý batch.
- Xử lý một file CV đơn lẻ.
- Chạy lệnh CLI, web UI hoặc FastAPI server.
- Hỏi AI (chat) dựa trên dữ liệu đã xử lý.

## 🚀 Bắt đầu nhanh

1. **Clone repository**

   ```bash
   git clone <repo_url>
   cd HoanCauAI
   ```

2. **Tạo môi trường ảo & cài dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Linux/Mac
   # .venv\Scripts\activate     # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Tạo file `.env`**

   Tạo file `.env` tại gốc dự án với nội dung:
   ```env
   # LLM
   LLM_PROVIDER=google
   LLM_MODEL=gemini-1.5-flash-latest
   GOOGLE_API_KEY=<YOUR_GOOGLE_KEY>
   OPENROUTER_API_KEY=<YOUR_OPENROUTER_KEY>

   # Email IMAP
   EMAIL_HOST=imap.gmail.com
   EMAIL_PORT=993
   EMAIL_USER=<YOUR_EMAIL>
   EMAIL_PASS=<YOUR_PASSWORD>

   # Đường dẫn lưu trữ
   ATTACHMENT_DIR=attachments
   OUTPUT_CSV=cv_summary.csv
   ```

## ⚙️ Sử dụng CLI Agent

Các lệnh chính:

```bash
# Xem trợ giúp
python3 cli_agent.py --help

# Tự động fetch CV từ email (watch loop)
python3 cli_agent.py watch --interval 600

# Chạy full process: fetch + xử lý batch
python3 cli_agent.py full-process

# Xử lý một file CV đơn lẻ
python3 cli_agent.py single path/to/cv.pdf

# Chạy FastAPI MCP server
python3 cli_agent.py serve --host 0.0.0.0 --port 8000

# Hỏi AI dựa trên kết quả CSV
python3 cli_agent.py chat "Câu hỏi của bạn"
```

## 🌐 Giao diện web (Streamlit)

```bash
streamlit run main_engine/app.py
```
Truy cập `http://localhost:8501` để:
- Nhập API key và email.
- Theo dõi tự động fetch.
- Xử lý batch, xử lý đơn, xem CSV và chat với AI.

## 🗂️ Cấu trúc dự án

```
HoanCauAI/
├── cli_agent.py           # CLI agent chính
├── main_engine/           # Streamlit UI và các scripts cũ
│   └── app.py
├── modules/               # Core modules (fetcher, processor, chatbot, server)
├── attachments/           # Lưu CV tải về
├── .env.example           # Mẫu cấu hình môi trường
├── requirements.txt       # Dependencies
└── README.md              # Hướng dẫn sử dụng
```

## 🤝 Đóng góp

1. Fork repo và tạo branch mới.
2. Viết code và test (pytest).
3. Commit, push và mở Pull Request.

## 📜 License

Distributed under the MIT License. Xem `LICENSE` chi tiết.
