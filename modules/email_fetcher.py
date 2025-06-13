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
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(_handler)


class EmailFetcher:
    def __init__(self, host: str, port: int, user: str, password: str):
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

    def fetch_cv_attachments(self, keywords=None) -> List[str]:
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        msg_nums = set()
        for key in keywords:
            status, data = self.mail.search(None, 'OR', f'SUBJECT "{key}"', f'BODY "{key}"')
            if status == "OK" and data and data[0]:
                msg_nums.update(data[0].split())

        os.makedirs(ATTACHMENT_DIR, exist_ok=True)
        new_files = []

        for num in msg_nums:
            status, msg_data = self.mail.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            for part in msg.walk():
                content_disposition = part.get("Content-Disposition", "")
                if part.get_content_maintype() == "application" and "attachment" in content_disposition:
                    filename = part.get_filename()
                    if not filename:
                        continue
                    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
                    path = os.path.join(ATTACHMENT_DIR, safe_name)
                    if os.path.exists(path):
                        logger.info(f"➡️ Bỏ qua, đã tồn tại: {path}")
                        continue
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    new_files.append(path)
                    logger.info(f"✅ Đã lưu đính kèm mới: {path}")

            self.mail.store(num, "+FLAGS", "\\Seen")

        if not new_files:
            logger.info("ℹ️ Không tìm thấy đính kèm mới.")
        return new_files
