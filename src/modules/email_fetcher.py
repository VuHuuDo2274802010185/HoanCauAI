# modules/email_fetcher.py

import imaplib                   # thư viện IMAP4 để kết nối và tương tác với server email
import email                     # thư viện xử lý định dạng email (parser)
from email.header import decode_header  # decode header RFC2047
import os                        # thao tác hệ thống file và đường dẫn
import re                        # xử lý biểu thức chính quy
import time                      # sleep and delay functions
import logging                   # ghi log
from datetime import date, datetime, timezone, timedelta  # dùng để lọc email và tạo timestamp
from typing import List, Optional, Tuple, Dict
from email.utils import parsedate_to_datetime

from .config import ATTACHMENT_DIR, EMAIL_UNSEEN_ONLY
from .sent_time_store import record_sent_time
from .uid_store import load_last_uid, save_last_uid

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

    # ------------------------------------------------------------------
    def _fetch_headers_batch(self, uids: List[bytes]) -> List[Dict[str, str]]:
        """Fetch headers and bodystructure for a batch of UIDs."""
        uid_str = ",".join(uid.decode() if isinstance(uid, bytes) else str(uid) for uid in uids)
        if hasattr(self.mail, 'uid'):
            typ, data = self.mail.uid('fetch', uid_str, '(BODY.PEEK[HEADER] BODYSTRUCTURE UID INTERNALDATE)')
        else:
            typ, data = self.mail.fetch(uid_str, '(BODY.PEEK[HEADER] BODYSTRUCTURE UID INTERNALDATE)')
        if typ != 'OK' or not data:
            return []

        messages: List[Dict[str, str]] = []
        i = 0
        current: Dict[str, str] = {}
        while i < len(data):
            item = data[i]
            if isinstance(item, tuple) and b'BODY[HEADER]' in item[0]:
                if current:
                    messages.append(current)
                    current = {}
                header_meta = item[0]
                header_bytes = item[1] or b''
                uid_match = re.search(br'UID (\d+)', header_meta)
                uid_val = uid_match.group(1).decode() if uid_match else header_meta.split()[0].decode()
                date_match = re.search(br'INTERNALDATE "([^"]+)"', header_meta)
                internal_date = date_match.group(1).decode() if date_match else ''
                current = {
                    'uid': uid_val,
                    'header': header_bytes,
                    'internaldate': internal_date,
                    'bodystructure': ''
                }
            elif isinstance(item, tuple) and b'BODYSTRUCTURE' in item[0]:
                if not current:
                    current = {'uid': '', 'header': b'', 'internaldate': '', 'bodystructure': ''}
                current['bodystructure'] += item[0].decode()
                date_match = re.search(r'INTERNALDATE "([^"]+)"', item[0].decode())
                if date_match:
                    current['internaldate'] = date_match.group(1)
                uid_match = re.search(r'UID (\d+)', item[0].decode())
                if uid_match:
                    current['uid'] = uid_match.group(1)
            elif isinstance(item, bytes):
                if current and current.get('bodystructure') and item.strip() not in {b'', b')'}:
                    current['bodystructure'] += item.decode()
                elif current and not current.get('bodystructure') and item.strip() not in {b'', b')'}:
                    current['header'] += item
            i += 1
        if current:
            messages.append(current)
        return messages

    @staticmethod
    def _has_cv_attachment(bodystructure: str) -> bool:
        """Check BODYSTRUCTURE for CV attachment."""
        if not bodystructure:
            return False
        m = re.search(r'"(?:name|filename)" "([^\"]*\.(?:pdf|docx))"', bodystructure, re.IGNORECASE)
        if not m:
            return False
        fname = m.group(1)
        return bool(re.search(r'(cv|resume)', fname, re.IGNORECASE))

    def fetch_cv_attachments(
        self,
        keywords: Optional[List[str]] = None,
        since: Optional[date] = None,
        before: Optional[date] = None,
        batch_size: int = 100,
        unseen_only: bool = EMAIL_UNSEEN_ONLY,
        progress_callback=None,
        fast_mode: bool = False,
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
        Args:
            progress_callback: Hàm callback để báo cáo tiến trình (current, total, message)
        """
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        new_files: List[str] = []
        self.last_fetch_info = []

        # --- Tìm email với optional SINCE và UID range ---
        criteria = ['UNSEEN'] if unseen_only else ['ALL']
        if since:
            criteria += ['SINCE', since.strftime('%d-%b-%Y')]
        if before:
            # "BEFORE" của IMAP là mốc không bao gồm ngày chỉ định,
            # nên cần cộng thêm 1 ngày để bao gồm toàn bộ ``before``
            next_day = before + timedelta(days=1)
            criteria += ['BEFORE', next_day.strftime('%d-%b-%Y')]

        last_uid = load_last_uid()
        if last_uid:
            criteria = ['UID', f'{last_uid + 1}:*'] + criteria

        if hasattr(self.mail, 'uid'):
            typ, data = self.mail.uid('search', None, *criteria)
        else:
            typ, data = self.mail.search(None, *criteria)
        if typ != 'OK':
            self.logger.error(f"[ERR] Lỗi tìm email: {typ}")
            return []

        email_ids = data[0].split() if data and data[0] else []
        # Sắp xếp ID giảm dần để lấy email mới trước
        email_ids.sort(key=lambda x: int(x), reverse=True)
        total_emails = len(email_ids)
        self.logger.info(f"[INFO] Đã tìm thấy {total_emails} email trong hộp thư.")
        
        if progress_callback:
            progress_callback(0, total_emails, "Bắt đầu quét email...")

        if not fast_mode:
            max_uid_seen = 0
            processed_count = 0
            for start in range(0, len(email_ids), batch_size):
                batch = email_ids[start:start + batch_size]
                for num in batch:
                    processed_count += 1
                    if progress_callback:
                        progress_callback(processed_count, total_emails, f"Đang xử lý email {processed_count}/{total_emails}")
                
                # Fetch both message and INTERNALDATE for accurate timestamp
                # Fetch both message and INTERNALDATE for accurate timestamp
                if hasattr(self.mail, 'uid'):
                    typ, msg_data = self.mail.uid('fetch', num, '(RFC822 INTERNALDATE)')
                    uid_int = int(num)
                else:
                    typ, msg_data = self.mail.fetch(num, '(RFC822 INTERNALDATE)')
                    uid_int = int(num)
                if typ != "OK" or not msg_data:
                    continue
                if uid_int > max_uid_seen:
                    max_uid_seen = uid_int

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
                                dt = datetime.fromtimestamp(time.mktime(tup), tz=timezone.utc)
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

                # Chỉ log debug nếu không có progress_callback
                if not progress_callback:
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
                        if not progress_callback:
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
                    if not progress_callback:
                        self.logger.info(f"[OK] Lưu đính kèm mới: {path}")

                # Đánh dấu email đã đọc để tránh xử lý lại lần sau
                try:
                    self.mail.store(num, "+FLAGS", "\\Seen")
                except Exception:
                    pass

            if not new_files:
                if not progress_callback:
                    self.logger.info("[INFO] Không tìm thấy đính kèm mới.")

            if progress_callback:
                progress_callback(total_emails, total_emails, f"Hoàn thành! Tìm thấy {len(new_files)} file mới.")

            if max_uid_seen:
                try:
                    save_last_uid(max_uid_seen)
                except Exception as e:
                    self.logger.warning(f"Could not save last UID: {e}")

            return new_files

        else:
            # Optimized mode: fetch headers in batch first
            max_uid_seen = 0
            processed_count = 0
            for start in range(0, len(email_ids), batch_size):
                batch = email_ids[start:start + batch_size]
                infos = self._fetch_headers_batch(batch)
                for info in infos:
                    processed_count += 1
                    if progress_callback:
                        progress_callback(processed_count, total_emails, f"Đang xử lý email {processed_count}/{total_emails}")

                    uid = info.get('uid')
                    if not uid:
                        continue
                    uid_int = int(uid)
                    if uid_int > max_uid_seen:
                        max_uid_seen = uid_int

                    internal_date = info.get('internaldate', '')
                    header_bytes = info.get('header', b'')
                    bodystructure = info.get('bodystructure', '')

                    msg_header = email.message_from_bytes(header_bytes)
                    try:
                        subj_hdr = msg_header.get('Subject', '')
                        subj = ''.join(
                            p.decode(enc or 'utf-8', errors='ignore') if isinstance(p, bytes) else p
                            for p, enc in decode_header(subj_hdr)
                        )
                    except Exception:
                        subj = ''

                    if not any(kw.lower() in subj.lower() for kw in keywords):
                        continue
                    if not self._has_cv_attachment(bodystructure):
                        continue

                    if hasattr(self.mail, 'uid'):
                        typ, full_data = self.mail.uid('fetch', uid, '(RFC822)')
                    else:
                        typ, full_data = self.mail.fetch(uid, '(RFC822)')
                    if typ != 'OK' or not full_data:
                        continue
                    raw_msg = None
                    for it in full_data:
                        if isinstance(it, tuple) and isinstance(it[1], (bytes, bytearray)):
                            raw_msg = it[1]
                            break
                    if raw_msg is None:
                        continue

                    msg = email.message_from_bytes(raw_msg)

                    sent_time: str | None = ""
                    if internal_date:
                        try:
                            dt = parsedate_to_datetime(internal_date)
                            sent_time = dt.isoformat()
                        except Exception:
                            try:
                                tup = imaplib.Internaldate2tuple(f'INTERNALDATE "{internal_date}"'.encode())
                                if tup:
                                    dt = datetime.fromtimestamp(time.mktime(tup), tz=timezone.utc)
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

                    if not progress_callback:
                        self.logger.info(f"[DEBUG] Email ID {uid}: {subj}")

                    for part in msg.walk():
                        raw_name = part.get_filename()
                        if not raw_name:
                            continue

                        decoded_parts = decode_header(raw_name)
                        filename = ''.join(
                            (p.decode(enc or 'utf-8') if isinstance(p, bytes) else p)
                            for p, enc in decoded_parts
                        )

                        name, ext = os.path.splitext(filename)
                        if ext.lower() not in ['.pdf', '.docx']:
                            continue
                        if not re.search(r"(cv|resume)", name, re.IGNORECASE):
                            continue
                        safe_name = re.sub(r'[^\w\-\_ ]', '_', name)
                        safe = safe_name + ext

                        path = os.path.join(ATTACHMENT_DIR, safe)

                        if os.path.exists(path):
                            if not progress_callback:
                                self.logger.info(f"[INFO] Đã tồn tại: {path}")
                            continue

                        with open(path, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        new_files.append(path)
                        self.last_fetch_info.append((path, sent_time))
                        try:
                            record_sent_time(path, sent_time)
                        except Exception as e:
                            self.logger.warning(f"Could not record sent time for {path}: {e}")
                        if not progress_callback:
                            self.logger.info(f"[OK] Lưu đính kèm mới: {path}")

                    try:
                        if hasattr(self.mail, 'uid'):
                            self.mail.uid('store', uid, "+FLAGS", "\\Seen")
                        else:
                            self.mail.store(uid, "+FLAGS", "\\Seen")
                    except Exception:
                        pass

            if not new_files:
                if not progress_callback:
                    self.logger.info("[INFO] Không tìm thấy đính kèm mới.")

            if progress_callback:
                progress_callback(total_emails, total_emails, f"Hoàn thành! Tìm thấy {len(new_files)} file mới.")

            if max_uid_seen:
                try:
                    save_last_uid(max_uid_seen)
                except Exception as e:
                    self.logger.warning(f"Could not save last UID: {e}")

            return new_files
