# HoanCau AI Resume Processor

HoanCau AI Resume Processor là hệ thống tự động trích xuất thông tin quan trọng từ hồ sơ (.pdf, .docx), hỗ trợ chạy qua CLI, giao diện web (Streamlit) và API (FastAPI).

## 🚀 Setup

### ⚡ Quick Start

1. **Tải mã nguồn** về máy
2. **Windows:** chạy `setup_window.cmd` rồi `start_window.cmd`
3. **macOS/Linux:** chạy `./setup_linux.sh` rồi `./start_linux.sh`
4. Làm theo hướng dẫn hiển thị trên màn hình

### 📋 Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn (https://www.python.org/downloads/)
- Pip (đi kèm Python) hoặc pip3
- Virtual environment tool (`venv` hoặc `virtualenv`)
- Git (https://git-scm.com/downloads) để clone repository
- Tài khoản email IMAP (Gmail, Outlook, v.v.) với quyền truy cập IMAP bật
- Trình duyệt web hiện đại (Chrome, Firefox) để sử dụng giao diện Streamlit

### 🚦 Cài đặt thủ công

1. **Cài Python và Git**
   - Tải Python từ [python.org](https://www.python.org/downloads/) rồi cài đặt (Windows nhớ tick "Add python to PATH")
   - Tải Git tại [git-scm.com](https://git-scm.com/downloads) và cài mặc định
2. **Mở Terminal / Command Prompt**
   - **Windows:** nhấn `Win + R` → gõ `cmd` → Enter
   - **macOS:** mở **Terminal** từ Spotlight hoặc Applications
   - **Linux:** mở ứng dụng **Terminal**
3. **Kiểm tra phiên bản**
   ```bash
   python --version   # hoặc python3 --version
   git --version
   ```
   Nếu cả hai lệnh đều in phiên bản, bạn đã sẵn sàng tiếp tục

## ✉️ Troubleshooting Email Fetch

- Đảm bảo IMAP đã được bật trong cài đặt email (Gmail: Settings → Forwarding and POP/IMAP → Enable IMAP).
- Với Gmail, tạo **App Password** thay vì mật khẩu chính: https://support.google.com/mail/answer/185833
- Kiểm tra file `.env` đúng thông tin:
  ```bash
  cat .env | grep EMAIL
  ```
- Chạy lệnh thử tay:
  ```bash
  python3 -c "from modules.email_fetcher import EmailFetcher; f=EmailFetcher(); f.connect(); print(f.fetch_cv_attachments()); print(f.last_fetch_info)"
  ```
  Kết quả trả về danh sách đường dẫn file (nếu trống, nghĩa là không tìm thấy attachment trong inbox).
  Thuộc tính `last_fetch_info` chứa cặp `(path, sent_time)` cho mỗi file mới tải.
  Khi xử lý bằng `CVProcessor`, cột `Thời gian nhận` (đứng trước cột `Nguồn`) trong bảng kết quả sẽ hiển thị giá trị `sent_time` này.
  Chuỗi ISO sẽ được định dạng lại cho dễ đọc, ví dụ `2:33 pm 26/6/2025`.
  Các giá trị thời gian này được lưu lại trong file `attachments/sent_times.json` để lần xử lý sau vẫn giữ nguyên thông tin.
- Nếu vẫn không có email, kiểm tra folder IMAP mặc định là `INBOX`, hoặc đổi:
  ```python
  f.mail.select('INBOX.Sent Mail')  # hoặc tên folder khác
  ```

### 🔧 Thiết lập môi trường

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
pip install -r requirements-dev.txt # for running tests
```
Hoặc đơn giản chạy `./setup_linux.sh` (macOS/Linux) hoặc `setup_window.cmd` (Windows)
để tự động tạo môi trường, cài dependencies, sao chép `.env.example` và
tạo các thư mục cần thiết.

3. **Tạo file `.env`**

   Sao chép file mẫu `.env.example` thành `.env` rồi điền các khoá API của bạn:
   ```bash
   cp .env.example .env
   ```
   Sau đó mở `.env` bằng editor bất kỳ và thay thế các giá trị placeholder
   (như `your_google_api_key`) bằng thông tin thực tế hoặc chạy
   `python scripts/update_env.py` để nhập giá trị trực tiếp. Những biến quan trọng gồm:
   `LLM_PROVIDER`, `LLM_MODEL`, một trong các khóa API (`GOOGLE_API_KEY` hoặc
   `OPENROUTER_API_KEY`), `EMAIL_USER` và `EMAIL_PASS`. File `.env` đã nằm trong
   `.gitignore` nên **không commit** lên Git. Nếu gặp lỗi cấu hình, hãy so sánh
   với file mẫu [`.env.example`](./.env.example) để biết các biến cần thiết.
    Bạn có thể tạo sẵn các thư mục `attachments`, `csv`, `log` và `static` (hoặc để
   script tự tạo) để lưu file tải về và log.
   Nếu trước đây bạn từng chạy phiên bản cũ sử dụng thư mục `.log` hoặc `logs`,
   dự án sẽ tự động chuyển toàn bộ nội dung sang `log` khi khởi chạy.

### 💻 Cài đặt nhanh trên Windows

1. Truy cập trang GitHub repo và bấm **Code** → **Download ZIP** (hoặc dùng
   `git clone <repo_url>`).
2. Giải nén (nếu tải ZIP) và mở `cmd` trong thư mục dự án.
3. Chạy `setup_window.cmd` để tự động tạo `.env`, tạo virtual env và cài đặt
   dependencies.
4. Mở file `.env` vừa tạo và điền các biến như `GOOGLE_API_KEY`, thông tin
   `EMAIL_*`.
5. Cuối cùng chạy `start_window.cmd` để mở ngay giao diện Streamlit.

### 📦 Tự động setup trên macOS/Linux

Trong thư mục dự án, chạy:

```bash
./setup_linux.sh
```

Script sẽ tạo `.env`, virtualenv và cài dependencies tương tự `setup_window.cmd`.
Sau khi hoàn tất, chạy tiếp `./start_linux.sh` để khởi chạy nhanh giao diện Streamlit.

### 📦 Cài đặt package tùy chọn

Bạn có thể cài đặt project như một package Python để sử dụng câu lệnh `cli-agent`
ở bất kỳ đâu. Điều này tiện lợi cho việc gọi CLI mà không cần chỉ định đường dẫn
`scripts/cli_agent.py`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Sau khi cài đặt, chạy thử:

```bash
cli-agent --help
```

Các lệnh tương tự phần bên dưới nhưng ngắn gọn hơn.

### 🛡️ SmartScreen trên Windows

Khi chạy `setup_window.cmd` hoặc `start_window.cmd` lần đầu, SmartScreen có thể chặn file với thông báo "Windows protected your PC". Để bỏ chặn:

1. Chuột phải vào file → **Properties** → tích **Unblock** → Apply.
2. Hoặc chạy PowerShell:
   ```powershell
   Unblock-File .\setup_window.cmd
   Unblock-File .\start_window.cmd
   ```
   Sau đó chạy script lại.

## 🌟 Tính năng

- Tự động quét email IMAP, tải file đính kèm và xử lý batch.
- Xử lý một file CV đơn lẻ.
- Trích xuất thông tin qua LLM (Google Gemini/OpenRouter) với cơ chế fallback.
- Lưu kết quả sang CSV và Excel.
- Hỏi đáp thông tin tuyển dụng dựa trên dữ liệu đã xử lý.
- Chat bằng giọng nói trực tiếp trong tab Hỏi AI.
- Chạy lệnh CLI, web UI hoặc FastAPI server.
- Cung cấp API MCP server để tích hợp hệ thống khác.
- Lưu log cuộc trò chuyện của tính năng Hỏi AI.
- Không gây cảnh báo Streamlit khi chạy CLI: `DynamicLLMClient` tự kiểm tra session context.

## ⚙️ Sử dụng CLI Agent

Các lệnh chính:

```bash
# Xem trợ giúp
cli-agent --help             # đã cài package
# hoặc
python3 scripts/cli_agent.py --help

# Tự động fetch CV từ email (watch loop)
cli-agent watch --interval 600     # chỉ quét UNSEEN
cli-agent watch --all             # quét toàn bộ email

# Chạy full process: fetch + xử lý batch
cli-agent full-process            # chỉ quét UNSEEN
cli-agent full-process --all      # quét toàn bộ

# Xử lý một file CV đơn lẻ
cli-agent single path/to/cv.pdf

# Chạy FastAPI MCP server
cli-agent serve --host 0.0.0.0 --port 8000

# Hỏi AI dựa trên kết quả CSV
cli-agent chat "Câu hỏi của bạn"
```
Lệnh `chat` tự động sử dụng khóa API tương ứng với `LLM_PROVIDER`
được khai báo trong file `.env` (`GOOGLE_API_KEY` hoặc `OPENROUTER_API_KEY`).
Mỗi lần hỏi đáp sẽ được lưu vào file log tại `log/chat_log.json` (có thể thay đổi qua biến `CHAT_LOG_FILE` hoặc thư mục `LOG_DIR`).

## 🌐 Giao diện web (Streamlit)

```bash
streamlit run src/main_engine/app.py
```
Truy cập `http://localhost:8501` để:
- Nhập API key và email.
- Theo dõi tự động fetch.
- Xử lý batch, xử lý đơn, xem CSV và chat với AI.
- Gửi câu hỏi và nghe trả lời bằng giọng nói ngay trong tab **Hỏi AI**.
- Trong tab **MCP Server**, nhập API key (Google/OpenRouter/VectorShift) và nhấn
  "Khởi động" để server tự nhận diện platform.
- Tab **Chỉnh .env** cho phép xem và lưu nội dung file cấu hình ngay trên giao diện.

### 🚲 Simple Mode

Nếu chỉ cần các bước cơ bản, chạy:

```bash
streamlit run scripts/simple_app.py
```

Ứng dụng sẽ hướng dẫn tuần tự nhập API key → fetch CV → xử lý → xem kết quả và ẩn các tab nâng cao.

### 🌙 Dark Mode

Giao diện nay hỗ trợ cả chế độ sáng và tối. Streamlit sẽ áp dụng theme dựa trên cài đặt trong `~/.streamlit/config.toml` hoặc lựa chọn *Appearance* ở menu cài đặt (biểu tượng bánh răng). Theme tối sử dụng tông vàng chủ đạo như chế độ sáng nhưng với nền đen dịu mắt, phù hợp làm việc ban đêm.

## 🗂️ Cấu trúc dự án

```
HoanCauAI/
├── scripts/               # CLI và các tiện ích
│   ├── cli_agent.py
│   ├── simple_app.py
│   └── health_check.py
├── src/
│   ├── main_engine/       # Streamlit UI và các scripts cũ
│   │   └── app.py
│   └── modules/           # Core modules (fetcher, processor, chatbot, server)
├── config/                # File cấu hình JSON
├── csv/                   # Kết quả CSV
├── docs/                  # Tài liệu bổ sung
├── attachments/           # Lưu CV tải về
├── .env.example           # Mẫu cấu hình môi trường
├── requirements.txt       # Dependencies
└── README.md              # Hướng dẫn sử dụng
```

## 🤝 Đóng góp

1. Fork repo và tạo branch mới.
2. Viết code và test (pytest).
3. Commit, push và mở Pull Request.

## 🧪 Chạy test

Trước khi chạy test, cài đặt các gói trong `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
pytest
```


Các test tự tạo module giả mạo cho `pandas` và `requests` nếu bạn chưa cài hai
thư viện này. Điều này giúp chạy test nhanh mà không cần cài đầy đủ phụ
thuộc.

Có thể kiểm tra nhanh môi trường với:

```bash
python3 scripts/health_check.py
```

## 📜 License

Distributed under the MIT License. Xem `LICENSE` chi tiết.
