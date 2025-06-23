import sys
import types
import importlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))


def _dummy_streamlit(theme="dark"):
    class DummyCM:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    class DummySidebar:
        def expander(self, *a, **k):
            return DummyCM()
        def columns(self, *a, **k):
            return (DummyCM(), DummyCM())
        def selectbox(self, *a, **k):
            opts = k.get("options", [])
            return opts[0] if opts else None
        def text_input(self, *a, **k):
            return ""
        def button(self, *a, **k):
            return False
        def __getattr__(self, name):
            return lambda *a, **k: None

    class DummyStreamlit:
        def __init__(self):
            self.session_state = {}
            self.sidebar = DummySidebar()
            self._options = {"theme.base": theme}
            self.runtime = types.SimpleNamespace(
                exists=lambda: False,
                scriptrunner=types.SimpleNamespace(get_script_run_ctx=lambda suppress_warning=True: None),
            )
        def get_option(self, key):
            return self._options.get(key)
        def set_page_config(self, *a, **k):
            pass
        def markdown(self, *a, **k):
            pass
        def tabs(self, names):
            return [DummyCM() for _ in names]
        def __getattr__(self, name):
            return lambda *a, **k: None

    return DummyStreamlit()


def _install_app(monkeypatch):
    # stub streamlit
    dummy_st = _dummy_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", dummy_st)

    # minimal modules.config
    cfg = types.SimpleNamespace(
        LLM_CONFIG={"provider": "google", "model": "m", "api_key": "", "available_models": []},
        get_models_for_provider=lambda *a, **k: [],
        get_model_price=lambda m: "unknown",
        OUTPUT_CSV="out.csv",
        LOG_DIR=Path("log"),
        LOG_FILE=Path("log/app.log"),
        GOOGLE_API_KEY="",
        OPENROUTER_API_KEY="",
        EMAIL_HOST="",
        EMAIL_PORT="",
        EMAIL_USER="",
        EMAIL_PASS="",
        EMAIL_UNSEEN_ONLY=False,
    )
    monkeypatch.setitem(sys.modules, "modules.config", cfg)
    monkeypatch.setitem(sys.modules, "modules.auto_fetcher", types.SimpleNamespace(watch_loop=lambda *a, **k: None))
    monkeypatch.setitem(sys.modules, "modules.qa_chatbot", types.ModuleType("modules.qa_chatbot"))

    # stub tabs
    tab_mod = types.ModuleType("main_engine.tabs")
    simple_tab = types.SimpleNamespace(render=lambda *a, **k: None)
    for name in ["fetch_tab", "process_tab", "single_tab", "results_tab", "chat_tab"]:
        setattr(tab_mod, name, simple_tab)
        monkeypatch.setitem(sys.modules, f"main_engine.tabs.{name}", simple_tab)
    monkeypatch.setitem(sys.modules, "main_engine.tabs", tab_mod)

    mod = importlib.import_module("main_engine.app")
    importlib.reload(mod)
    return mod


def _css_dark_values():
    css = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text()
    m = re.search(r':root\[data-theme="dark"\]\s*{([^}]*)}', css, re.M)
    assert m, "dark theme section missing"
    body = m.group(1)
    def g(var):
        m2 = re.search(rf'--{var}:\s*([^;]+);', body)
        return m2.group(1).strip()
    return {
        "text_color": g("cv-text-color"),
        "background_color": g("cv-bg-color"),
        "secondary_color": g("cv-accent-color"),
        "accent_color": g("btn-gold"),
    }


def test_dark_theme_session_state(monkeypatch):
    app = _install_app(monkeypatch)
    expected = _css_dark_values()
    for k, v in expected.items():
        assert app.st.session_state[k] == v
