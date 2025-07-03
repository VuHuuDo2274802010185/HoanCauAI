import sys
import os
import types
from email.message import EmailMessage
from datetime import date

import importlib
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))


class DummyGenAI:
    def configure(self, **kwargs):
        pass

    def list_models(self):
        return []


@pytest.fixture
def email_fetcher_module(mock_requests, monkeypatch, tmp_path):
    fake = DummyGenAI()
    sys.modules['google'] = types.SimpleNamespace(generativeai=fake)
    sys.modules['google.generativeai'] = fake
    import modules.email_fetcher as email_fetcher
    importlib.reload(email_fetcher)
    import modules.uid_store as uid_store
    monkeypatch.setattr(email_fetcher, 'ATTACHMENT_DIR', tmp_path)
    monkeypatch.setattr(uid_store, 'LAST_UID_FILE', tmp_path / 'last_uid.txt')
    return email_fetcher


def test_fetch_cv_attachments(email_fetcher_module, tmp_path):
    email_fetcher = email_fetcher_module
    EmailFetcher = email_fetcher.EmailFetcher

    msg = EmailMessage()
    msg['Subject'] = 'CV Nguyen'
    msg['Date'] = 'Wed, 20 Sep 2023 10:15:00 -0400'
    msg.set_content('body')
    msg.add_attachment(b'data', maintype='application', subtype='pdf', filename='cv.pdf')
    raw = msg.as_bytes()

    class FakeIMAP:
        def __init__(self):
            self.last_criteria = None
            self.fetch_queries = []

        def uid(self, cmd, *args):
            if cmd.lower() == 'search':
                charset = args[0]
                criteria = args[1:]
                self.last_criteria = criteria
                return 'OK', [b'1']
            if cmd.lower() == 'fetch':
                id_set = args[0]
                query = args[1]
                self.fetch_queries.append(query)
                if query == '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])':
                    ids = id_set.split(b',') if isinstance(id_set, bytes) else [id_set]
                    return 'OK', [(b'UID %s' % i, b'Subject: CV Nguyen\r\n') for i in ids]
                return 'OK', [
                    (None, raw),
                    (b'INTERNALDATE', b'"20-Sep-2023 10:20:00 -0400"'),
                ]
            return 'NO', []

        def store(self, *args, **kwargs):
            pass

    fetcher = EmailFetcher()
    imap = FakeIMAP()
    fetcher.mail = imap
    files = fetcher.fetch_cv_attachments(before=date(2023, 9, 21))
    expected = tmp_path / 'cv.pdf'
    assert files == [str(expected)]
    assert expected.exists()
    assert fetcher.last_fetch_info == [(str(expected), '2023-09-20T10:20:00-04:00')]
    assert 'BEFORE' in imap.last_criteria
    assert '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])' in imap.fetch_queries
    assert '(RFC822 INTERNALDATE)' in imap.fetch_queries


def test_profile_file_processed(email_fetcher_module, tmp_path):
    email_fetcher = email_fetcher_module
    EmailFetcher = email_fetcher.EmailFetcher

    msg = EmailMessage()
    msg['Subject'] = 'Profile'
    msg['Date'] = 'Wed, 20 Sep 2023 10:15:00 -0400'
    msg.set_content('body')
    msg.add_attachment(b'data', maintype='application', subtype='pdf', filename='profile.pdf')
    raw = msg.as_bytes()

    class FakeIMAP:
        def __init__(self):
            self.fetch_queries = []

        def uid(self, cmd, *args):
            if cmd.lower() == 'search':
                return 'OK', [b'1']
            if cmd.lower() == 'fetch':
                id_set = args[0]
                query = args[1]
                self.fetch_queries.append(query)
                if query == '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])':
                    ids = id_set.split(b',') if isinstance(id_set, bytes) else [id_set]
                    return 'OK', [(b'UID %s' % i, b'Subject: Profile\r\n') for i in ids]
                return 'OK', [
                    (None, raw),
                    (b'INTERNALDATE', b'"20-Sep-2023 10:20:00 -0400"'),
                ]
            return 'NO', []

        def store(self, *args, **kwargs):
            pass

    fetcher = EmailFetcher()
    imap = FakeIMAP()
    fetcher.mail = imap
    files = fetcher.fetch_cv_attachments()
    expected = tmp_path / 'profile.pdf'
    assert files == [str(expected)]
    assert expected.exists()

