import sys
import os
import types
import pytest

# Ensure repo root and src in path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

# Provide dummy streamlit before importing the module
sys.modules['streamlit'] = types.SimpleNamespace(session_state={})

import modules.dynamic_llm_client as dlc


class DummyResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}
    def json(self):
        return self._data


def test_provider_selection_param(monkeypatch):
    monkeypatch.setattr(dlc.requests, "get", lambda *a, **k: DummyResp())
    client = dlc.DynamicLLMClient(provider="openrouter", model="m1", api_key="sk-or-key")
    assert client.provider == "openrouter"
    assert client.model == "m1"
    assert client.api_key == "sk-or-key"
    assert client.client is None


def test_provider_selection_session(monkeypatch):
    dlc.st.session_state.clear()
    dlc.st.session_state.update({
        "selected_provider": "openrouter",
        "selected_model": "m2",
        "openrouter_api_key": "sk-or-session"
    })
    monkeypatch.setattr(dlc, "_streamlit_ctx_exists", lambda: True)
    monkeypatch.setattr(dlc.requests, "get", lambda *a, **k: DummyResp())
    client = dlc.DynamicLLMClient()
    assert client.provider == "openrouter"
    assert client.model == "m2"
    assert client.api_key == "sk-or-session"


def test_invalid_provider(monkeypatch):
    with pytest.raises(ValueError):
        dlc.DynamicLLMClient(provider="bad", api_key="dummy")


def test_openrouter_unauthorized(monkeypatch):
    monkeypatch.setattr(dlc.requests, "get", lambda *a, **k: DummyResp())
    def fake_post(*a, **k):
        return DummyResp(status_code=401, data={"detail": "unauthorized"})
    monkeypatch.setattr(dlc.requests, "post", fake_post)
    client = dlc.DynamicLLMClient(provider="openrouter", api_key="sk-or-key")
    with pytest.raises(ValueError):
        client.generate_content(["hi"])


def test_openrouter_missing_key(monkeypatch):
    monkeypatch.setattr(dlc.requests, "get", lambda *a, **k: DummyResp())
    with pytest.raises(ValueError):
        dlc.DynamicLLMClient(provider="openrouter", api_key="")

