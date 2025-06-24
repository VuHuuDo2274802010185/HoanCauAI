import sys
import os
import types
import importlib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

# minimal env so Settings can initialize
os.environ.setdefault("EMAIL_HOST", "host")
os.environ.setdefault("EMAIL_PORT", "993")
os.environ.setdefault("EMAIL_USER", "user")
os.environ.setdefault("EMAIL_PASS", "pass")
os.environ.setdefault("ATTACHMENT_DIR", "attachments")
os.environ.setdefault("OUTPUT_CSV", "csv/out.csv")
os.environ.setdefault("OUTPUT_EXCEL", "excel/out.xlsx")

import modules.mcp_server as mcp


class DummyFetcher:
    def __init__(self, *a, **k):
        pass
    def connect(self):
        pass

class DummyProcessor:
    def __init__(self, *a, **k):
        pass
    def process(self):
        return pd.DataFrame([{"a": 1}])
    def save_to_csv(self, df, path):
        self.saved = path
    def save_to_excel(self, df, path):
        self.saved_excel = path
    def extract_text(self, path):
        return "text"
    def extract_info_with_llm(self, text):
        return {"ok": True}


def setup_app(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp, "EmailFetcher", DummyFetcher)
    monkeypatch.setattr(mcp, "CVProcessor", DummyProcessor)
    monkeypatch.setattr(mcp, "LLMClient", lambda: None)
    monkeypatch.setattr(mcp.settings, "attachment_dir", tmp_path)
    monkeypatch.setattr(mcp.settings, "output_csv", tmp_path / "out.csv")
    return TestClient(mcp.app)


def test_health_endpoint():
    client = TestClient(mcp.app)
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_run_full_missing_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp.settings, "email_user", "")
    monkeypatch.setattr(mcp.settings, "email_pass", "")
    client = setup_app(monkeypatch, tmp_path)
    res = client.post("/run-full-process")
    assert res.status_code == 400


def test_run_full_success(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp.settings, "email_user", "u")
    monkeypatch.setattr(mcp.settings, "email_pass", "p")
    client = setup_app(monkeypatch, tmp_path)
    res = client.post("/run-full-process")
    assert res.status_code == 200
    assert res.json() == {"processed": 1}


def test_process_single_cv(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp.settings, "email_user", "u")
    monkeypatch.setattr(mcp.settings, "email_pass", "p")
    client = setup_app(monkeypatch, tmp_path)
    file_content = b"data"
    res = client.post("/process-single-cv", files={"file": ("cv.pdf", file_content, "application/pdf")})
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_results_endpoint(monkeypatch, tmp_path):
    client = setup_app(monkeypatch, tmp_path)
    # not exists
    res = client.get("/results")
    assert res.status_code == 404
    # create file then fetch
    out_file = tmp_path / "out.csv"
    out_file.write_text("a,b")
    res = client.get("/results")
    assert res.status_code == 200
    assert res.text == "a,b"

