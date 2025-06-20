#!/usr/bin/env bash
set -e

GREEN="\033[0;32m"
RESET="\033[0m"

echo -e "${GREEN}======================================================"
echo -e "                RESUME AI - KHỞI ĐỘNG               "
echo -e "======================================================${RESET}"

# 1) Check Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 không tìm thấy. Cài đặt rồi chạy lại." >&2
  exit 1
fi

echo "Đã có Python: $(python3 --version)"

# 2) Activate virtualenv if available
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
  echo "Đã kích hoạt môi trường ảo."
else
  echo "Không tìm thấy môi trường ảo tại .venv, sẽ dùng Python hệ thống."
fi

# 3) Loading animation
spinner() {
  local chars='/-\\|'
  for i in {1..20}; do
    for j in {0..3}; do
      printf "\rĐang khởi động ứng dụng... %s" "${chars:j:1}"
      sleep 0.2
    done
  done
  echo
}

spinner

# 4) Launch Streamlit UI
streamlit run main_engine/app.py

echo "Ứng dụng đã thoát. Nhấn Ctrl+C để đóng terminal." 
