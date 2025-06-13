# README.md

## 🧠 Trình Trích Xuất Thông Tin CV với AI (Gemini)

Ứng dụng sử dụng Google Gemini AI để tự động đọc và trích xuất thông tin từ các file CV (.pdf, .docx), hỗ trợ nhà tuyển dụng tổng hợp dữ liệu nhanh chóng.

---

## 🏗️ Cấu trúc dự án
```
.
├── app.py                  # Giao diện chính Streamlit
├── static/
│   └── logo.png            # Logo ứng dụng
├── modules/
│   ├── config.py           # Cấu hình API và email
│   ├── cv_processor.py     # Xử lý CV, trích xuất AI
│   ├── email_fetcher.py    # Lấy CV từ email IMAP
│   └── prompts.py          # Prompt cho mô hình AI
├── attachments/            # Lưu các file CV tải về
├── cv_summary.xlsx         # Kết quả trích xuất
└── requirements.txt        # Thư viện cần thiết
```

---

## 🚀 Hướng dẫn cài đặt

### 1. Clone và cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Tạo file `.env`
```ini
GOOGLE_API_KEY=your_gemini_api_key
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

> 🔐 Khuyến nghị dùng App Password nếu dùng Gmail.

### 3. Chạy ứng dụng
```bash
streamlit run app.py
```

---

## ✨ Tính năng chính
- Tải CV từ email hoặc upload trực tiếp
- Trích xuất AI với Gemini Free
- Ghi kết quả ra Excel, có định dạng đẹp
- Giao diện đơn giản, dễ sử dụng

---

## 📩 Hỗ trợ
Nếu có lỗi hoặc cần hỗ trợ, hãy liên hệ: `your_email@example.com`
