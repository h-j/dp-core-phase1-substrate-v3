"""
Phase 4: Shared Pytest Fixtures for DP-Core tests.
Zero external service dependencies required.
"""
import pytest
from unittest.mock import MagicMock


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
