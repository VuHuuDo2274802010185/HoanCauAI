import sys
import types
import pytest


def _install_dummy_pandas():
    class DummyDataFrame(list):
        def __init__(self, data=None, columns=None):
            super().__init__(data or [])

        def to_csv(self, *args, **kwargs):
            pass

    dummy_pd = types.SimpleNamespace(
        DataFrame=DummyDataFrame,
        set_option=lambda *a, **k: None,
    )
    sys.modules.setdefault('pandas', dummy_pd)
    return dummy_pd


def _install_dummy_requests():
    class DummyResponse:
        def __init__(self, data=None):
            self._data = data or {}

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    dummy_req = types.SimpleNamespace(
        get=lambda *a, **k: DummyResponse(),
        post=lambda *a, **k: DummyResponse(),
    )
    sys.modules.setdefault('requests', dummy_req)
    return dummy_req


@pytest.fixture
def mock_pandas():
    try:
        import pandas as pd  # noqa: F401
    except Exception:
        pd = _install_dummy_pandas()
    else:
        pd = sys.modules['pandas']
    return pd


@pytest.fixture
def mock_requests():
    try:
        import requests  # noqa: F401
    except Exception:
        req = _install_dummy_requests()
    else:
        req = sys.modules['requests']
    return req
