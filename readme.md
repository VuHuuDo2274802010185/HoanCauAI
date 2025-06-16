## Resume AI - CV Processor

**Resume AI** là một bộ công cụ toàn diện để tự động trích xuất thông tin quan trọng từ file CV/Resume (hỗ trợ PDF và DOCX). Dự án bao gồm cả giao diện web, API server và CLI, được thiết kế để:

* **Người dùng cuối** (không cần biết code) dễ dàng cài đặt, cấu hình và chạy batch hoặc single-file processing.
* **Developer** mới lần đầu tiếp cận nhanh chóng hiểu cấu trúc mã, mở rộng và bảo trì.

---

## 🌟 Tổng quan tính năng

1. **Batch Processing từ Email (IMAP)**

   * Kết nối IMAP, tìm email có từ khóa (CV, Resume), tải về thư mục `attachments`.
2. **Single File Processing**

   * Upload trực tiếp file CV (.pdf/.docx) qua giao diện hoặc API.
3. **AI Extraction**

   * Dùng Google Gemini hoặc OpenRouter để trích xuất các trường: `ten`, `email`, `dien_thoai`, `hoc_van`, `kinh_nghiem`.
4. **Regex Fallback**

   * Khi AI response không hợp lệ JSON, dùng biểu thức chính quy đơn giản để lấy thông tin.
5. **Streamlit UI**

   * Giao diện web thân thiện để cấu hình LLM, chạy xử lý, xem và tải kết quả.
6. **FastAPI Backend**

   * REST API có thể tích hợp với hệ thống khác hoặc AI Agent.
7. **CLI (Click)**

   * Câu lệnh `info` xem cấu hình hiện tại.
   * `list-models` liệt kê các models khả dụng.
8. **Unit Tests (pytest)**

   * Đảm bảo tính ổn định của module fetch model và logic quan trọng.

---

## 🚀 Bắt đầu nhanh

### 1. Clone & tạo môi trường ảo

```bash
git clone <repo_url>
cd <repo_folder>
python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc, điền các biến sau (không commit file này):

```dotenv
# --- LLM ---
LLM_PROVIDER=google              # 'google' hoặc 'openrouter'
LLM_MODEL=gemini-1.5-flash-latest
GOOGLE_API_KEY=your_google_key
OPENROUTER_API_KEY=your_openrouter_key

# --- Email (IMAP) ---
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_app_password

# --- Đường dẫn ---
ATTACHMENT_DIR=attachments       # thư mục lưu file tải về
OUTPUT_CSV=cv_summary.csv        # file CSV kết quả
```

> **Lưu ý**: `.env.example` có sẵn template, bạn chỉ cần sao chép và điền giá trị.

---

## 📂 Cấu trúc dự án

```
.
├── app.py                    # Streamlit UI
├── mcp_server.py             # FastAPI backend server
├── main.py                   # CLI entry point (import và chạy config_info)
├── modules/                  # Thư mục chứa module core
│   ├── config.py             # Load & validate .env → biến cấu hình dùng chung
│   ├── config_info.py        # CLI commands (Click) để xem config & models
│   ├── email_fetcher.py      # IMAP email fetching & attachment download
│   ├── cv_processor.py       # CV text extraction & info parsing
│   ├── dynamic_llm_client.py # LLM client cho Streamlit
│   ├── llm_client.py         # LLM client chung cho backend API
│   ├── model_fetcher.py      # Fetch & cache danh sách models từ API
│   └── prompts.py            # Prompt mẫu cho AI trích xuất thông tin CV
├── static/                   # Tài nguyên tĩnh cho UI
│   └── style.css             # Custom CSS cho Streamlit
├── attachments/              # Thư mục lưu CV tải về từ email
├── tests/                    # Unit tests (pytest)
│   └── test_models.py        # Test logic fetch model
├── .env.example              # Template file cấu hình môi trường
├── requirements.txt          # Danh sách dependencies
└── README.md                 # File hướng dẫn này
```

---

## 🎯 Hướng dẫn sử dụng

### Chạy giao diện Streamlit

```bash
streamlit run app.py
```

* Mở `http://localhost:8501` để cấu hình LLM, chạy batch hoặc single file, xem & tải kết quả.

### Chạy API Server

```bash
uvicorn mcp_server:app --reload --host 0.0.0.0 --port 8000
```

* Truy cập Swagger UI tại `http://localhost:8000/docs`.

#### Endpoints chính

| Phương thức | Đường dẫn            | Mô tả                                          |
| ----------- | -------------------- | ---------------------------------------------- |
| POST        | `/run-full-process`  | Quét email, tải CV, trích xuất, lưu CSV        |
| POST        | `/process-single-cv` | Upload CV (.pdf/.docx), trả về JSON trích xuất |
| GET         | `/results`           | Tải file CSV kết quả                           |

### Sử dụng CLI

```bash
# Xem thông tin cấu hình
python main.py info
# Liệt kê models khả dụng
python main.py list-models
```

---