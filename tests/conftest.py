"""
Phase 4: Shared Pytest Fixtures for DP-Core tests.
Zero external service dependencies required for collection.
Service-gated tests are marked with @pytest.mark.requires_postgres or @pytest.mark.requires_ollama
and automatically skip unless DP_TEST_POSTGRES=1 or DP_TEST_OLLAMA=1 is set.
"""
import os
from unittest.mock import MagicMock
import pytest


def pytest_runtest_setup(item):
    """
    Hook to skip tests marked with requires_postgres or requires_ollama
    if the corresponding environment variable (DP_TEST_POSTGRES=1 or DP_TEST_OLLAMA=1) is not set.
    """
    for marker in item.iter_markers(name="requires_postgres"):
        if os.environ.get("DP_TEST_POSTGRES") != "1":
            pytest.skip("PostgreSQL required (set DP_TEST_POSTGRES=1 to run)")

    for marker in item.iter_markers(name="requires_ollama"):
        if os.environ.get("DP_TEST_OLLAMA") != "1":
            pytest.skip("Ollama LLM required (set DP_TEST_OLLAMA=1 to run)")


@pytest.fixture
def mock_ollama_client(monkeypatch):
    """Mocks OllamaClient.generate to return clean deterministic JSON without LLM calls."""
    mock_client = MagicMock()
    mock_client.generate.return_value = '{"claim": "test claim", "direction": "bullish", "horizon": "5d"}'
    monkeypatch.setattr("interfaces.ollama_client.OllamaClient", lambda *args, **kwargs: mock_client)
    return mock_client


@pytest.fixture
def tmp_repo_dir(tmp_path):
    """Provides a clean temporary directory for repository tests."""
    return tmp_path
