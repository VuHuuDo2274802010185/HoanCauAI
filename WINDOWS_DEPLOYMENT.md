# 🪟 HoanCau AI Resume Processor - Windows Deployment Guide

## 📦 Các Phương Án Tạo Ứng Dụng Windows

Dự án cung cấp **3 cách** để tạo ứng dụng chạy trên Windows:

### 1. 🏗️ **EXE File (Khuyến nghị cho phân phối)**
Tạo file .exe độc lập, không cần cài Python trên máy đích.

```bash
# Chạy script build
python build_windows_exe.py

# Hoặc dùng batch file
build_exe.bat
```

**Ưu điểm:**
- ✅ Không cần cài Python trên máy đích
- ✅ File .exe độc lập, dễ phân phối
- ✅ Tự động tạo installer và shortcut
- ✅ Professional, giống phần mềm thương mại

**Nhược điểm:**
- ❌ File .exe khá lớn (100-200MB)
- ❌ Thời gian build lâu hơn
- ❌ Phức tạp hơn khi debug

### 2. 📦 **Portable App (Khuyến nghị cho sử dụng cá nhân)**
Tạo thư mục portable chứa toàn bộ ứng dụng.

```bash
# Chạy script tạo portable app
create_portable_app.bat
```

**Ưu điểm:**
- ✅ Nhanh, đơn giản
- ✅ Easy to modify và debug
- ✅ Nhỏ gọn (chỉ source code)
- ✅ Chạy trực tiếp từ thư mục

**Nhược điểm:**
- ❌ Cần cài Python trên máy đích
- ❌ Cần cài dependencies lần đầu

### 3. 🚀 **Quick Test Run**
Chạy thử nhanh ứng dụng trên máy hiện tại.

```bash
# Test nhanh
run_test.bat
```

---

## 🎯 Hướng Dẫn Chi Tiết

### 📋 Yêu Cầu Hệ Thống

- **Windows 10/11** (64-bit)
- **Python 3.8+** (chỉ cho Portable App)
- **RAM:** 2GB trống
- **Ổ cứng:** 500MB trống
- **Internet:** Cần kết nối để gọi AI API

### 🔧 Bước 1: Chuẩn Bị Build Environment

```bash
# Clone project
git clone <repository-url>
cd HoanCauAI

# Cài dependencies
pip install -r requirements.txt

# Tạo .env file
copy .env.example .env
# Sau đó edit .env với API keys
```

### 🏗️ Bước 2A: Build EXE File

```bash
# Chạy build script
python build_windows_exe.py

# Hoặc dùng batch file (đơn giản hơn)
build_exe.bat
```

**Kết quả:** 
- `dist/HoanCauAI_ResumeProcessor.exe` - File thực thi chính
- `installer.bat` - Script cài đặt tự động

**Cách sử dụng:**
1. Copy thư mục `dist` sang máy Windows đích
2. Chạy `installer.bat` để cài đặt
3. Chỉnh sửa `.env` file với API keys
4. Chạy từ desktop shortcut hoặc Start Menu

### 📦 Bước 2B: Tạo Portable App

```bash
# Chạy script tạo portable
create_portable_app.bat
```

**Kết quả:**
- `HoanCauAI_Portable/` - Thư mục ứng dụng portable
- `Start_HoanCauAI.bat` - Script khởi động
- `README.md` - Hướng dẫn sử dụng
- `.env` - File cấu hình

**Cách sử dụng:**
1. Copy thư mục `HoanCauAI_Portable` sang máy Windows đích
2. Cài Python trên máy đích (nếu chưa có)
3. Chỉnh sửa `.env` file với API keys  
4. Chạy `Start_HoanCauAI.bat`

### 🚀 Bước 2C: Quick Test

```bash
# Test nhanh trên máy hiện tại
run_test.bat
```

---

## ⚙️ Cấu Hình

### 🔑 API Keys Cần Thiết

Chỉnh sửa file `.env`:

```env
# Google AI (Gemini)
GOOGLE_API_KEY=AIzaSy...  # Lấy từ https://makersuite.google.com/app/apikey

# Email (Gmail)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password  # App Password, không phải mật khẩu thường
```

### 📧 Thiết Lập Gmail App Password

1. Vào **Google Account Settings**
2. **Security** → **2-Step Verification** (bật nếu chưa có)
3. **App passwords** → **Generate new password**
4. Chọn **Mail** và **Windows Computer**
5. Copy mật khẩu 16 ký tự vào `EMAIL_PASS`

---

## 🎉 Kết Quả

Sau khi build thành công, bạn sẽ có:

### EXE Version:
```
dist/
├── HoanCauAI_ResumeProcessor.exe   # Main executable
├── .env.example                    # Configuration template
└── static/                         # Web assets

installer.bat                       # Auto installer
```

### Portable Version:
```
HoanCauAI_Portable/
├── Start_HoanCauAI.bat            # Main launcher
├── Create_Desktop_Shortcut.bat    # Shortcut creator
├── README.md                      # User guide
├── .env                           # Configuration
├── src/                           # Application source
└── static/                        # Web assets
```

---

## 🌐 Sử Dụng Ứng Dụng

1. **Khởi động:** Chạy file .exe hoặc batch script
2. **Truy cập:** Browser tự động mở tại `http://localhost:8501`
3. **Cấu hình:** Nhập API keys trong giao diện web
4. **Sử dụng:** Upload CV, fetch email, chat với AI

### ✨ Tính Năng Chính:
- 📄 **Xử lý CV:** Upload và phân tích PDF/DOCX
- 📧 **Email Fetching:** Tự động lấy CV từ Gmail
- 🤖 **AI Chat:** Hỏi đáp về dữ liệu CV
- 📊 **Export:** Xuất kết quả CSV, Excel, JSON
- 🎨 **Themes:** 10+ giao diện đẹp

---

## 🛠️ Troubleshooting

### ❌ Lỗi Thường Gặp:

**"Python not found"**
- Cài Python từ https://python.org
- Tick "Add Python to PATH" khi cài

**"Module not found"**
- Chạy: `pip install -r requirements.txt`

**"Port 8501 already in use"**  
- Tắt Streamlit apps khác
- Hoặc đổi port trong code

**"API key invalid"**
- Kiểm tra API key trong .env
- Tạo API key mới nếu cần

**"Email connection failed"**
- Kiểm tra Gmail App Password
- Bật 2-Factor Authentication
- Cho phép "Less secure app access"

### 📞 Hỗ Trợ:
- **GitHub Issues:** https://github.com/VuHuuDo2274802010185/HoanCauAI/issues
- **Email:** vuhuudo2004@gmail.com
- **Documentation:** README.md files trong project

---

## 📋 Checklist Deploy

### Pre-Build:
- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with API keys
- [ ] Application tested locally (`run_test.bat`)

### EXE Build:
- [ ] Run `build_exe.bat`
- [ ] Check `dist/` folder contains .exe file
- [ ] Test .exe on clean Windows machine
- [ ] Create installer package

### Portable Build:
- [ ] Run `create_portable_app.bat`
- [ ] Check `HoanCauAI_Portable/` folder
- [ ] Test on Windows machine with Python
- [ ] Create usage documentation

### Distribution:
- [ ] Package files into ZIP
- [ ] Create user guide
- [ ] Test installation on target machines
- [ ] Provide support documentation

---

*Happy Building! 🎉*
