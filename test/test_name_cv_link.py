import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

import modules.qa_chatbot as qc


def test_name_cv_link(tmp_path, monkeypatch):
    class DummyClient:
        def __init__(self, *a, **k):
            pass
        def generate_content(self, msgs):
            return "Alice là ứng viên tiềm năng."
    monkeypatch.setattr(qc, 'DynamicLLMClient', DummyClient)
    monkeypatch.setattr(qc, 'ATTACHMENT_DIR', tmp_path)
    (tmp_path / 'alice.pdf').write_text('data')
    df = pd.DataFrame([{'Họ tên': 'Alice', 'Nguồn': 'alice.pdf'}])
    ans = qc.answer_question('Alice?', df, provider='p', model='m', api_key='key')
    assert 'download="alice.pdf"' in ans
