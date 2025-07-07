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


def _validate_config():
    """Validate email configuration before use"""
    from .config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS
    
    missing = []
    if not EMAIL_HOST:
        missing.append("EMAIL_HOST")
    if not EMAIL_USER:
        missing.append("EMAIL_USER")
    if not EMAIL_PASS:
        missing.append("EMAIL_PASS")
    if not EMAIL_PORT:
        missing.append("EMAIL_PORT")
    
    if missing:
        raise ValueError(f"Missing email configuration: {', '.join(missing)}")

class EmailFetcher:
    """
    Lớp để kết nối IMAP, tìm email chứa CV/Resume và tải file đính kèm về máy.
    Sau mỗi lần gọi ``fetch_cv_attachments()``, thông tin (path, thời gian gửi)
    của các file mới sẽ được lưu trong ``last_fetch_info``.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                 user: Optional[str] = None, password: Optional[str] = None):
        """
        Khởi tạo EmailFetcher với thông tin kết nối:
        - host, port, user, password: nếu không truyền, dùng biến từ config
        """
        # Validate config first
        _validate_config()
        
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

    def reset_uid_store(self) -> None:
        """
        Reset the UID store to reprocess all emails from the beginning.
        This will cause the next fetch to process all emails, not just new ones.
        """
        try:
            from .config import LAST_UID_FILE
            if LAST_UID_FILE.exists():
                LAST_UID_FILE.unlink()  # Delete the file
            self.logger.info("[INFO] UID store has been reset. Next fetch will process all emails.")
        except Exception as e:
            self.logger.error(f"[ERR] Failed to reset UID store: {e}")

    def get_last_processed_uid(self) -> Optional[int]:
        """
        Get the UID of the last processed email.
        Returns None if no emails have been processed yet.
        """
        return load_last_uid()

    def fetch_cv_attachments(
        self,
        keywords: Optional[List[str]] = None,
        since: Optional[date] = None,
        before: Optional[date] = None,
        batch_size: int = 100,
        unseen_only: bool = EMAIL_UNSEEN_ONLY,
        ignore_last_uid: bool = False,
    ) -> List[str]:
        """
        Tìm và tải xuống file đính kèm PDF/DOCX từ các email thoả mãn:
        - Tiêu đề hoặc nội dung chứa bất kỳ từ khoá nào trong ``keywords``.
        - Ngày gửi >= ``since`` và < ``before`` nếu được cung cấp
          (``before`` được hiểu là mốc kết thúc, không bao gồm ngày này).
        Quét theo từng đợt ``batch_size`` email mới nhất.
        Nếu ``unseen_only`` được bật (mặc định), chỉ tìm trong các email chưa đọc
        để tránh quét lại những thư đã xử lý.
        Nếu ``ignore_last_uid`` được bật, bỏ qua UID đã lưu và xử lý tất cả email.
        Thông tin path và thời gian gửi của mỗi file tải được
        sẽ lưu trong ``last_fetch_info``.
        """
        if self.mail is None:
            raise RuntimeError("Chưa kết nối IMAP. Gọi connect() trước.")

        if keywords is None:
            keywords = ["CV", "Resume", "Curriculum Vitae"]

        new_files: List[str] = []
        self.last_fetch_info = []
        processed_emails = 0
        emails_with_attachments = 0
        total_attachments_found = 0

        self.logger.info(f"[DEBUG] Fetching CVs with keywords: {keywords}")
        
        # --- Tìm email với optional SINCE và UID range ---
        criteria = ['UNSEEN'] if unseen_only else ['ALL']
        if since:
            criteria += ['SINCE', since.strftime('%d-%b-%Y')]
        if before:
            # "BEFORE" của IMAP là mốc không bao gồm ngày chỉ định,
            # nên cần cộng thêm 1 ngày để bao gồm toàn bộ ``before``
            next_day = before + timedelta(days=1)
            criteria += ['BEFORE', next_day.strftime('%d-%b-%Y')]

        # Debug: Log the search criteria being used
        self.logger.info(f"[DEBUG] Search criteria: {criteria}, unseen_only: {unseen_only}")
        
        last_uid = load_last_uid()
        if last_uid and not ignore_last_uid:
            self.logger.info(f"[DEBUG] Last UID from previous fetch: {last_uid}")
        elif ignore_last_uid:
            self.logger.info(f"[DEBUG] Ignoring last UID ({last_uid}), processing all emails")
            last_uid = None
        else:
            self.logger.info(f"[DEBUG] No previous UID found, searching all emails")
        
        # Initialize variables
        typ = 'NO'
        data = [b'']
        
        # Build search criteria with more conservative approach
        try:
            if hasattr(self.mail, 'uid'):
                # Try different search approaches in order of preference
                search_successful = False
                
                # Approach 1: Try with criteria if they exist
                if criteria and criteria != ['ALL']:
                    try:
                        search_criteria = ' '.join(criteria)
                        self.logger.info(f"[DEBUG] Attempting UID search with criteria: {search_criteria}")
                        typ, data = self.mail.uid('search', 'UTF-8', search_criteria)
                        if typ == 'OK':
                            search_successful = True
                            self.logger.info(f"[DEBUG] UID search successful, found {len(data[0].split()) if data and data[0] else 0} emails")
                    except Exception as e:
                        self.logger.debug(f"UID search with criteria failed: {e}")
                
                # Approach 2: Try simple ALL search if criteria search failed
                if not search_successful:
                    try:
                        self.logger.info("[DEBUG] Attempting simple UID search with ALL")
                        typ, data = self.mail.uid('search', 'UTF-8', 'ALL')
                        if typ == 'OK':
                            search_successful = True
                            self.logger.info(f"[DEBUG] UID ALL search successful, found {len(data[0].split()) if data and data[0] else 0} emails")
                    except Exception as e:
                        self.logger.debug(f"UID search with ALL failed: {e}")
                
                # Approach 3: Try without UTF-8 charset
                if not search_successful:
                    try:
                        search_criteria = 'ALL' if not criteria or criteria == ['ALL'] else ' '.join(criteria)
                        self.logger.debug(f"Attempting UID search without charset: {search_criteria}")
                        typ, data = self.mail.uid('search', search_criteria)
                        if typ == 'OK':
                            search_successful = True
                    except Exception as e:
                        self.logger.debug(f"UID search without charset failed: {e}")
                
                if not search_successful:
                    raise Exception("All UID search methods failed")
                    
                # Filter by UID range if we have a last_uid and search was successful
                if typ == 'OK' and data and data[0]:
                    all_uids = data[0].split()
                    self.logger.info(f"[DEBUG] Before UID filtering: {len(all_uids)} emails")
                    if last_uid:
                        # Filter UIDs to only include those greater than last_uid
                        filtered_uids = [uid for uid in all_uids if int(uid) > last_uid]
                        self.logger.info(f"[DEBUG] After UID filtering (> {last_uid}): {len(filtered_uids)} emails")
                        # Reconstruct data format
                        data = [b' '.join(filtered_uids)] if filtered_uids else [b'']
                    else:
                        self.logger.info(f"[DEBUG] No UID filtering applied, using all {len(all_uids)} emails")
            else:
                # Regular search without UID support - try different approaches
                search_successful = False
                
                if criteria and criteria != ['ALL']:
                    try:
                        search_criteria = ' '.join(criteria)
                        typ, data = self.mail.search('UTF-8', search_criteria)
                        if typ == 'OK':
                            search_successful = True
                    except Exception:
                        pass
                
                if not search_successful:
                    typ, data = self.mail.search('UTF-8', 'ALL')
                
        except Exception as e:
            self.logger.error(f"[ERR] All IMAP search methods failed: {e}")
            self.logger.info("[INFO] Attempting basic message enumeration...")
            
            # Final fallback: try to get recent messages directly
            try:
                # Get total message count
                status, messages = self.mail.select("INBOX")
                if status == 'OK' and messages and messages[0]:
                    total_msgs = int(messages[0])
                    # Get last 100 messages (or all if less than 100)
                    start_msg = max(1, total_msgs - 99)
                    msg_range = f"{start_msg}:{total_msgs}"
                    
                    if hasattr(self.mail, 'uid'):
                        # Convert message numbers to UIDs
                        typ, uid_data = self.mail.uid('search', 'UTF-8', f'{start_msg}:*')
                        if typ == 'OK':
                            data = uid_data
                        else:
                            # Fallback to message numbers
                            data = [' '.join(str(i) for i in range(start_msg, total_msgs + 1)).encode()]
                    else:
                        data = [' '.join(str(i) for i in range(start_msg, total_msgs + 1)).encode()]
                    typ = 'OK'
                else:
                    self.logger.error("[ERR] Could not determine message count")
                    return []
            except Exception as final_e:
                self.logger.error(f"[ERR] Final fallback also failed: {final_e}")
                return []
            
        if typ != 'OK':
            self.logger.error(f"[ERR] Lỗi tìm email: {typ}")
            return []

        email_ids = data[0].split() if data and data[0] else []
        # Sắp xếp ID giảm dần để lấy email mới trước
        email_ids.sort(key=lambda x: int(x), reverse=True)
        self.logger.info(f"[INFO] Đã tìm thấy {len(email_ids)} email trong hộp thư.")
        
        # If no emails found with current criteria, suggest alternatives
        if len(email_ids) == 0:
            if unseen_only:
                self.logger.info("[INFO] Không tìm thấy email UNSEEN. Thử tắt 'unseen_only' để tìm tất cả email.")
            if last_uid:
                self.logger.info(f"[INFO] Có thể tất cả email đều có UID <= {last_uid}. Thử xóa UID store để reset.")
            return []

        max_uid_seen = 0
        
        for start in range(0, len(email_ids), batch_size):
            batch = email_ids[start:start + batch_size]
            for num in batch:
                processed_emails += 1
                # Convert bytes to string for IMAP commands
                num_str = num.decode() if isinstance(num, bytes) else str(num)
                
                # Log progress every 10 emails
                if processed_emails % 10 == 0:
                    self.logger.info(f"[PROGRESS] Processed {processed_emails}/{len(email_ids)} emails, found {len(new_files)} CV files so far")

                # Fetch full email with attachments info first
                if hasattr(self.mail, 'uid'):
                    typ, msg_data = self.mail.uid('fetch', num_str, '(RFC822 INTERNALDATE)')
                    uid_int = int(num_str)
                else:
                    typ, msg_data = self.mail.fetch(num_str, '(RFC822 INTERNALDATE)')
                    uid_int = int(num_str)
                    
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

                # Check for PDF/DOCX attachments FIRST - always fetch PDF/DOCX files
                has_cv_attachment = False
                cv_attachments = []
                
                for part in msg.walk():
                    raw_name = part.get_filename()
                    if not raw_name:
                        continue

                    # Decode file name
                    try:
                        decoded_parts = decode_header(raw_name)
                        filename = ''.join(
                            (p.decode(enc or 'utf-8') if isinstance(p, bytes) else p)
                            for p, enc in decoded_parts
                        )
                    except Exception:
                        filename = raw_name

                    # Check if it's a PDF/DOCX file - treat all as potential CVs
                    name, ext = os.path.splitext(filename)
                    if ext.lower() in ['.pdf', '.docx']:
                        # Prioritize files that clearly look like CVs
                        is_obvious_cv = re.search(r"(cv|resume|curriculum|vitae)", name, re.IGNORECASE)
                        has_cv_attachment = True
                        cv_attachments.append((part, filename, is_obvious_cv))
                        self.logger.debug(f"[ATTACHMENT] Found {ext.upper()}: {filename} {'(obvious CV)' if is_obvious_cv else '(potential CV)'}")
                
                if has_cv_attachment:
                    self.logger.info(f"[EMAIL {num_str}] Found {len(cv_attachments)} PDF/DOCX attachment(s)")

                # If no PDF/DOCX attachments, check keywords in subject/body before skipping
                skip_email = False
                if not has_cv_attachment:
                    # Get subject and body for keyword filtering
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
                                payload = part.get_payload(decode=False)
                                
                                if isinstance(payload, str):
                                    if part.get('Content-Transfer-Encoding') == 'base64':
                                        import base64
                                        decoded_bytes = base64.b64decode(payload)
                                        body_text += decoded_bytes.decode(charset, errors='ignore')
                                    else:
                                        body_text += payload
                                elif isinstance(payload, bytes):
                                    body_text += payload.decode(charset, errors='ignore')
                            except Exception as e:
                                self.logger.debug(f"Failed to extract text from part: {e}")
                                pass

                    all_text = f"{subj}\n{body_text}".lower()
                    # Skip if no keywords found and no PDF/DOCX attachments
                    if not any(kw.lower() in all_text for kw in keywords):
                        self.logger.debug(f"[SKIP] Email {num_str}: No PDF/DOCX attachments and no keywords in subject/body")
                        skip_email = True
                
                if skip_email:
                    continue

                # Log email being processed with more details
                try:
                    subj_hdr = msg.get('Subject', '')
                    subj = ''.join(
                        p.decode(enc or 'utf-8', errors='ignore') if isinstance(p, bytes) else p
                        for p, enc in decode_header(subj_hdr)
                    )
                except Exception:
                    subj = ''
                
                attachment_info = ""
                if has_cv_attachment:
                    attachment_info = f"({len(cv_attachments)} PDF/DOCX files)"
                else:
                    attachment_info = "(keyword match only)"
                    
                self.logger.info(f"[PROCESSING] Email {num_str}: {subj[:50]}... {attachment_info}")

                # Process PDF/DOCX attachments if found
                if has_cv_attachment:
                    emails_with_attachments += 1
                    total_attachments_found += len(cv_attachments)
                    
                    # Sort to prioritize obvious CV files first
                    cv_attachments.sort(key=lambda x: x[2], reverse=True)  # is_obvious_cv first
                    
                    for part, filename, is_obvious_cv in cv_attachments:
                        # Sanitize filename
                        name, ext = os.path.splitext(filename)
                        safe_name = re.sub(r'[^\w\-\_ ]', '_', name)
                        safe = safe_name + ext
                        path = os.path.join(ATTACHMENT_DIR, safe)

                        # Skip if file already exists
                        if os.path.exists(path):
                            self.logger.info(f"[INFO] Đã tồn tại: {path}")
                            continue

                        # Save attachment
                        payload = part.get_payload(decode=True)
                        if payload is None:
                            self.logger.warning(f"[SKIP] Failed to decode attachment: {safe}")
                            continue

                        # Convert to bytes
                        if isinstance(payload, str):
                            content_bytes = payload.encode('utf-8')
                        elif isinstance(payload, bytes):
                            content_bytes = payload
                        else:
                            self.logger.warning(f"[SKIP] Unsupported payload type for {safe}: {type(payload)}")
                            continue

                        try:
                            with open(path, "wb") as f:
                                f.write(content_bytes)
                            new_files.append(path)
                            self.last_fetch_info.append((path, sent_time))
                            try:
                                record_sent_time(path, sent_time)
                            except Exception as e:
                                self.logger.warning(f"Could not record sent time for {path}: {e}")
                            priority_msg = " (priority CV)" if is_obvious_cv else " (PDF/DOCX)"
                            self.logger.info(f"[OK] Lưu đính kèm mới: {path}{priority_msg}")
                        except Exception as e:
                            self.logger.error(f"[ERROR] Failed to save {safe}: {e}")
                            continue
                else:
                    # Even in aggressive mode, check for any PDF/DOCX attachments in emails without obvious CVs
                    # This catches cases where files might not be detected in the first pass
                    emails_with_attachments += 1 if has_cv_attachment else 0
                    
                    for part in msg.walk():
                        raw_name = part.get_filename()
                        if not raw_name:
                            continue

                        try:
                            decoded_parts = decode_header(raw_name)
                            filename = ''.join(
                                (p.decode(enc or 'utf-8') if isinstance(p, bytes) else p)
                                for p, enc in decoded_parts
                            )
                        except Exception:
                            filename = raw_name

                        name, ext = os.path.splitext(filename)
                        if ext.lower() not in ['.pdf', '.docx']:
                            continue
                            
                        # In aggressive mode or keyword-matched emails, save all PDF/DOCX files
                        safe_name = re.sub(r'[^\w\-\_ ]', '_', name)
                        safe = safe_name + ext
                        path = os.path.join(ATTACHMENT_DIR, safe)

                        if os.path.exists(path):
                            self.logger.info(f"[INFO] Đã tồn tại: {path}")
                            continue

                        payload = part.get_payload(decode=True)
                        if payload is None:
                            self.logger.warning(f"[SKIP] Failed to decode attachment: {safe}")
                            continue

                        if isinstance(payload, str):
                            content_bytes = payload.encode('utf-8')
                        elif isinstance(payload, bytes):
                            content_bytes = payload
                        else:
                            self.logger.warning(f"[SKIP] Unsupported payload type for {safe}: {type(payload)}")
                            continue

                        try:
                            with open(path, "wb") as f:
                                f.write(content_bytes)
                            new_files.append(path)
                            self.last_fetch_info.append((path, sent_time))
                            try:
                                record_sent_time(path, sent_time)
                            except Exception as e:
                                self.logger.warning(f"Could not record sent time for {path}: {e}")
                            self.logger.info(f"[OK] Lưu đính kèm mới: {path} (keyword match)")
                        except Exception as e:
                            self.logger.error(f"[ERROR] Failed to save {safe}: {e}")
                            continue

                # Đánh dấu email đã đọc để tránh xử lý lại lần sau
                try:
                    self.mail.store(num_str, "+FLAGS", "\\Seen")
                except Exception:
                    pass

        # Log summary statistics
        self.logger.info(f"[SUMMARY] Processed {processed_emails} emails, found {emails_with_attachments} emails with PDF/DOCX attachments")
        self.logger.info(f"[SUMMARY] Total attachments found: {total_attachments_found}, downloaded: {len(new_files)}")
        
        if not new_files:
            self.logger.info("[INFO] Không tìm thấy đính kèm mới.")

        if max_uid_seen:
            try:
                save_last_uid(max_uid_seen)
            except Exception as e:
                self.logger.warning(f"Could not save last UID: {e}")

        return new_files
