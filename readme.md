# HoanCau AI Resume Processor

HoanCau AI Resume Processor là hệ thống tự động trích xuất thông tin quan trọng từ hồ sơ (.pdf, .docx), hỗ trợ chạy qua CLI, giao diện web (Streamlit) và API (FastAPI).

## 📋 Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn (https://www.python.org/downloads/)
- Pip (đi kèm Python) hoặc pip3
- Virtual environment tool (`venv` hoặc `virtualenv`)
- Git (để clone repository) https://git-scm.com/downloads
- Tài khoản email IMAP (Gmail, Outlook, v.v.) với quyền truy cập IMAP hiện bật
- Trình duyệt web hiện đại (Chrome, Firefox) để sử dụng giao diện Streamlit

## 🚦 Beginner Setup

1. **Cài Python và Git**
   - Tải Python từ [python.org](https://www.python.org/downloads/) rồi cài đặt
     như hướng dẫn (Windows nhớ tick "Add python to PATH").
   - Tải Git tại [git-scm.com](https://git-scm.com/downloads) và cài đặt mặc định.
2. **Mở Terminal / Command Prompt**
   - **Windows**: nhấn `Win + R` → gõ `cmd` → Enter.
   - **macOS**: mở **Terminal** từ Spotlight hoặc Applications.
   - **Linux**: mở ứng dụng **Terminal**.
3. **Kiểm tra phiên bản**
   ```bash
   python --version   # hoặc python3 --version
   git --version
   ```
   Nếu cả hai lệnh đều in phiên bản, bạn đã sẵn sàng tiếp tục.

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
- Lưu log cuộc trò chuyện của tính năng Hỏi AI.
- Không gây cảnh báo Streamlit khi chạy CLI: `DynamicLLMClient` tự kiểm tra session context.

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
   Hoặc đơn giản chạy `./setup.sh` (macOS/Linux) hoặc `setup.cmd` (Windows)
   để tự động thực hiện các bước trên.

3. **Tạo file `.env`**

   Sao chép file mẫu `.env.example` thành `.env` rồi điền các khoá API của bạn:
   ```bash
   cp .env.example .env
   ```
   Sau đó mở `.env` bằng editor bất kỳ và thay thế các giá trị placeholder
   (như `your_google_api_key`) bằng thông tin thực tế. Những biến quan trọng gồm:
   `LLM_PROVIDER`, `LLM_MODEL`, một trong các khóa API (`GOOGLE_API_KEY` hoặc
   `OPENROUTER_API_KEY`), `EMAIL_USER` và `EMAIL_PASS`. File `.env` đã nằm trong
   `.gitignore` nên **không commit** lên Git. Nếu gặp lỗi cấu hình, hãy so sánh
   với file mẫu [`.env.example`](./.env.example) để biết các biến cần thiết.
   Bạn có thể tạo sẵn các thư mục `attachments`, `output` và `log` (hoặc để
   script tự tạo) để lưu file tải về và log.

### 💻 Cài đặt nhanh trên Windows

1. Truy cập trang GitHub repo và bấm **Code** → **Download ZIP** (hoặc dùng
   `git clone <repo_url>`).
2. Giải nén (nếu tải ZIP) và mở `cmd` trong thư mục dự án.
3. Chạy `setup.cmd` để tự động tạo `.env`, tạo virtual env và cài đặt
   dependencies.
4. Mở file `.env` vừa tạo và điền các biến như `GOOGLE_API_KEY`, thông tin
   `EMAIL_*`.
5. Cuối cùng chạy `run_resume_ai.cmd` để mở ngay giao diện Streamlit.

### 📦 Tự động setup trên macOS/Linux

Trong thư mục dự án, chạy:

```bash
./setup.sh
```

Script sẽ tạo `.env`, virtualenv và cài dependencies tương tự `setup.cmd`.
Sau khi hoàn tất, chạy tiếp `./start.sh` để khởi chạy nhanh giao diện Streamlit.

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
python3 scripts/cli_agent.py --help

# Tự động fetch CV từ email (watch loop)
python3 scripts/cli_agent.py watch --interval 600     # chỉ quét UNSEEN
python3 scripts/cli_agent.py watch --all             # quét toàn bộ email

# Chạy full process: fetch + xử lý batch
python3 scripts/cli_agent.py full-process            # chỉ quét UNSEEN
python3 scripts/cli_agent.py full-process --all      # quét toàn bộ

# Xử lý một file CV đơn lẻ
python3 scripts/cli_agent.py single path/to/cv.pdf

# Chạy FastAPI MCP server
python3 scripts/cli_agent.py serve --host 0.0.0.0 --port 8000

# Hỏi AI dựa trên kết quả CSV
python3 scripts/cli_agent.py chat "Câu hỏi của bạn"
```
Lệnh `chat` tự động sử dụng khóa API tương ứng với `LLM_PROVIDER`
được khai báo trong file `.env` (`GOOGLE_API_KEY` hoặc `OPENROUTER_API_KEY`).
Mỗi lần hỏi đáp sẽ được lưu vào file log tại `log/chat_log.json` (có thể thay đổi qua biến `CHAT_LOG_FILE`).

## 🌐 Giao diện web (Streamlit)

```bash
streamlit run main_engine/app.py
```
Truy cập `http://localhost:8501` để:
- Nhập API key và email.
- Theo dõi tự động fetch.
- Xử lý batch, xử lý đơn, xem CSV và chat với AI.
- Trong tab **MCP Server**, nhập API key (Google/OpenRouter/VectorShift) và nhấn
  "Khởi động" để server tự nhận diện platform.

### 🚲 Simple Mode

Nếu chỉ cần các bước cơ bản, chạy:

```bash
streamlit run scripts/simple_app.py
```

Ứng dụng sẽ hướng dẫn tuần tự nhập API key → fetch CV → xử lý → xem kết quả và ẩn các tab nâng cao.

## 🗂️ Cấu trúc dự án

```
HoanCauAI/
├── scripts/               # CLI và các tiện ích
│   ├── cli_agent.py
│   ├── simple_app.py
│   └── health_check.py
├── main_engine/           # Streamlit UI và các scripts cũ
│   └── app.py
├── modules/               # Core modules (fetcher, processor, chatbot, server)
├── config/                # File cấu hình JSON
├── csv/                   # Kết quả CSV
├── docs/                  # Tài liệu bổ sung
├── attachments/           # Lưu CV tải về
├── static/                # Tệp CSS và tài nguyên giao diện
│   ├── style.css
│   └── custom.css
├── .env.example           # Mẫu cấu hình môi trường
├── requirements.txt       # Dependencies
└── README.md              # Hướng dẫn sử dụng
```

Tệp `static/custom.css` chứa các biến được định dạng từ ứng dụng để điều chỉnh giao diện. Có thể chỉnh sửa file này để thay đổi màu sắc hoặc font chữ.

## 🤝 Đóng góp

1. Fork repo và tạo branch mới.
2. Viết code và test (pytest).
3. Commit, push và mở Pull Request.

## 🧪 Chạy test

Sau khi cài đặt các phụ thuộc, chạy toàn bộ test bằng:

```bash
pytest
```

Có thể kiểm tra nhanh môi trường với:

```bash
python3 scripts/health_check.py
```

## 📜 License

Distributed under the MIT License. Xem `LICENSE` chi tiết.
