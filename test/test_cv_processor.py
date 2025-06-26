import sys
import os
import types
import importlib
import pytest


class DummyStreamlit:
    session_state = {}


class DummyGenAI:
    def configure(self, **kw):
        pass

    class GenerativeModel:
        def __init__(self, model):
            self.model = model

        def generate_content(self, prompt):
            return types.SimpleNamespace(text="")

    def list_models(self):
        return []


@pytest.fixture
def cv_processor_class(mock_pandas, mock_requests, monkeypatch):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, "src"))
    sys.modules.setdefault("streamlit", DummyStreamlit())
    sys.modules.setdefault("google", types.SimpleNamespace(generativeai=DummyGenAI()))
    sys.modules.setdefault("google.generativeai", DummyGenAI())

    cvp = importlib.import_module("modules.cv_processor")

    class DummyLLMClient:
        def generate_content(self, messages):
            return ""

    if hasattr(cvp, "DynamicLLMClient"):
        monkeypatch.setattr(cvp, "DynamicLLMClient", DummyLLMClient)
    return cvp.CVProcessor


@pytest.mark.parametrize('text,expected', [
    (
        """Họ tên: Nguyen Van A\nTuổi: 30\nEmail: a@test.com\nĐiện thoại: +84987654321\nĐịa chỉ: 123 Street\nHọc vấn: University ABC\nKinh nghiệm: 5 năm\nKỹ năng: Python""",
        {
            'ten': 'Nguyen Van A',
            'tuoi': '30',
            'email': 'a@test.com',
            'dien_thoai': '+84987654321',
            'hoc_van': 'University ABC',
            'kinh_nghiem': '5 năm',
            'dia_chi': '123 Street',
            'ky_nang': 'Python',
        }
    ),
    (

        """Họ tên: John Smith\nAge: 35\nEmail: john@example.com\nĐiện thoại: 555-123-4567\nAddress: 1 Main St\nEducation: BSc\nExperience: 3 years\nSkills: Java""",
        {
            'ten': 'John Smith',
            'tuoi': '35',
            'email': 'john@example.com',
            'dien_thoai': '555-123-4567',
            'hoc_van': 'BSc',
            'kinh_nghiem': '3 years',
            'dia_chi': '1 Main St',
            'ky_nang': 'Java',
        }
    )
])
def test_fallback_regex(cv_processor_class, text, expected):
    info = cv_processor_class()._fallback_regex(text)
    assert info == expected


def test_process_includes_sent_time(cv_processor_class, tmp_path, monkeypatch):
    cp_module = importlib.import_module(cv_processor_class.__module__)
    monkeypatch.setattr(cp_module, 'ATTACHMENT_DIR', tmp_path)

    class DummyFetcher:
        def fetch_cv_attachments(self, unseen_only=True):
            p = tmp_path / 'cv.pdf'
            p.write_text('data')
            self.last_fetch_info = [(str(p), '2023-09-20T10:15:00Z')]
            return [str(p)]

    fetcher = DummyFetcher()
    processor = cp_module.CVProcessor(fetcher)
    monkeypatch.setattr(processor, 'extract_text', lambda p: '')
    monkeypatch.setattr(processor, 'extract_info_with_llm', lambda t: {})
    df = processor.process()
    if hasattr(df, 'iloc'):
        value = df['Thời gian nhận'].iloc[0]
    else:
        value = df[0]['Thời gian nhận']
    expected = cp_module.format_sent_time_display('2023-09-20T10:15:00Z')
    assert value == expected


def test_process_uses_saved_sent_time(cv_processor_class, tmp_path, monkeypatch):
    cp_module = importlib.import_module(cv_processor_class.__module__)

    monkeypatch.setattr(cp_module, 'ATTACHMENT_DIR', tmp_path)
    metadata = tmp_path / 'sent_times.json'
    monkeypatch.setattr(cp_module, 'SENT_TIME_FILE', metadata, raising=False)

    import modules.sent_time_store as sts
    monkeypatch.setattr(sts, 'SENT_TIME_FILE', metadata, raising=False)

    p = tmp_path / 'cv.pdf'
    p.write_text('data')
    sts.record_sent_time(str(p), '2023-09-20T12:00:00Z')

    processor = cp_module.CVProcessor()
    monkeypatch.setattr(processor, 'extract_text', lambda p: '')
    monkeypatch.setattr(processor, 'extract_info_with_llm', lambda t: {})
    df = processor.process()
    if hasattr(df, 'iloc'):
        value = df['Thời gian nhận'].iloc[0]
    else:
        value = df[0]['Thời gian nhận']
    expected = cp_module.format_sent_time_display('2023-09-20T12:00:00Z')
    assert value == expected
