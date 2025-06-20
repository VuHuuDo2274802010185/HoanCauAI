#!/usr/bin/env bash

set -e
export LC_ALL=C.UTF-8

YELLOW="\033[1;33m"
WHITE="\033[1;37m"
GREEN="\033[0;92m"
RESET="\033[0m"

echo -e "${GREEN}======================================================${RESET}"
if command -v lolcat >/dev/null 2>&1; then
  echo "             RESUME AI - SETUP SCRIPT             " | lolcat
else
  echo -e "${YELLOW}             RESUME AI - SETUP SCRIPT             ${RESET}"
fi
echo -e "${GREEN}======================================================${RESET}"

# 1) Check Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 không tìm thấy. Cài Python từ https://www.python.org rồi chạy lại." >&2
  exit 1
fi

echo "Đã có Python: $(python3 --version)"

# 2) Copy .env if missing
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Đã tạo file .env từ .env.example. Vui lòng chỉnh sửa giá trị."
  else
    echo "Không tìm thấy .env.example. Hãy tạo file .env thủ công." >&2
  fi
else
  echo "File .env đã tồn tại."
fi

# 3) Create virtual environment if missing
if [ ! -d .venv ]; then
  echo "Tạo virtual environment..."
  python3 -m venv .venv
else
  echo "Virtual environment đã tồn tại."
fi

# 4) Activate virtualenv
source .venv/bin/activate

# 5) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6) Create folders
mkdir -p attachments output log

echo -e "${YELLOW}Setup hoàn tất!${RESET}"
