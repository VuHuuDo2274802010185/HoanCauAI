import json
import os
from typing import Dict
from .config import SENT_TIME_FILE

def load_sent_times() -> Dict[str, str]:
    """Load mapping of attachment filename to sent time."""
    if SENT_TIME_FILE.exists():
        try:
            with open(SENT_TIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            return {}
    return {}

def record_sent_time(path: str, sent_time: str | None) -> None:
    """Update mapping with sent time for the given attachment path."""
    fname = os.path.basename(path)
    data = load_sent_times()
    data[fname] = sent_time or ""
    with open(SENT_TIME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
