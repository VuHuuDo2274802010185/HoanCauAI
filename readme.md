# HoanCau AI Resume Processor

HoanCau AI Resume Processor là hệ thống tự động trích xuất thông tin quan trọng từ hồ sơ (.pdf, .docx), hỗ trợ chạy qua CLI, giao diện web (Streamlit) và API (FastAPI).

## 📋 Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn (https://www.python.org/downloads/)
- Pip (đi kèm Python) hoặc pip3
- Virtual environment tool (`venv` hoặc `virtualenv`)
- Git (để clone repository) https://git-scm.com/downloads
- Tài khoản email IMAP (Gmail, Outlook, v.v.) với quyền truy cập IMAP hiện bật
- Trình duyệt web hiện đại (Chrome, Firefox) để sử dụng giao diện Streamlit

## ✉️ Troubleshooting Email Fetch

- Đảm bảo IMAP đã được bật trong cài đặt email (Gmail: Settings → Forwarding and POP/IMAP → Enable IMAP).
- Với Gmail, tạo **App Password** thay vì mật khẩu chính: https://support.google.com/mail/answer/185833
- Kiểm tra file `.env` đúng thông tin:
  ```bash
  cat .env | grep EMAIL
  ```
- Chạy lệnh thử tay:
  ```bash
  python3 -c "from modules.email_fetcher import EmailFetcher; f=EmailFetcher(); f.connect(); print(f.fetch_cv_attachments())"
  ```
  Kết quả trả về danh sách đường dẫn file (nếu trống, nghĩa là không tìm thấy attachment trong inbox).
- Nếu vẫn không có email, kiểm tra folder IMAP mặc định là `INBOX`, hoặc đổi:
  ```python
  f.mail.select('INBOX.Sent Mail')  # hoặc tên folder khác
  ```

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
   EMAIL_UNSEEN_ONLY=1

   # Đường dẫn lưu trữ
   ATTACHMENT_DIR=attachments
   OUTPUT_CSV=cv_summary.csv
   ```

### 💻 Cài đặt nhanh trên Windows

1. Truy cập trang GitHub repo và bấm **Code** → **Download ZIP** (hoặc dùng
   `git clone <repo_url>`).
2. Giải nén (nếu tải ZIP) và mở `cmd` trong thư mục dự án.
3. Chạy `setup.cmd` để tự động tạo `.env`, tạo virtual env và cài đặt
   dependencies.
4. Mở file `.env` vừa tạo và điền các biến như `GOOGLE_API_KEY`, thông tin
   `EMAIL_*`.
5. Cuối cùng chạy `run_resume_ai.cmd` để khởi động (không tham số sẽ mở UI,
   thêm `cli` để chạy qua dòng lệnh).

### 🛡️ SmartScreen trên Windows

Khi chạy `setup.cmd` hoặc `run_resume_ai.cmd` lần đầu, SmartScreen có thể chặn file với thông báo "Windows protected your PC". Để bỏ chặn:

1. Chuột phải vào file → **Properties** → tích **Unblock** → Apply.
2. Hoặc chạy PowerShell:
   ```powershell
   Unblock-File .\setup.cmd
   Unblock-File .\run_resume_ai.cmd
   ```
   Sau đó chạy script lại.

## ⚙️ Sử dụng CLI Agent

Các lệnh chính:

```bash
# Xem trợ giúp
python3 cli_agent.py --help

# Tự động fetch CV từ email (watch loop)
python3 cli_agent.py watch --interval 600     # chỉ quét UNSEEN
python3 cli_agent.py watch --all             # quét toàn bộ email

# Chạy full process: fetch + xử lý batch
python3 cli_agent.py full-process            # chỉ quét UNSEEN
python3 cli_agent.py full-process --all      # quét toàn bộ

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
