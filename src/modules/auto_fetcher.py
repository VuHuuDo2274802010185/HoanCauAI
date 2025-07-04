# modules/auto_fetcher.py
"""Chạy EmailFetcher liên tục với khoảng nghỉ tuỳ chọn."""

import time
import logging
import argparse
import imaplib
from datetime import date, datetime

from .config import EMAIL_UNSEEN_ONLY

from .email_fetcher import EmailFetcher


def watch_loop(
    interval: int,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    unseen_only: bool = EMAIL_UNSEEN_ONLY,
    since: date | None = None,
    before: date | None = None,
) -> None:
    """Kết nối IMAP và gọi fetch_cv_attachments() liên tục."""
    fetcher = EmailFetcher(host, port, user, password)
    fetcher.connect()
    logging.info(f"Bắt đầu auto fetch, interval={interval}s")

    try:
        while True:
            try:
                fetcher.fetch_cv_attachments(
                    since=since,
                    before=before,
                    unseen_only=unseen_only,
                )
            except imaplib.IMAP4.abort:
                logging.warning("Mất kết nối IMAP, thử kết nối lại...")
                try:
                    fetcher.connect()
                except Exception as e:
                    logging.error(f"Không thể kết nối lại: {e}")
            except Exception as e:  # bắt mọi lỗi để không dừng vòng lặp
                logging.error(f"Lỗi fetch: {e}")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Đã dừng auto fetch")
    finally:
        if fetcher.mail:
            try:
                fetcher.mail.logout()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Tự động fetch CV từ email")
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Khoảng thời gian (giây) giữa các lần quét",
    )
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument(
        "--from-date",
        type=lambda s: datetime.strptime(s, "%d/%m/%Y").date(),
        help="Chỉ lấy email từ ngày này (DD/MM/YYYY)",
    )
    parser.add_argument(
        "--to-date",
        type=lambda s: datetime.strptime(s, "%d/%m/%Y").date(),
        help="Chỉ lấy email trước ngày này (DD/MM/YYYY)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Quét tất cả email thay vì chỉ UNSEEN",
    )
    args = parser.parse_args()
    watch_loop(
        args.interval,
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        unseen_only=not args.all,
        since=args.from_date,
        before=args.to_date,
    )


if __name__ == "__main__":
    main()
