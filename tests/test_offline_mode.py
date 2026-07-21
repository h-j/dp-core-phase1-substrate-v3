import os
import uuid
from unittest.mock import patch

import pytest

# 1. Import OllamaClient FIRST (before setting REPLAY_OFFLINE env var)
from interfaces.ollama_client import OllamaClient


def test_offline_mode_set_after_import_raises():
    # Set environment variable AFTER import
    os.environ["REPLAY_OFFLINE"] = "1"
    try:
        client = OllamaClient()
        unique_prompt = f"cache_miss_test_{uuid.uuid4()}"

        with pytest.raises(RuntimeError) as exc_info:
            client.generate(unique_prompt)

        assert "Offline mode: cache miss" in str(exc_info.value)
    finally:
        os.environ.pop("REPLAY_OFFLINE", None)


def test_offline_mode_disabled_does_not_raise_offline_error():
    # Ensure REPLAY_OFFLINE is "0" or unset
    os.environ["REPLAY_OFFLINE"] = "0"
    try:
        client = OllamaClient()
        unique_prompt = f"cache_miss_test_{uuid.uuid4()}"

        # Mock ollama.chat so test does not require a live Ollama connection
        with patch("ollama.chat") as mock_chat:
            mock_chat.return_value = {"message": {"content": "mocked response"}}
            res = client.generate(unique_prompt)
            assert res == "mocked response"
            mock_chat.assert_called_once()
    finally:
        os.environ.pop("REPLAY_OFFLINE", None)
