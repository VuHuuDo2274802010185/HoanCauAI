# modules/auto_fetcher.py
"""Chạy EmailFetcher liên tục với khoảng nghỉ tuỳ chọn."""

import time
import logging
import argparse
import imaplib

from .config import EMAIL_UNSEEN_ONLY, OUTPUT_CSV

from .email_fetcher import EmailFetcher
from .cv_processor import CVProcessor
from .llm_client import LLMClient


def watch_loop(
    interval: int,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    unseen_only: bool = EMAIL_UNSEEN_ONLY,
) -> None:
    """Kết nối IMAP, fetch và xử lý CV liên tục."""
    fetcher = EmailFetcher(host, port, user, password)
    processor = CVProcessor(fetcher, llm_client=LLMClient())
    fetcher.connect()
    logging.info(f"Bắt đầu auto fetch, interval={interval}s")

    try:
        while True:
            try:
                files = fetcher.fetch_cv_attachments(unseen_only=unseen_only)
                for path in files:
                    df = processor.process_file(path)
                    if not df.empty:
                        processor.save_to_csv(df, str(OUTPUT_CSV), append=True)
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
    )


if __name__ == "__main__":
    main()
