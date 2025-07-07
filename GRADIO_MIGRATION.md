# Chuyển đổi từ Streamlit sang Gradio - Hoàn Cầu AI CV Processor

## Tổng quan

Dự án này đã được chuyển đổi từ giao diện Streamlit sang Gradio để cung cấp trải nghiệm người dùng tốt hơn và tích hợp dễ dàng hơn.

## Thay đổi chính

### 1. File mới được tạo

- `src/main_engine/gradio_app.py` - Ứng dụng Gradio chính
- `run_gradio.py` - Script khởi chạy Gradio
- `start_gradio_linux.sh` - Script khởi động cho Linux
- `start_gradio_window.cmd` - Script khởi động cho Windows
- `test_gradio.py` - Test app đơn giản

### 2. Cập nhật dependencies

- Thêm `gradio>=4.0.0` vào `requirements.txt`
- Thêm `GradioProgressBar` class vào `modules/progress_manager.py`

### 3. Chuyển đổi UI Components

#### Streamlit → Gradio Mapping

| Streamlit | Gradio | Ghi chú |
|-----------|--------|---------|
| `st.tabs()` | `gr.Tabs()` với `gr.TabItem()` | Cấu trúc tương tự |
| `st.sidebar` | `gr.Column(scale=1)` | Sidebar thành cột bên trái |
| `st.button()` | `gr.Button()` | Tương đương |
| `st.text_input()` | `gr.Textbox()` | Tương đương |
| `st.selectbox()` | `gr.Dropdown()` | Tương đương |
| `st.file_uploader()` | `gr.File()` | Tương đương |
| `st.progress()` | `gr.Progress()` | Context manager |
| `st.chat_message()` | `gr.Chatbot()` | Component chat chuyên dụng |

### 4. Tính năng chính được chuyển đổi

#### ✅ Đã hoàn thành:
- [x] Cấu hình LLM (Provider, API Key, Model)
- [x] Cấu hình Email
- [x] Tab "Lấy & Xử lý CV" với progress tracking
- [x] Tab "Single File" - xử lý file đơn lẻ
- [x] Tab "Kết quả" - hiển thị dữ liệu đã xử lý
- [x] Tab "Hỏi AI" - chat với AI về CV
- [x] System status monitoring
- [x] Custom CSS styling
- [x] Error handling

#### 🔄 Đang phát triển:
- [ ] Real-time progress updates
- [ ] File download functionality
- [ ] Advanced chat features

### 5. Cách chạy ứng dụng

#### Linux/MacOS:
```bash
chmod +x start_gradio_linux.sh
./start_gradio_linux.sh
```

#### Windows:
```cmd
start_gradio_window.cmd
```

#### Manual:
```bash
pip install -r requirements.txt
python run_gradio.py
```

### 6. URL truy cập

Sau khi khởi chạy thành công:
- Local: `http://localhost:7860`
- Network: `http://0.0.0.0:7860`

## Ưu điểm của Gradio so với Streamlit

### 1. Performance
- ⚡ Khởi động nhanh hơn
- 🔄 Hot reload tốt hơn
- 📱 Responsive trên mobile

### 2. User Experience  
- 🎨 Interface đẹp hơn out-of-the-box
- 💬 Chat interface tự nhiên hơn
- 📊 Progress tracking mượt mà hơn

### 3. Development
- 🐍 Pure Python, không cần special syntax
- 🔧 Event handling rõ ràng hơn
- 🧪 Testing dễ dàng hơn

### 4. Deployment
- 🌐 Dễ deploy lên Hugging Face Spaces
- 📦 Bundle size nhỏ hơn
- 🔐 Built-in authentication

## Migration Notes

### State Management
- Streamlit: `st.session_state`
- Gradio: `AppState` class + function parameters

### Event Handling
- Streamlit: Rerun-based
- Gradio: Event-driven với callbacks

### Progress Tracking
- Streamlit: `st.progress()` + containers
- Gradio: `gr.Progress()` context manager

### File Handling
- Streamlit: `st.file_uploader()` returns UploadedFile
- Gradio: `gr.File()` returns file path/object

## Troubleshooting

### 1. Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"
```

### 2. Port Issues
```python
# Change port in gradio_app.py
app.launch(server_port=7861)  # Use different port
```

### 3. Dependencies
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Development Roadmap

### Phase 1: Core Migration ✅
- Basic UI components
- Main functionality
- Essential features

### Phase 2: Enhancement 🔄
- Advanced progress tracking
- Better error handling
- Performance optimization

### Phase 3: Advanced Features 📋
- Real-time collaboration
- Advanced analytics
- API integration

## Contributing

Khi đóng góp code:
1. Test cả Streamlit và Gradio versions
2. Update documentation
3. Ensure backward compatibility
4. Follow existing code style

## Notes

- File `app.py` (Streamlit) vẫn được giữ lại để tương thích ngược
- Gradio app chạy độc lập, không phụ thuộc Streamlit
- Có thể chạy song song cả hai phiên bản
