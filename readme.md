# HoanCau AI Resume Processor

HoanCau AI Resume Processor là hệ thống AI tự động trích xuất và phân tích thông tin từ CV/Resume (.pdf, .docx), hỗ trợ:
- 🌐 **Web Application** (Streamlit)
- 📡 **API Server** (FastAPI) 
- 🎯 **Embeddable Widget** (nhúng vào website)
- 💻 **Desktop Application** (Electron)

## 📁 Cấu trúc dự án

```
HoanCauAI/
├── 📱 main_engine/          # Ứng dụng Streamlit chính
│   ├── app.py              # Main Streamlit app
│   └── tabs/               # UI tabs (chat, process, results...)
├── 🔧 modules/             # Core Python modules
│   ├── cv_processor.py     # CV processing logic
│   ├── llm_client.py       # AI client integrations
│   └── qa_chatbot.py       # Chat functionality
├── 📡 api/                 # FastAPI server for embedding
│   ├── api_server.py       # API endpoints
│   └── README.md           # API documentation
├── 🎯 widget/              # Embeddable widget
│   ├── widget.html         # Widget UI
│   ├── widget.js           # Widget logic
│   ├── embed.html          # Integration guide
│   └── README.md           # Widget documentation
├── 💻 desktop/             # Electron desktop app
│   ├── package.json        # Node.js configuration
│   ├── src/                # Electron source files
│   ├── assets/             # App resources
│   └── README.md           # Desktop app guide
├── 🚀 scripts/             # Automation scripts
│   ├── run-all.sh          # Start all services
│   ├── start-api.sh        # Start API only
│   ├── build-electron.sh   # Build desktop app
│   └── README.md           # Scripts documentation
├── 📚 docs/                # Documentation
│   ├── DEPLOYMENT_GUIDE.md # Deployment guide
│   └── README.md           # Docs overview
└── 📄 static/              # Static assets (CSS, images)
```

## � Quick Start

### 1. Chạy tất cả services (Khuyến nghị)
```bash
# Clone repository
git clone <repository-url>
cd HoanCauAI

# Chạy tất cả services
chmod +x scripts/*.sh
./scripts/run-all.sh
```

### 2. Chỉ chạy API server (để nhúng widget)
```bash
./scripts/start-api.sh
```

### 3. Chỉ chạy Streamlit app
```bash
cd main_engine
streamlit run app.py
```

### 4. Build desktop app
```bash
./scripts/build-electron.sh
```

## 🌍 Truy cập ứng dụng

Sau khi chạy `./scripts/run-all.sh`:

- 🌐 **API Server**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs
- 🎯 **Widget Demo**: http://localhost:8000/widget
- 📊 **Streamlit App**: http://localhost:8501
- 💻 **Desktop App**: Electron window

## 🎯 Tính năng chính

### 🌐 Web Application
- Upload và phân tích CV/Resume
- Giao diện thân thiện với Streamlit
- Xử lý batch files
- Xuất kết quả CSV/Excel
- Chat AI tương tác

### 📡 API Server
- RESTful APIs cho phân tích CV
- CORS support cho embedding
- Swagger documentation
- Health monitoring
- Rate limiting ready

### 🎯 Embeddable Widget
- Nhúng vào bất kỳ website nào
- 3 cách tích hợp (iframe, JS, API)
- Responsive design
- Customizable theme
- Real-time chat

### 💻 Desktop App
- Cross-platform (Windows/macOS/Linux)
- Native file handling
- Offline capabilities
- System integration
- Auto-updates ready

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
Sau khi hoàn tất, chạy tiếp `./run_resume_ai.sh` để mở giao diện Streamlit.

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
streamlit run simple_app.py
```

Ứng dụng sẽ hướng dẫn tuần tự nhập API key → fetch CV → xử lý → xem kết quả và ẩn các tab nâng cao.

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
