# Build Resume AI

**Build Resume AI** là hệ thống tự động trích xuất thông tin quan trọng từ file CV/Resume (.pdf, .docx) dành cho:

* **Người dùng cuối**: giao diện web (Streamlit), scripts .bat dễ chạy.
* **Developer**: API (FastAPI), CLI, module động, dễ mở rộng.

---

## 🌟 Tính năng chính

1. **Batch Processing** qua email IMAP:

   * Quét hòm thư, tìm email có từ khóa (CV, Resume).
   * Tự động tải file đính kèm, trích xuất, lưu kết quả.
2. **Single File Processing**:

   * Upload file CV đơn lẻ (.pdf/.docx) và nhận ngay kết quả JSON.
3. **Top5 Selection**:

   * Dùng AI (Google Gemini/OpenRouter) đánh giá, chọn ra TOP 5 hồ sơ tốt nhất.
4. **CLI & Scripts Windows**:

   * `main_engine/main.py` xử lý batch/single qua CLI.
   * `main_engine/select_top5.py` chọn TOP 5 qua AI.
   * `run_resume_ai.bat` chạy UI hoặc CLI/select tự động.
5. **Streamlit UI**:

   * Giao diện web trực quan để cấu hình LLM, chạy batch/single, xem & tải CSV.
6. **Module tái sử dụng**:

   * `modules/email_fetcher.py`, `modules/cv_processor.py`, `modules/dynamic_llm_client.py`,...
   * Dễ dàng tích hợp trong dự án khác.

---

## 🚀 Bắt đầu nhanh

1. **Clone repository**

   ```bash
   git clone <repo_url>
   cd <repo_folder>
   ```
2. **Tạo môi trường ảo & cài dependencies**

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Tạo file `.env`**

   * Copy từ mẫu:

     ```bash
     cp .env.example .env
     ```
   * Hoặc dùng `setup.bat` (Windows):

     ```bash
     setup.bat
     ```
   * Điền giá trị:

     ```dotenv
     # LLM
     LLM_PROVIDER=google
     LLM_MODEL=gemini-1.5-flash-latest
     GOOGLE_API_KEY=...
     OPENROUTER_API_KEY=...

     # Email
     EMAIL_HOST=imap.gmail.com
     EMAIL_PORT=993
     EMAIL_USER=...
     EMAIL_PASS=...

     # Paths
     ATTACHMENT_DIR=attachments
     OUTPUT_CSV=cv_summary.csv

     # Canva (nếu dùng)
     CANVA_ACCESS_TOKEN=
     ```

---

## 📂 Cấu trúc dự án

```
.
├── main_engine/             # Entry-point cho UI & CLI
│   ├── app.py               # Streamlit UI
│   ├── main.py              # CLI batch/single
│   ├── select_top5.py       # Chọn TOP5 CV
│   └── run_resume_ai.bat    # Script Windows chạy UI/CLI/select
├── modules/                 # Module core
│   ├── config.py            # Load .env, cấu hình chung
│   ├── email_fetcher.py     # Fetch CV qua IMAP
│   ├── cv_processor.py      # Xử lý & trích xuất CV
│   ├── dynamic_llm_client.py# LLM client wrapper
│   ├── model_fetcher.py     # Lấy danh sách models
│   └── prompts.py           # Prompt mẫu cho AI
├── static/                  # Tài nguyên tĩnh
│   ├── style.css            # CSS tùy chỉnh
│   └── logo.png             # Logo hiển thị
├── attachments/             # Lưu CV tải từ email
├── tests/                   # Unit tests (pytest)
│   └── test_models.py       # Kiểm thử model_fetcher
├── .env.example             # Mẫu cấu hình môi trường
├── requirements.txt         # Dependencies
└── README.md                # Hướng dẫn này
```

---

## 🎯 Hướng dẫn sử dụng

### 1. Giao diện Streamlit UI

```bash
run_resume_ai.bat        # Windows: double-click hoặc chạy từ CMD
otr
# Hoặc Linux/Mac:
streamlit run main_engine/app.py
```

* Truy cập: `http://localhost:8501`
* Tab "Batch Email": xử lý hàng loạt từ email.
* Tab "Single File": upload CV đơn lẻ.
* Tab "Kết quả": xem & tải CSV.
* Sidebar cho phép nhập Gmail, mật khẩu và API key của provider.
  Nhấn "Lấy models" để cập nhật danh sách model từ API.
### 2. CLI (chạy Python)

```bash
# Batch qua email (mặc định)
python main_engine/main.py --batch
# Hoặc xử lý file đơn
python main_engine/main.py --single path/to/cv.pdf
```

### 3. Chọn TOP 5 CV

```bash
python main_engine/select_top5.py   # In ra danh sách TOP 5 Nguồn
```

### 4. Script Windows (.bat)

* `setup.bat`: tự động tạo `.env`, venv và cài dependencies.
* `run_resume_ai.bat [cli|select]`:

  * Không tham số: chạy UI.
  * `cli`: chạy main\_engine/main.py
  * `select`: chạy select\_top5.

---

## 🔧 Phát triển & đóng góp

1. Fork repo, tạo branch `feature/...`.
2. Viết code, chạy `pytest` đảm bảo không lỗi.
3. Commit & push lên branch, mở Pull Request.

---

## 📜 License

Distributed under the MIT License. Xem `LICENSE` để biết chi tiết.
