# modules/cv_processor.py
import os
import re
import json
import time
import logging
from typing import List, Dict
import pandas as pd
import pdfminer.high_level
import docx

from .config import genai_client, LLM_MODEL, ATTACHMENT_DIR, OUTPUT_EXCEL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(_handler)


class CVProcessor:
    def __init__(self, fetcher, model: str = LLM_MODEL):
        self.fetcher = fetcher
        self.model = model

    def extract_text(self, path: str) -> str:
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

        system_prompt = (
            "Bạn là trợ lý AI chuyên trích xuất thông tin từ CV. "
            "Hãy trả về JSON với các khóa: ten, email, dien_thoai, hoc_van, kinh_nghiem."
        )

        for attempt in range(1, 4):
            try:
                resp = genai_client.generate_content(
                    model=self.model,
                    contents=[{"text": system_prompt}, {"text": text}]
                )
                logger.debug(f"Phản hồi AI: {resp.text}")
                return json.loads(resp.text)
            except Exception as e:
                msg = str(e).lower()
                if ("quota" in msg or "429" in msg) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"Lỗi GenAI SDK: {e}")
                break

        logger.info("Chạy regex fallback.")
        return self._fallback_regex(text)

    def _fallback_regex(self, text: str) -> Dict:
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
        new_files: List[str] = self.fetcher.fetch_cv_attachments()

        if not new_files:
            logger.info("Không tìm thấy đính kèm mới, tổng hợp tất cả CV hiện có.")
            attachments = [
                os.path.join(ATTACHMENT_DIR, fname)
                for fname in os.listdir(ATTACHMENT_DIR)
                if fname.lower().endswith((".pdf", ".docx", ".doc"))
            ]
        else:
            attachments = new_files

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
        if df.empty:
            df = pd.DataFrame(columns=["Nguồn", "Họ tên", "Email", "Điện thoại", "Học vấn", "Kinh nghiệm"])

        return df

    def save_to_excel(self, df: pd.DataFrame, output: str = OUTPUT_EXCEL):
        if os.path.exists(output):
            try:
                os.remove(output)
                logger.info(f"Đã xóa file cũ: {output}")
            except Exception as e:
                logger.warning(f"Không xóa được file cũ ({output}): {e}")

        with pd.ExcelWriter(output, engine='xlsxwriter', mode='w') as writer:
            df.to_excel(writer, sheet_name='CV Summary', index=False)
            workbook  = writer.book
            worksheet = writer.sheets['CV Summary']

            header_fmt = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D7E4BC',
                'border': 1
            })
            cell_fmt = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1
            })

            for col_idx, col in enumerate(df.columns):
                worksheet.write(0, col_idx, col, header_fmt)
                series = df[col].astype(str)
                max_length = max(series.map(len).max(), len(col)) + 2
                worksheet.set_column(col_idx, col_idx, max_length, cell_fmt)

            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            worksheet.freeze_panes(1, 0)

        logger.info(f"Đã lưu {len(df)} hồ sơ vào {output}.")
