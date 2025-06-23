# 🚀 HoanCau AI - Embeddable Widget & Desktop App

## 📋 Tổng quan

Dự án HoanCau AI hiện đã được mở rộng với:

1. **🌐 API Server** - Cho phép nhúng vào website
2. **📱 Embeddable Widget** - Widget có thể nhúng vào bất kỳ trang web nào  
3. **💻 Desktop App** - Ứng dụng desktop được xây dựng bằng Electron

## 🔧 Cài đặt và Chạy

### 1. API Server (Embeddable Backend)

```bash
# Linux/macOS
chmod +x start-api.sh
./start-api.sh

# Windows
start-api.bat
```

API sẽ chạy tại: `http://localhost:8000`
- 📖 API Docs: `http://localhost:8000/docs`
- 🎯 Widget Demo: `http://localhost:8000/widget`
- 📝 Hướng dẫn nhúng: `http://localhost:8000/static/embed.html`

### 2. Desktop App (Electron)

```bash
# Cài đặt Node.js dependencies
npm install

# Chạy development mode
npm run electron-dev

# Build cho production
# Linux/macOS
chmod +x build-electron.sh
./build-electron.sh

# Windows  
build-electron.bat
```

## 🌐 Nhúng Widget vào Website

### Phương pháp 1: Iframe (Đơn giản)

```html
<iframe 
    src="http://your-api-server.com/widget" 
    width="100%" 
    height="800"
    frameborder="0"
    style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
</iframe>
```

### Phương pháp 2: JavaScript Embed (Linh hoạt)

```html
<div id="hoancau-ai-widget"></div>
<script>
window.HoanCauConfig = {
    apiUrl: 'http://your-api-server.com',
    theme: 'light'
};
</script>
<script src="http://your-api-server.com/widget.js"></script>
```

### Phương pháp 3: API Integration (Tùy chỉnh hoàn toàn)

```javascript
async function analyzeCV(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', 'google');
    formData.append('model_name', 'gemini-1.5-flash');
    
    const response = await fetch('http://your-api-server.com/api/analyze-cv', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}
```

## 📡 API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/analyze-cv` | POST | Phân tích CV từ file upload |
| `/api/chat` | POST | Chat với AI về kết quả phân tích |
| `/api/models` | GET | Lấy danh sách AI models khả dụng |
| `/health` | GET | Kiểm tra trạng thái server |
| `/widget` | GET | Trang widget HTML |
| `/widget.js` | GET | Widget JavaScript |

## 🎨 Tùy chỉnh Giao diện

### CSS Override

```css
.hoancau-widget {
    /* Tùy chỉnh widget */
    border: 2px solid #your-brand-color;
    background: #your-background;
}

.widget-header {
    background: linear-gradient(135deg, #your-color1, #your-color2);
}
```

### JavaScript Configuration

```javascript
window.HoanCauConfig = {
    apiUrl: 'http://your-api-server.com',
    theme: 'light', // 'light' hoặc 'dark'
    width: '100%',
    maxWidth: '600px',
    language: 'vi' // 'vi' hoặc 'en'
};
```

## 💻 Desktop App Features

- ✅ Giao diện desktop native
- ✅ Tích hợp với Python backend
- ✅ File drag & drop
- ✅ System tray support
- ✅ Auto-updater (có thể thêm)
- ✅ Offline mode (tùy chọn)

### Desktop App Screenshots

```
┌─────────────────────────────────────────┐
│ 🎯 HoanCau AI Resume Processor    [●○○] │
├─────────────────────────────────────────┤
│                                         │
│   📄 Drag & drop CV files here         │
│                                         │
│   🚀 [Analyze CV]  📊 [View Results]   │
│                                         │
│   💬 Chat with AI about results        │
│                                         │
└─────────────────────────────────────────┘
```

## 🔒 Production Deployment

### 1. API Server Security

```python
# api_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 2. Environment Variables

```bash
# Production .env
GOOGLE_API_KEY=your_production_key
OPENROUTER_API_KEY=your_production_key
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 3. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "api_server.py"]
```

### 4. Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Usage Analytics

Widget tự động track:
- 📈 Số lượng CV được phân tích
- ⏱️ Thời gian xử lý trung bình  
- 🎯 Model AI được sử dụng nhiều nhất
- 🌍 Nguồn traffic (domain nhúng widget)

## 🆘 Troubleshooting

### Widget không load
```javascript
// Kiểm tra CORS
fetch('http://your-api-server.com/health')
    .then(response => response.json())
    .then(data => console.log('API Status:', data))
    .catch(error => console.error('CORS or API Error:', error));
```

### Desktop App không khởi động
```bash
# Kiểm tra Python backend
python api_server.py

# Kiểm tra Electron
npm run electron-dev
```

### API Server lỗi
```bash
# Kiểm tra logs
tail -f app.log

# Test API endpoints
curl http://localhost:8000/health
```

## 🎯 Next Steps

1. **📱 Mobile App** - React Native wrapper
2. **🔌 Browser Extension** - Chrome/Firefox extension
3. **📧 Email Integration** - Outlook/Gmail add-ins
4. **🤖 Slack Bot** - Slack workspace integration
5. **📊 Analytics Dashboard** - Usage statistics web app

## 📞 Hỗ trợ

- 📖 Documentation: `/static/embed.html`
- 🐛 Bug reports: GitHub Issues
- 💬 Chat support: Tích hợp trong widget
- 📧 Email: support@hoancau.ai

---

**🎉 Chúc bạn thành công với HoanCau AI!**
