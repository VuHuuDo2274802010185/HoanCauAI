# -*- coding: utf-8 -*-
# Script kiểm tra nhanh môi trường dự án Hoàn Cầu AI

import sys  # Thư viện hệ thống để lấy thông tin phiên bản
import importlib  # Dùng để thử import các gói cần thiết
from pathlib import Path  # Hỗ trợ thao tác đường dẫn

# Thư mục gốc của dự án (cha của thư mục scripts)
BASE_DIR = Path(__file__).resolve().parent.parent
# Danh sách lưu trữ các lỗi phát hiện được
errors = []

# --- Kiểm tra phiên bản Python ---
if sys.version_info < (3, 7):  # Yêu cầu tối thiểu Python 3.7
    errors.append("Python 3.7+ is required")

# --- Kiểm tra gói bắt buộc ---
try:
    importlib.import_module('streamlit')  # thử import streamlit
except ImportError:
    errors.append("Missing required package: streamlit")  # báo lỗi nếu thiếu

# --- Kiểm tra các thư mục cần thiết ---
for d in ["attachments", "csv", "log", "static"]:
    if not (BASE_DIR / d).is_dir():  # nếu thư mục không tồn tại
        errors.append(f"Missing directory: {d}")

# --- Kiểm tra file cấu hình môi trường ---
if not (BASE_DIR / '.env').is_file():
    errors.append(".env file not found")

# --- In kết quả kiểm tra ---
if errors:  # Nếu có lỗi
    print("Health check failed:")
    for e in errors:
        print(f" - {e}")  # Liệt kê từng lỗi
    sys.exit(1)  # Thoát với mã lỗi

print("All checks passed")  # Không có lỗi
