# modules/email_fetcher.py

import imaplib
import email
import os
import re
import logging
from typing import List

from .config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, ATTACHMENT_DIR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.addHandler(logging.FileHandler("email_fetcher.log"))  # log ra file

class EmailFetcher:
    def __init__(self, host: str = EMAIL_HOST, port: int = EMAIL_PORT,
                 user: str = EMAIL_USER, password: str = EMAIL_PASS):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.mail = None

    def connect(self) -> None:
        try:
            self.mail = imaplib.IMAP4_SSL(self.host, self.port)
            self.mail.login(self.user, self.password)
            self.mail.select("INBOX")
            logger.info("✅ Đã kết nối IMAP và chọn INBOX.")
        except Exception as e:
            logger.error(f"❌ Lỗi khi kết nối IMAP: {e}")
            raise

    def fetch_cv_attachments(self, keywords: List[str] = None) -> List[str]:
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        msg_nums = set()
        for key in keywords:
            # đúng cú pháp OR với bộ lọc IMAP
            typ, data = self.mail.search(None, f'(OR SUBJECT "{key}" BODY "{key}")')
            if typ == "OK" and data and data[0]:
                msg_nums.update(data[0].split())

        os.makedirs(ATTACHMENT_DIR, exist_ok=True)
        new_files = []

        for num in msg_nums:
            typ, msg_data = self.mail.fetch(num, "(RFC822)")
            if typ != "OK" or not msg_data:
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            logger.info(f"📨 Email từ: {msg.get('From', '<unknown>')}")

            for part in msg.walk():
                if part.get_content_maintype() == "application" and part.get("Content-Disposition"):
                    filename = part.get_filename()
                    if not filename:
                        continue
                    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
                    path = os.path.join(ATTACHMENT_DIR, safe)
                    if os.path.exists(path):
                        logger.info(f"➡️ Đã tồn tại: {path}")
                        continue
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    new_files.append(path)
                    logger.info(f"✅ Lưu đính kèm mới: {path}")

            # đánh dấu đã đọc
            self.mail.store(num, "+FLAGS", "\\Seen")

        if not new_files:
            logger.info("ℹ️ Không tìm thấy đính kèm mới.")
        return new_files
