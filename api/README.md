# API Module

Thư mục này chứa các thành phần liên quan đến API server cho việc nhúng widget.

## Files

### `api_server.py`
- **Mục đích**: FastAPI server chính cho embeddable API
- **Chức năng**: 
  - Xử lý upload và phân tích CV
  - Chat AI endpoint
  - Health check và monitoring
  - Serve static files cho widget
- **Endpoints**:
  - `POST /api/analyze-cv` - Phân tích CV
  - `POST /api/chat` - Chat với AI
  - `GET /api/models` - Lấy danh sách models
  - `GET /health` - Health check
  - `GET /widget` - Widget HTML
  - `GET /widget.js` - Widget JavaScript
- **Dependencies**: FastAPI, uvicorn, pydantic
- **Port**: 8000

## Cách chạy

```bash
cd api/
python api_server.py
```

## Cập nhật sau này

- Thêm authentication/authorization
- Rate limiting
- Caching cho API responses
- WebSocket support cho real-time updates
- API versioning
- OpenAPI documentation enhancements
