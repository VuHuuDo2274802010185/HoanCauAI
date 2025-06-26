import sys
from pathlib import Path
import json
import modules.qa_chatbot as qc


def test_log_chat_corrupted(tmp_path):
    log_file = tmp_path / "chat_log.json"
    log_file.write_text("corrupted")
    qc._log_chat("Q", "A", log_file)
    data = json.loads(log_file.read_text())
    assert data[-1]["question"] == "Q"


def test_get_chat_statistics_corrupted(tmp_path):
    log_file = tmp_path / "chat_log.json"
    log_file.write_text("corrupted")
    stats = qc.get_chat_statistics(log_file)
    assert stats["total_chats"] == 0
