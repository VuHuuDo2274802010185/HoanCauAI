# test_models.py

import os               # thư viện để truy cập biến môi trường
import sys
import types
import importlib
import pytest           # pytest framework để viết và chạy unit tests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))


class DummyGenAI:
    def configure(self, **kw):
        pass

    def list_models(self):
        return []


@pytest.fixture
def model_fetcher_module(mock_requests, monkeypatch):
    sys.modules.setdefault('google', types.SimpleNamespace(generativeai=DummyGenAI()))
    sys.modules.setdefault('google.generativeai', DummyGenAI())

    mf = importlib.import_module('modules.model_fetcher')
    importlib.reload(mf)
    return mf.ModelFetcher

@pytest.fixture
def google_key():
    """
    Fixture trả về GOOGLE_API_KEY từ biến môi trường.
    Nếu không có, các test dựa vào key này sẽ bị skip.
    """
    return os.getenv("GOOGLE_API_KEY")

@pytest.fixture
def openrouter_key():
    """
    Fixture trả về OPENROUTER_API_KEY từ biến môi trường.
    Nếu không có, các test dựa vào key này sẽ bị skip.
    """
    return os.getenv("OPENROUTER_API_KEY")

def test_google_models(model_fetcher_module, google_key):
    """
    Test rằng hàm get_google_models trả về ít nhất một model
    và kiểu trả về là list khi có GOOGLE_API_KEY.
    """
    if not google_key:
        pytest.skip("Bỏ qua test: GOOGLE_API_KEY chưa được thiết lập")
    ModelFetcher = model_fetcher_module
    models = ModelFetcher.get_google_models(google_key)  # gọi API hoặc cache để lấy list model
    # Kiểm tra kiểu dữ liệu trả về
    assert isinstance(models, list), "Kết quả phải là list"
    # Kiểm tra có ít nhất một model trong list
    assert models, "Mong đợi ít nhất một Google model"

def test_openrouter_models(model_fetcher_module, openrouter_key):
    """
    Test rằng hàm get_openrouter_models trả về danh sách dict
    mỗi dict phải có khóa 'id' khi có OPENROUTER_API_KEY.
    """
    if not openrouter_key:
        pytest.skip("Bỏ qua test: OPENROUTER_API_KEY chưa được thiết lập")
    ModelFetcher = model_fetcher_module
    models = ModelFetcher.get_openrouter_models(openrouter_key)  # gọi API hoặc cache để lấy list model dict
    # Kiểm tra kiểu dữ liệu trả về
    assert isinstance(models, list), "Kết quả phải là list"
    # Kiểm tra mỗi phần tử phải chứa khóa 'id'
    assert all(isinstance(m, dict) and 'id' in m for m in models), "Mỗi model phải là dict có khóa 'id'"
