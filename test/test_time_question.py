import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

import modules.qa_chatbot as qc


def test_time_question(monkeypatch):
    # Fail if LLM client is created
    class FailClient:
        def __init__(self, *a, **k):
            raise AssertionError('LLM should not be called')
    monkeypatch.setattr(qc, 'DynamicLLMClient', FailClient)
    df = pd.DataFrame([{'a':1}])
    ans = qc.answer_question('Bây giờ là mấy giờ?', df, provider='p', model='m', api_key='key')
    assert 'Bây giờ là' in ans
