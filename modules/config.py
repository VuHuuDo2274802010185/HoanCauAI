# modules/config.py
import os
from pathlib import Path
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv()

# --- API key và client Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise RuntimeError("Thiếu GOOGLE_API_KEY trong .env")
genai.configure(api_key=GOOGLE_API_KEY)

# Model Gemini
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")

# Email IMAP
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Thư mục attachments & file xuất CSV
ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR", "attachments")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "cv_summary.csv")
Path(ATTACHMENT_DIR).mkdir(parents=True, exist_ok=True)

# Configure with your API key
genai.configure(api_key=GOOGLE_API_KEY)

# Now you can use genai.GenerativeModel, etc.
model = genai.GenerativeModel('gemini-pro')