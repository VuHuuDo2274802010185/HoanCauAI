# Widget Module

Thư mục này chứa các thành phần cho embeddable widget có thể nhúng vào các trang web khác.

## Files

### `widget.html`
- **Mục đích**: Giao diện HTML chính của widget
- **Chức năng**:
  - Upload CV (PDF/DOCX)
  - Cài đặt AI (provider, model, temperature)
  - Hiển thị kết quả phân tích
  - Chat với AI
- **Tính năng**:
  - Responsive design
  - Modern UI với gradient
  - File validation
  - Loading states
  - Error handling
- **Styling**: Inline CSS với theme hiện đại

### `widget.js`
- **Mục đích**: Logic JavaScript cho widget
- **Class**: `HoanCauWidget`
- **Chức năng**:
  - File upload handling
  - API communication
  - Real-time chat
  - Status management
  - Error handling
- **API Integration**: Kết nối với API server
- **Events**: File selection, analysis, chat

### `embed.html`
- **Mục đích**: Hướng dẫn và demo cách nhúng widget
- **Nội dung**:
  - 3 phương pháp nhúng (iframe, JS, API)
  - Code examples
  - Configuration options
  - Demo widget
  - Troubleshooting guide

## Cách sử dụng

### 1. Iframe Embed
```html
<iframe src="http://api-server/widget" width="100%" height="800"></iframe>
```

### 2. JavaScript Embed
```html
<div id="hoancau-widget"></div>
<script src="http://api-server/widget.js"></script>
```

### 3. Custom API Integration
```javascript
const widget = new HoanCauWidget('http://api-server');
```

## Cập nhật sau này

- Multi-language support (EN/VI)
- Dark/Light theme toggle
- Mobile optimization
- Accessibility improvements
- Widget customization options
- Analytics tracking
- Real-time notifications
- Batch CV processing
- Export results (PDF/Excel)
- Integration with popular CMS (WordPress, Drupal)
