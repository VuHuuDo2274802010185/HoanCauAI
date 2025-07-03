"""Store and load the last processed email UID to speed up future fetches."""

from .config import LAST_UID_FILE


def load_last_uid() -> int:
    """Return the last processed UID or 0 if unavailable."""
    try:
        if LAST_UID_FILE.exists():
            content = LAST_UID_FILE.read_text(encoding="utf-8").strip()
            return int(content or 0)
    except Exception:
        return 0
    return 0


def save_last_uid(uid: int) -> None:
    """Persist the given UID."""
    try:
        LAST_UID_FILE.write_text(str(uid), encoding="utf-8")
    except Exception:
        pass
