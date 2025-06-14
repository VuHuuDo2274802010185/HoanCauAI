import os
import pytest
from modules.model_fetcher import ModelFetcher

@pytest.fixture
def google_key():
    return os.getenv("GOOGLE_API_KEY")

@pytest.fixture
def openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")

def test_google_models(google_key):
    if not google_key:
        pytest.skip("GOOGLE_API_KEY not set")
    models = ModelFetcher.get_google_models(google_key)
    assert isinstance(models, list)
    assert models, "Expected at least one Google model"

def test_openrouter_models(openrouter_key):
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    models = ModelFetcher.get_openrouter_models(openrouter_key)
    assert isinstance(models, list)
    assert all('id' in m for m in models)