# modules/cv_processor.py

import os
import re
import json
import time
import logging
from typing import List, Dict
import pandas as pd
import docx

# định nghĩa extractor PDF
try:
    from pdfminer.high_level import extract_text
    _PDF_EX = "pdfminer"
except ImportError:
    try:
        import PyPDF2
        _PDF_EX = "pypdf2"
    except ImportError:
        try:
            import fitz  # PyMuPDF
            _PDF_EX = "pymupdf"
        except ImportError:
            _PDF_EX = None

from .dynamic_llm_client import DynamicLLMClient
from .config import ATTACHMENT_DIR, OUTPUT_CSV
from .prompts import CV_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_h = logging.StreamHandler()
stream_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(stream_h)
logger.addHandler(logging.FileHandler("cv_processor.log"))  # log ra file

class CVProcessor:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher
        self.llm_client = DynamicLLMClient()

    def _extract_pdf(self, path: str) -> str:
        if _PDF_EX == "pdfminer":
            return extract_text(path)
        elif _PDF_EX == "pypdf2":
            from PyPDF2 import PdfReader
            txt = ""
            for p in PdfReader(path).pages:
                txt += p.extract_text() or ""
            return txt
        elif _PDF_EX == "pymupdf":
            import fitz
            doc = fitz.open(path)
            txt = "".join(p.get_text() for p in doc)
            doc.close()
            return txt
        logger.error("❌ Không có thư viện PDF phù hợp.")
        return ""

    def extract_text(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                return self._extract_pdf(path)
            if ext == ".docx":
                doc = docx.Document(path)
                return "\n".join(p.text for p in doc.paragraphs)
            logger.warning(f"⚠️ File không hỗ trợ: {path}")
        except Exception as e:
            logger.error(f"Lỗi đọc {path}: {e}")
        return ""

    def extract_info_with_llm(self, text: str) -> Dict:
        if not text.strip():
            return {}

        for attempt in range(1, 4):
            try:
                resp = self.llm_client.generate_content([CV_EXTRACTION_PROMPT, text])
                m = re.search(r'```json\s*([\s\S]+?)\s*```|({[\s\S]+})', resp)
                if m:
                    data = m.group(1) or m.group(2)
                    return json.loads(data)
                logger.warning(f"AI trả về không phải JSON: {resp}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"❌ Lỗi parse JSON: {e}")
                break
            except Exception as e:
                msg = str(e).lower()
                if any(x in msg for x in ("quota", "429", "resource_exhausted")) and attempt < 3:
                    wait = 2 ** attempt
                    logger.warning(f"Quota lỗi, retry sau {wait}s")
                    time.sleep(wait)
                    continue
                logger.error(f"❌ Lỗi GenAI: {e}")
                break

        logger.info("🔄 Dùng fallback regex")
        return self._fallback_regex(text)

    def _fallback_regex(self, text: str) -> Dict:
        patterns = {
            "ten": r"(?:(?:Họ tên|Tên)[\:\-\s]+)([^\n]+)",
            "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            "dien_thoai": r"(\+?\d[\d\-\s]{7,}\d)",
            "hoc_van": r"(?:(?:Học vấn|Education)[\:\-\s]+)([^\n]+)",
            "kinh_nghiem": r"(?:(?:Kinh nghiệm|Experience)[\:\-\s]+)([^\n]+)",
        }
        info = {}
        for k, p in patterns.items():
            m = re.search(p, text, re.IGNORECASE)
            info[k] = m.group(1).strip() if m else ""
        return info

    def process(self) -> pd.DataFrame:
        files = self.fetcher.fetch_cv_attachments() if self.fetcher else []
        if not files:
            logger.info("🔍 Dò thư mục attachments")
            files = [
                os.path.join(ATTACHMENT_DIR, f)
                for f in os.listdir(ATTACHMENT_DIR)
                if f.lower().endswith((".pdf", ".docx"))
            ]
        if not files:
            logger.info("ℹ️ Không có file CV.")
            return pd.DataFrame()

        rows = []
        for f in files:
            txt = self.extract_text(f)
            info = self.extract_info_with_llm(txt) or {}
            rows.append({
                "Nguồn": os.path.basename(f),
                "Họ tên": info.get("ten", ""),
                "Email": info.get("email", ""),
                "Điện thoại": info.get("dien_thoai", ""),
                "Học vấn": info.get("hoc_van", ""),
                "Kinh nghiệm": info.get("kinh_nghiem", ""),
            })

        return pd.DataFrame(rows)

    def save_to_csv(self, df: pd.DataFrame, output: str = OUTPUT_CSV):
        """Ghi đè file mỗi lần chạy. Nếu muốn append, đổi mode='a' và header=not exists."""
        df.to_csv(output, index=False, encoding="utf-8-sig")
        logger.info(f"✅ Lưu {len(df)} hồ sơ vào {output}")
