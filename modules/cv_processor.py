# modules/cv_processor.py
import os
import re
import json
import time
import logging
from typing import List, Dict, Optional
import pandas as pd
import pdfminer.high_level
import docx
from google.generativeai import GenerativeModel

from .config import LLM_MODEL, ATTACHMENT_DIR, OUTPUT_CSV
from .prompts import CV_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(_handler)


class CVProcessor:
    def __init__(self, fetcher=None, model_name: str = LLM_MODEL):
        self.fetcher = fetcher
        self.model = GenerativeModel(model_name)

    def extract_text(self, path: str) -> str:
        # ... (nội dung hàm không đổi)
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                return pdfminer.high_level.extract_text(path)
            elif ext == ".docx":
                doc = docx.Document(path)
                return "\n".join(p.text for p in doc.paragraphs)
            elif ext == ".doc":
                logger.warning(f"Không hỗ trợ tốt file .doc: {path}")
                return ""
        except Exception as e:
            logger.error(f"Lỗi khi đọc file {path}: {e}")
        return ""


    def extract_info_with_llm(self, text: str) -> Dict:
        if not text.strip():
            return {}

        for attempt in range(1, 4):
            try:
                # Sử dụng prompt từ file prompts.py
                resp = self.model.generate_content([CV_EXTRACTION_PROMPT, text])
                logger.debug(f"Phản hồi AI: {resp.text}")

                # Trích xuất JSON an toàn hơn
                json_match = re.search(r'```json\s*([\s\S]+?)\s*```|({[\s\S]+})', resp.text)
                if json_match:
                    json_str = json_match.group(1) or json_match.group(2)
                    return json.loads(json_str)
                else:
                    logger.warning(f"AI không trả về JSON hợp lệ. Chuyển sang fallback. Phản hồi: {resp.text}")
                    break

            except json.JSONDecodeError as e:
                logger.error(f"Lỗi parse JSON từ AI: {e}. Phản hồi: {resp.text}")
                break
            except Exception as e:
                msg = str(e).lower()
                if ("quota" in msg or "429" in msg or "resource_exhausted" in msg) and attempt < 3:
                    sleep_time = 2 ** attempt
                    logger.warning(f"Lỗi quota, thử lại sau {sleep_time} giây...")
                    time.sleep(sleep_time)
                    continue
                logger.error(f"Lỗi GenAI SDK: {e}")
                break

        logger.info("Chạy regex fallback.")
        return self._fallback_regex(text)

    def _fallback_regex(self, text: str) -> Dict:
        # ... (nội dung hàm không đổi)
        info: Dict[str, str] = {}
        patterns = {
            "ten": r"(?:(?:Họ tên|Tên|Name)[\s\:—\-]+)([^\n\r]+)",
            "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            "dien_thoai": r"(?:(?:Điện thoại|Phone)[\s\:—\-]+)?(\+?\d[\d\-\s]{7,}\d)",
            "hoc_van": r"(?:(?:Học vấn|Education)[\s\:—\-]+)([^\n\r]+)",
            "kinh_nghiem": r"(?:(?:Kinh nghiệm|Experience)[\s\:—\-]+)([^\n\r]+)",
        }
        for key, pat in patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            info[key] = m.group(1).strip() if m else ""
        return info


    def process(self) -> pd.DataFrame:
        new_files: List[str] = []
        if self.fetcher:
             new_files = self.fetcher.fetch_cv_attachments()

        if not new_files:
            logger.info("Không tìm thấy đính kèm mới, tổng hợp tất cả CV hiện có trong thư mục 'attachments'.")
            attachments = [
                os.path.join(ATTACHMENT_DIR, fname)
                for fname in os.listdir(ATTACHMENT_DIR)
                if fname.lower().endswith((".pdf", ".docx"))
            ]
        else:
            attachments = new_files
        
        if not attachments:
            logger.info("Không có file CV nào để xử lý.")
            return pd.DataFrame()

        records = []
        for path in attachments:
            text = self.extract_text(path)
            info = self.extract_info_with_llm(text)
            records.append({
                "Nguồn": os.path.basename(path),
                "Họ tên": info.get("ten", ""),
                "Email": info.get("email", ""),
                "Điện thoại": info.get("dien_thoai", ""),
                "Học vấn": info.get("hoc_van", ""),
                "Kinh nghiệm": info.get("kinh_nghiem", "")
            })

        df = pd.DataFrame(records)
        return df

    def save_to_csv(self, df: pd.DataFrame, output: str = OUTPUT_CSV):
        # Xuất ra file CSV, sử dụng utf-8-sig để Excel đọc tiếng Việt không bị lỗi
        df.to_csv(output, index=False, encoding='utf-8-sig')
        logger.info(f"Đã lưu {len(df)} hồ sơ vào {output}.")