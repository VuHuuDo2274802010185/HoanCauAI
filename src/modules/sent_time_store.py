"""Lưu thời gian gửi email ứng với mỗi file đính kèm."""

import json  # xử lý file JSON
import os  # thao tác đường dẫn
from typing import Dict
from .config import SENT_TIME_FILE  # đường dẫn file lưu thông tin thời gian

def load_sent_times() -> Dict[str, str]:
    """Load mapping of attachment filename to sent time."""
    if SENT_TIME_FILE.exists():
        try:
            # Đọc file JSON
            with open(SENT_TIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Chuyển đổi key/value về str
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            # Nếu lỗi, trả về dict rỗng
            return {}
    return {}

def record_sent_time(path: str, sent_time: str | None) -> None:
    """Update mapping with sent time for the given attachment path."""
    fname = os.path.basename(path)  # chỉ lấy tên file
    data = load_sent_times()  # đọc dữ liệu hiện có
    data[fname] = sent_time or ""  # cập nhật thời gian gửi
    with open(SENT_TIME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_sent_times_bulk(mapping: Dict[str, str | None]) -> None:
    """Ghi nhiều bản ghi thời gian gửi cùng lúc."""
    if not mapping:
        return
    data = load_sent_times()
    for path, ts in mapping.items():
        fname = os.path.basename(path)
        data[fname] = ts or ""
    with open(SENT_TIME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
