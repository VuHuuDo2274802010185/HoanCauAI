# HoanCau AI CV Processor - Full Gradio Interface

## 🌟 Giới thiệu

Đây là phiên bản Gradio đầy đủ tính năng của hệ thống xử lý CV thông minh HoanCau AI. Ứng dụng này cung cấp giao diện web hiện đại và toàn diện cho việc xử lý CV tự động với AI.

## ✨ Tính năng chính

### 🤖 Xử lý CV thông minh
- **Multi-LLM Support**: Hỗ trợ Google AI và OpenRouter
- **Batch Processing**: Xử lý hàng loạt CV từ email
- **Single File Processing**: Xử lý từng file CV riêng lẻ
- **Smart Extraction**: Trích xuất thông tin CV tự động với AI

### 📧 Tích hợp Email
- **Auto Fetch**: Tự động tải CV từ Gmail
- **Smart Filtering**: Lọc theo ngày, trạng thái đọc
- **UID Tracking**: Theo dõi email đã xử lý
- **Attachment Management**: Quản lý file đính kèm

### 💬 Chat với AI
- **CV Consultation**: Tư vấn về CV và tuyển dụng
- **Data Analysis**: Phân tích dữ liệu CV có sẵn
- **Interactive Q&A**: Hỏi đáp trực tiếp với AI
- **Chat History**: Lưu lịch sử trò chuyện

### 📊 Quản lý kết quả
- **Real-time Display**: Hiển thị kết quả thời gian thực
- **Export Options**: Xuất CSV, Excel
- **Data Visualization**: Bảng dữ liệu tương tác
- **Progress Tracking**: Theo dõi tiến trình xử lý

### ⚙️ Cấu hình nâng cao
- **Multi-provider**: Google AI, OpenRouter
- **Model Selection**: Chọn model AI phù hợp
- **API Management**: Quản lý khóa API
- **System Status**: Giám sát trạng thái hệ thống

## 🚀 Cài đặt và chạy

### Yêu cầu
- Python 3.8+
- pip
- Gmail account với App Password

### Cài đặt nhanh
```bash
# Clone repository
git clone <repository-url>
cd HoanCauAI

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình .env file
cp .env.example .env
# Chỉnh sửa .env với API keys và email config

# Chạy ứng dụng
./start_gradio_full.sh
```

### Cài đặt thủ công
```bash
# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Cài đặt packages
pip install gradio pandas python-dotenv requests beautifulsoup4

# Chạy
python gradio_full.py
```

## 🔧 Cấu hình

### 1. API Keys
Cấu hình trong giao diện web hoặc file `.env`:

```env
# Google AI
GOOGLE_API_KEY=your_google_api_key_here

# OpenRouter (alternative)
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 2. Email Configuration
```env
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_UNSEEN_ONLY=True
```

**Lưu ý**: Cần bật 2FA và tạo App Password cho Gmail.

### 3. Model Selection
- **Mặc định**: gemini-2.0-flash-exp (Google)
- **Alternatives**: Các model OpenRouter khác
- **Tự động detect**: Platform dựa trên API key

## 📖 Hướng dẫn sử dụng

### Bước 1: Cấu hình LLM
1. Mở giao diện web tại `http://localhost:7863`
2. Trong sidebar, chọn Provider (google/openrouter)
3. Nhập API Key
4. Chọn Model từ danh sách

### Bước 2: Cấu hình Email
1. Nhập Gmail và App Password
2. Click "Test Email" để kiểm tra kết nối
3. Xem Last UID để track tiến trình

### Bước 3: Fetch CV từ Email
1. Chuyển sang tab "📧 Lấy & Xử lý CV"
2. Chọn khoảng ngày (DD/MM/YYYY)
3. Tùy chọn "unseen only" hoặc "ignore last UID"
4. Click "📥 Fetch" để tải CV

### Bước 4: Xử lý CV
1. Sau khi fetch, click "⚙️ Process"
2. Theo dõi progress bar
3. Xem kết quả trong tab "📊 Kết quả"

### Bước 5: Xử lý file đơn lẻ
1. Tab "📄 Single File"
2. Upload file CV (.pdf/.docx)
3. Click "🔍 Phân tích CV"

### Bước 6: Chat với AI
1. Tab "💬 Hỏi AI"
2. Hỏi về CV, tuyển dụng, phân tích dữ liệu
3. AI sẽ tư vấn dựa trên CV đã xử lý

## 🎨 Giao diện

### Layout
- **Sidebar**: Cấu hình LLM, Email, System Status
- **Main Area**: 4 tabs chính
  - 📧 Lấy & Xử lý CV
  - 📄 Single File  
  - 📊 Kết quả
  - 💬 Hỏi AI

### Theme
- **Modern Design**: Giao diện hiện đại, responsive
- **Color Scheme**: Vàng gold (#d4af37) chủ đạo
- **Typography**: Be Vietnam Pro font
- **Interactive**: Buttons, forms tương tác mượt mà

## 🔍 Troubleshooting

### Lỗi thường gặp

1. **Import Module Error**
```bash
# Kiểm tra Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

2. **API Key Error**
```bash
# Kiểm tra .env file
cat .env | grep API_KEY
```

3. **Email Connection Error**
```bash
# Kiểm tra 2FA và App Password
# Đảm bảo "Less secure app access" được bật
```

4. **Port Already in Use**
```bash
# Đổi port trong gradio_full.py
app.launch(server_port=7864)  # Thay 7863
```

### Performance Tips

1. **Memory Usage**: Giới hạn batch size khi xử lý nhiều CV
2. **API Limits**: Theo dõi quota của API providers
3. **File Size**: Giới hạn file CV < 10MB
4. **Cache**: Clear cache models khi cần

## 📁 Cấu trúc file

```
HoanCauAI/
├── gradio_full.py          # Main application
├── start_gradio_full.sh    # Launch script
├── src/modules/            # Core modules
├── attachments/            # CV files
├── csv/                    # CSV outputs  
├── excel/                  # Excel outputs
├── log/                    # Log files
├── static/                 # Static assets
├── .env                    # Environment config
└── requirements.txt        # Dependencies
```

## 🆚 So sánh phiên bản

| Tính năng | Streamlit | Gradio Simple | Gradio Full |
|-----------|-----------|---------------|-------------|
| Interface | ✅ | ✅ | ✅ |
| LLM Multi-provider | ✅ | ❌ | ✅ |
| Email Integration | ✅ | ❌ | ✅ |
| Chat with AI | ✅ | ❌ | ✅ |
| Progress Tracking | ✅ | ❌ | ✅ |
| Single File | ✅ | ✅ | ✅ |
| Export Options | ✅ | ❌ | ✅ |
| System Status | ✅ | ❌ | ✅ |

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## 🆘 Support

- **Issues**: Tạo issue trên GitHub
- **Email**: contact@hoancau.ai
- **Documentation**: Xem wiki của repository

---

**HoanCau AI CV Processor** - Xử lý CV thông minh với sức mạnh AI 🚀
