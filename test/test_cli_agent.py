import os
import sys
import types
import importlib
from click.testing import CliRunner
import pytest

# ensure repo root and src on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

class DummyDF(list):
    def __init__(self, data=None):
        super().__init__(data or [])
    @property
    def empty(self):
        return len(self) == 0
    def to_csv(self, *a, **k):
        pass


@pytest.fixture
def cli_module(monkeypatch, tmp_path):
    calls = {}

    # dummy processor
    class DummyProcessor:
        def __init__(self, *a, **k):
            pass
        def process(self, from_time=None, to_time=None):
            calls['process_range'] = {'from': from_time, 'to': to_time}
            return DummyDF(calls.get('df_rows', []))
        def save_to_csv(self, df, path):
            calls['saved'] = path
        def save_to_excel(self, df, path):
            calls['saved_excel'] = path
        def extract_text(self, f):
            calls['extract_text'] = f
            return 'text'
        def extract_info_with_llm(self, t):
            return {'info': t}
    monkeypatch.setitem(sys.modules, 'modules.cv_processor', types.SimpleNamespace(CVProcessor=DummyProcessor))

    # dummy llm client
    class DummyLLMClient:
        def __init__(self):
            calls['llmclient'] = True
    monkeypatch.setitem(sys.modules, 'modules.llm_client', types.SimpleNamespace(LLMClient=DummyLLMClient))

    # dummy chatbot
    class DummyChatbot:
        def __init__(self, provider=None, model=None, api_key=None):
            pass
        def ask_question(self, question, df):
            calls['chat_question'] = question
            return 'ans'
    monkeypatch.setitem(sys.modules, 'modules.qa_chatbot', types.SimpleNamespace(QAChatbot=DummyChatbot))

    # dummy uvicorn
    def fake_run(app, host=None, port=None, reload=None):
        calls['uvicorn'] = (app, host, port, reload)
    monkeypatch.setitem(sys.modules, 'uvicorn', types.SimpleNamespace(run=fake_run))

    # dummy pandas
    monkeypatch.setitem(sys.modules, 'pandas', types.SimpleNamespace(DataFrame=DummyDF, read_csv=lambda p: DummyDF([{'a':1}])))

    # dummy settings
    settings = types.SimpleNamespace(
        email_host='h',
        email_port=993,
        email_user='u',
        email_pass='pw',
        email_unseen_only=True,
        output_csv=tmp_path / 'out.csv',
        output_excel=tmp_path / 'out.xlsx'
    )
    monkeypatch.setitem(sys.modules, 'modules.mcp_server', types.SimpleNamespace(settings=settings))

    # simple config
    monkeypatch.setitem(sys.modules, 'modules.config', types.SimpleNamespace(LLM_CONFIG={'api_key': ''}))

    cli = importlib.import_module('scripts.cli_agent')
    importlib.reload(cli)
    return cli.cli, calls, settings


def test_full_process_empty(cli_module):
    cli, calls, _ = cli_module
    runner = CliRunner()
    res = runner.invoke(cli, ['full-process'])
    assert res.exit_code == 0
    assert "Bắt đầu full process" in res.output
    assert "Không có CV mới" in res.output
    assert 'saved' not in calls
    assert calls['process_range']['from'] is None
    assert calls['process_range']['to'] is None


def test_full_process_with_data(cli_module):
    cli, calls, settings = cli_module
    calls['df_rows'] = [1, 2]
    runner = CliRunner()
    res = runner.invoke(cli, ['full-process'])
    assert res.exit_code == 0
    assert f"Đã xử lý 2 CV" in res.output
    assert calls['saved'] == str(settings.output_csv)
    assert calls['process_range']['from'] is None
    assert calls['process_range']['to'] is None


def test_single_missing_argument(cli_module):
    cli, calls, _ = cli_module
    runner = CliRunner()
    res = runner.invoke(cli, ['single'])
    assert res.exit_code != 0
    assert "Missing argument 'FILE'" in res.output


def test_single_success(cli_module, tmp_path):
    cli, calls, _ = cli_module
    file = tmp_path / 'cv.pdf'
    file.write_text('data')
    runner = CliRunner()
    res = runner.invoke(cli, ['single', str(file)])
    assert res.exit_code == 0
    assert f"Xử lý file: {file}" in res.output
    assert "{'info': 'text'}" in res.output
    assert calls['extract_text'] == str(file)


def test_serve_runs_uvicorn(cli_module):
    cli, calls, _ = cli_module
    runner = CliRunner()
    res = runner.invoke(cli, ['serve', '--host', '1.2.3.4', '--port', '1234'])
    assert res.exit_code == 0
    assert "Chạy MCP server tại http://1.2.3.4:1234" in res.output
    assert calls['uvicorn'] == ('modules.mcp_server:app', '1.2.3.4', 1234, True)


def test_chat_missing_csv(cli_module):
    cli, calls, _ = cli_module
    runner = CliRunner()
    res = runner.invoke(cli, ['chat', 'hi'])
    assert res.exit_code == 0
    assert "File kết quả không tồn tại" in res.output


def test_chat_success(cli_module):
    cli, calls, settings = cli_module
    settings.output_csv.write_text('a,b')
    runner = CliRunner()
    res = runner.invoke(cli, ['chat', 'hello'])
    assert res.exit_code == 0
    assert res.output.strip().endswith('ans')
    assert calls['chat_question'] == 'hello'

