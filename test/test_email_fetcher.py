import sys
import os
import types
from email.message import EmailMessage
from pathlib import Path

import importlib
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class DummyGenAI:
    def configure(self, **kwargs):
        pass

    def list_models(self):
        return []


@pytest.fixture
def email_fetcher_module(monkeypatch, tmp_path):
    fake = DummyGenAI()
    sys.modules['google'] = types.SimpleNamespace(generativeai=fake)
    sys.modules['google.generativeai'] = fake
    import modules.email_fetcher as email_fetcher
    importlib.reload(email_fetcher)
    monkeypatch.setattr(email_fetcher, 'ATTACHMENT_DIR', tmp_path)
    return email_fetcher


def test_fetch_cv_attachments(email_fetcher_module, tmp_path):
    email_fetcher = email_fetcher_module
    EmailFetcher = email_fetcher.EmailFetcher

    msg = EmailMessage()
    msg['Subject'] = 'CV Nguyen'
    msg.set_content('body')
    msg.add_attachment(b'data', maintype='application', subtype='pdf', filename='cv.pdf')
    raw = msg.as_bytes()

    class FakeIMAP:
        def search(self, charset, *criteria):
            return 'OK', [b'1']

        def fetch(self, num, query):
            return 'OK', [(None, raw)]

        def store(self, *args, **kwargs):
            pass

    fetcher = EmailFetcher()
    fetcher.mail = FakeIMAP()
    files = fetcher.fetch_cv_attachments()
    expected = tmp_path / 'cv.pdf'
    assert files == [str(expected)]
    assert expected.exists()


def test_ignore_non_cv_files(email_fetcher_module, tmp_path):
    email_fetcher = email_fetcher_module
    EmailFetcher = email_fetcher.EmailFetcher

    msg = EmailMessage()
    msg['Subject'] = 'CV Nguyen'
    msg.set_content('body')
    msg.add_attachment(b'data', maintype='application', subtype='pdf', filename='invoice.pdf')
    raw = msg.as_bytes()

    class FakeIMAP:
        def search(self, charset, *criteria):
            return 'OK', [b'1']

        def fetch(self, num, query):
            return 'OK', [(None, raw)]

        def store(self, *args, **kwargs):
            pass

    fetcher = EmailFetcher()
    fetcher.mail = FakeIMAP()
    files = fetcher.fetch_cv_attachments()
    assert files == []
