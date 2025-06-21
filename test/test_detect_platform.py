import pathlib
import requests
import logging
from typing import Optional

import pytest

# Utility to load detect_platform function from source with correct line numbers
APP_PATH = pathlib.Path('main_engine/app.py')
LINES = APP_PATH.read_text().splitlines()
SNIPPET = "\n".join(LINES[232-1:272])
OFFSET_CODE = "\n" * (232 - 1) + SNIPPET

NAMESPACE = {
    'requests': requests,
    'logger': logging.getLogger("test"),
    'handle_error': lambda f: f,
    'Optional': Optional,
}
exec(OFFSET_CODE, NAMESPACE)

# Expose the loaded function
_detect_platform = NAMESPACE['detect_platform']


@pytest.mark.parametrize(
    "key,expected",
    [
        ("sk-or-123", "openrouter"),
        ("AIzaFakeKey", "google"),
        ("vs-abcdef", "vectorshift"),
    ],
)
def test_pattern_detection(key, expected):
    assert _detect_platform(key) == expected


def test_api_detection(monkeypatch):
    class Resp:
        def __init__(self, code):
            self.status_code = code

    def fake_get(url, headers=None, timeout=5):
        if "openrouter.ai" in url:
            return Resp(200)
        return Resp(404)

    monkeypatch.setattr(requests, "get", fake_get)
    assert _detect_platform("somekey") == "openrouter"


def test_detection_failure(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "get", fake_get)
    assert _detect_platform("unknown") is None
