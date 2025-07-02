# modules/email_fetcher.py

import imaplib                   # thư viện IMAP4 để kết nối và tương tác với server email
import email                     # thư viện xử lý định dạng email (parser)
from email.header import decode_header  # decode header RFC2047
import os                        # thao tác hệ thống file và đường dẫn
import re                        # xử lý biểu thức chính quy
import time                      # sleep and delay functions
import logging                   # ghi log
from datetime import date, datetime, timezone, timedelta  # dùng để lọc email và tạo timestamp
from typing import List, Optional, Tuple
from email.utils import parsedate_to_datetime

from .config import ATTACHMENT_DIR, EMAIL_UNSEEN_ONLY  # đường dẫn lưu file đính kèm và chế độ quét
from .sent_time_store import record_sent_time

# --- Logger của module (tránh nhân đôi handler khi tạo nhiều instance) ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(_h)


class EmailFetcher:
    """
    Lớp để kết nối IMAP, tìm email chứa CV/Resume và tải file đính kèm về máy.
    Sau mỗi lần gọi ``fetch_cv_attachments()``, thông tin (path, thời gian gửi)
    của các file mới sẽ được lưu trong ``last_fetch_info``.
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
        self.last_fetch_info: List[Tuple[str, str | None]] = []

        # Sử dụng logger chung của module (không thêm handler mới)
        self.logger = logger

    def connect(self) -> None:
        """
        Enhanced IMAP connection with better error handling and validation
        """
        try:
            # Validate connection parameters
            if not self.host or not self.user or not self.password:
                raise ValueError("Missing required connection parameters (host/user/password)")
            
            if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
                raise ValueError(f"Invalid port number: {self.port}")
            
            self.logger.info(f"Connecting to IMAP server: {self.host}:{self.port}")
            
            # Establish SSL connection with timeout
            self.mail = imaplib.IMAP4_SSL(self.host, self.port)
            
            # Login with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.mail.login(self.user, self.password)
                    break
                except imaplib.IMAP4.error as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"Login attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            # Select INBOX
            status, messages = self.mail.select("INBOX")
            if status != 'OK':
                raise imaplib.IMAP4.error(f"Failed to select INBOX: {messages}")
            
            total_messages = int(messages[0]) if messages and messages[0] else 0
            
            self.logger.info(f"✅ IMAP connection successful: {self.user}@{self.host} (Total messages: {total_messages})")
            
        except imaplib.IMAP4.error as e:
            self.logger.error(f"IMAP error: {e}")
            raise ConnectionError(f"IMAP connection failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected connection error: {e}")
            raise

    def fetch_cv_attachments(
        self,
        keywords: Optional[List[str]] = None,
        since: Optional[date] = None,
        before: Optional[date] = None,
        batch_size: int = 100,
        unseen_only: bool = EMAIL_UNSEEN_ONLY,
    ) -> List[str]:
        """
        Tìm và tải xuống file đính kèm PDF/DOCX từ các email thoả mãn:
        - Tiêu đề hoặc nội dung chứa bất kỳ từ khoá nào trong ``keywords``.
        - Ngày gửi >= ``since`` và < ``before`` nếu được cung cấp
          (``before`` được hiểu là mốc kết thúc, không bao gồm ngày này).
        Quét theo từng đợt ``batch_size`` email mới nhất.
        Nếu ``unseen_only`` được bật (mặc định), chỉ tìm trong các email chưa đọc
        để tránh quét lại những thư đã xử lý.
        Thông tin path và thời gian gửi của mỗi file tải được
        sẽ lưu trong ``last_fetch_info``.
        """
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        new_files: List[str] = []
        self.last_fetch_info = []

        # --- Tìm email với optional SINCE ---
        criteria = ['UNSEEN'] if unseen_only else ['ALL']
        if since:
            criteria += ['SINCE', since.strftime('%d-%b-%Y')]
        if before:
            # "BEFORE" của IMAP là mốc không bao gồm ngày chỉ định,
            # nên cần cộng thêm 1 ngày để bao gồm toàn bộ ``before``
            next_day = before + timedelta(days=1)
            criteria += ['BEFORE', next_day.strftime('%d-%b-%Y')]

        typ, data = self.mail.search(None, *criteria)
        if typ != 'OK':
            self.logger.error(f"[ERR] Lỗi tìm email: {typ}")
            return []

        email_ids = data[0].split() if data and data[0] else []
        # Sắp xếp ID giảm dần để lấy email mới trước
        email_ids.sort(key=lambda x: int(x), reverse=True)
        self.logger.info(f"[INFO] Đã tìm thấy {len(email_ids)} email trong hộp thư.")

        for start in range(0, len(email_ids), batch_size):
            batch = email_ids[start:start + batch_size]
            for num in batch:
                # Fetch both message and INTERNALDATE for accurate timestamp
                typ, msg_data = self.mail.fetch(num, '(RFC822 INTERNALDATE)')
                if typ != "OK" or not msg_data:
                    continue

                raw_msg = None
                internal_date = None
                for item in msg_data:
                    if isinstance(item, tuple):
                        header = item[0] or b''
                        payload = item[1]
                        if raw_msg is None and isinstance(payload, (bytes, bytearray)):
                            raw_msg = payload
                        if header.strip().upper() == b'INTERNALDATE' and isinstance(payload, (bytes, bytearray)):
                            internal_date = payload.decode().strip('"')
                        else:
                            m = re.search(br'INTERNALDATE "([^"]+)"', header)
                            if m:
                                internal_date = m.group(1).decode()
                            if not internal_date and isinstance(payload, (bytes, bytearray)):
                                m = re.search(br'INTERNALDATE "([^"]+)"', payload)
                                if m:
                                    internal_date = m.group(1).decode()
                    elif isinstance(item, bytes):
                        m = re.search(br'INTERNALDATE "([^"]+)"', item)
                        if m:
                            internal_date = m.group(1).decode()

                if raw_msg is None:
                    continue

                msg = email.message_from_bytes(raw_msg)

                # Determine sent time, prefer INTERNALDATE over Date header
                sent_time: str | None = ""
                if internal_date:
                    try:
                        dt = parsedate_to_datetime(internal_date)
                        sent_time = dt.isoformat()
                    except Exception:
                        try:
                            tup = imaplib.Internaldate2tuple(f'INTERNALDATE "{internal_date}"'.encode())
                            if tup:
                                dt = datetime.fromtimestamp(time.mktime(tup), tz=datetime.timezone.utc)
                                sent_time = dt.isoformat()
                        except Exception:
                            sent_time = ""
                if not sent_time:
                    date_hdr = msg.get('Date')
                    if date_hdr:
                        try:
                            dt = parsedate_to_datetime(date_hdr)
                            sent_time = dt.isoformat()
                        except Exception:
                            sent_time = ""

                # Lấy tiêu đề và nội dung để lọc theo keywords
                try:
                    subj_hdr = msg.get('Subject', '')
                    subj = ''.join(
                        p.decode(enc or 'utf-8', errors='ignore') if isinstance(p, bytes) else p
                        for p, enc in decode_header(subj_hdr)
                    )
                except Exception:
                    subj = ''

                body_text = ''
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain' and not part.get_filename():
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_text += part.get_payload(decode=True).decode(charset, errors='ignore')
                        except Exception:
                            pass

                all_text = f"{subj}\n{body_text}".lower()
                if not any(kw.lower() in all_text for kw in keywords):
                    continue

                self.logger.info(f"[DEBUG] Email ID {num.decode()}: {subj}")

                # Xử lý phần đính kèm mọi email: mỗi part có filename và đuôi PDF/DOCX
                for part in msg.walk():
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
                    if ext.lower() not in ['.pdf', '.docx']:
                        continue
                    if not re.search(r"(cv|resume)", name, re.IGNORECASE):
                        continue
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
                    self.last_fetch_info.append((path, sent_time))
                    try:
                        record_sent_time(path, sent_time)
                    except Exception as e:
                        self.logger.warning(f"Could not record sent time for {path}: {e}")
                    self.logger.info(f"[OK] Lưu đính kèm mới: {path}")

                # Đánh dấu email đã đọc để tránh xử lý lại lần sau
                try:
                    self.mail.store(num, "+FLAGS", "\\Seen")
                except Exception:
                    pass

        if not new_files:
            self.logger.info("[INFO] Không tìm thấy đính kèm mới.")

        return new_files
