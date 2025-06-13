# config.py
import os
from pathlib import Path
from google import genai

from dotenv import load_dotenv
load_dotenv()

# --- API key và client Genie 2.0 Flash ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise RuntimeError("Thiếu GOOGLE_API_KEY trong .env")
genai_client = genai.Client(api_key=GOOGLE_API_KEY)

# Model Gemini 2.0 Flash (Developer API) :contentReference[oaicite:0]{index=0}
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")

# Email IMAP
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
if not EMAIL_USER or not EMAIL_PASS:
    raise RuntimeError("Thiếu EMAIL_USER hoặc EMAIL_PASS trong .env")

# Thư mục attachments & file xuất Excel
ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR", "attachments")
OUTPUT_EXCEL   = os.getenv("OUTPUT_EXCEL",   "cv_summary.xlsx")
Path(ATTACHMENT_DIR).mkdir(parents=True, exist_ok=True)
