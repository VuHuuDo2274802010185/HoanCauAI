# modules/auto_fetcher.py
"""Chạy EmailFetcher liên tục với khoảng nghỉ tuỳ chọn."""

import time
import logging
import argparse
import imaplib

from .email_fetcher import EmailFetcher


def watch_loop(interval: int) -> None:
    """Kết nối IMAP và gọi fetch_cv_attachments() liên tục."""
    fetcher = EmailFetcher()
    fetcher.connect()
    logging.info(f"Bắt đầu auto fetch, interval={interval}s")

    try:
        while True:
            try:
                fetcher.fetch_cv_attachments()
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
    args = parser.parse_args()
    watch_loop(args.interval)


if __name__ == "__main__":
    main()
