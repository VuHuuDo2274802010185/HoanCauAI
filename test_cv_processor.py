import sys
import types
import pytest

# Stub external dependencies before importing cv_processor
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

sys.modules.setdefault('streamlit', DummyStreamlit())
sys.modules.setdefault('google', types.SimpleNamespace(generativeai=DummyGenAI()))
sys.modules.setdefault('google.generativeai', DummyGenAI())

import modules.cv_processor as cvp

# Replace DynamicLLMClient with dummy to avoid API requirements
class DummyLLMClient:
    def generate_content(self, messages):
        return ''

cvp.DynamicLLMClient = DummyLLMClient
CVProcessor = cvp.CVProcessor


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
def test_fallback_regex(text, expected):
    info = CVProcessor()._fallback_regex(text)
    assert info == expected
