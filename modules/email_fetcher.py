# modules/email_fetcher.py

import imaplib                   # thư viện IMAP4 để kết nối và tương tác với server email
import email                     # thư viện xử lý định dạng email (parser)
from email.header import decode_header  # decode header RFC2047
import os                        # thao tác hệ thống file và đường dẫn
import re                        # xử lý biểu thức chính quy
import logging                   # ghi log
from typing import List          # khai báo kiểu List

from .config import ATTACHMENT_DIR  # đường dẫn lưu file đính kèm


class EmailFetcher:
    """
    Lớp để kết nối IMAP, tìm email chứa CV/Resume và tải file đính kèm về máy.
    """

    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None):
        """
        Khởi tạo EmailFetcher với thông tin kết nối:
        - host, port, user, password: nếu không truyền, dùng biến từ config
        """
        from .config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS

        self.host = host or EMAIL_HOST
        self.port = port or EMAIL_PORT
        self.user = user or EMAIL_USER
        self.password = password or EMAIL_PASS
        self.mail = None

        # Thiết lập logger cho instance
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

    def connect(self) -> None:
        """
        Kết nối tới IMAP server và đăng nhập. Chọn mailbox 'INBOX'.
        """
        try:
            self.mail = imaplib.IMAP4_SSL(self.host, self.port)
            self.mail.login(self.user, self.password)
            self.mail.select("INBOX")
            self.logger.info(f"[OK] Đã kết nối IMAP: {self.user}@{self.host}")
        except Exception as e:
            self.logger.error(f"[ERR] Lỗi kết nối IMAP: {e}")
            raise

    def fetch_cv_attachments(self, keywords: List[str] = None) -> List[str]:
        """
        Tìm và tải xuống các file đính kèm của email có tiêu đề hoặc nội dung chứa bất kỳ từ khóa nào trong keywords.
        Trả về danh sách đường dẫn các file mới được lưu. Decode tên file đúng UTF-8 và giữ phần mở rộng.
        """
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        new_files: List[str] = []

        for key in keywords:
            typ, data = self.mail.search(None, f'(OR SUBJECT "{key}" BODY "{key}")')
            if typ != "OK" or not data or not data[0]:
                continue

            for num in data[0].split():
                typ, msg_data = self.mail.fetch(num, '(RFC822)')
                if typ != "OK" or not msg_data:
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue

                    raw_name = part.get_filename()
                    if not raw_name:
                        continue

                    # 1) Decode tên file theo RFC2047
                    decoded_parts = decode_header(raw_name)
                    filename = ''.join(
                        (p.decode(enc or 'utf-8') if isinstance(p, bytes) else p)
                        for p, enc in decoded_parts
                    )

                    # 2) Giữ lại phần mở rộng và sanitize tên
                    name, ext = os.path.splitext(filename)
                    safe_name = re.sub(r'[^\w\-\_ ]', '_', name)
                    safe = safe_name + ext

                    path = os.path.join(ATTACHMENT_DIR, safe)

                    # 3) Bỏ qua nếu file đã tồn tại
                    if os.path.exists(path):
                        self.logger.info(f"[INFO] Đã tồn tại: {path}")
                        continue

                    # 4) Ghi file nhị phân
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    new_files.append(path)
                    self.logger.info(f"[OK] Lưu đính kèm mới: {path}")

                # Đánh dấu email đã đọc
                self.mail.store(num, "+FLAGS", "\\Seen")

        if not new_files:
            self.logger.info("[INFO] Không tìm thấy đính kèm mới.")

        return new_files
