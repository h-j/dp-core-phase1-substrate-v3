"""
Tests for LLMLedger and OllamaClient integration across LIVE, REPLAY, and AUTO modes.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from interfaces.llm_ledger import LLMLedger, LedgerMode, LedgerMissError
from interfaces.ollama_client import OllamaClient


@pytest.fixture
def temp_ledger_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    # Remove file so test can verify auto-creation
    if tmp_path.exists():
        tmp_path.unlink()
    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


def test_ledger_file_created_automatically(temp_ledger_file):
    assert not temp_ledger_file.exists()
    ledger = LLMLedger(mode="auto", path=temp_ledger_file)
    assert temp_ledger_file.exists()
    with open(temp_ledger_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}


def test_live_mode_records_and_calls_provider(temp_ledger_file):
    ledger = LLMLedger(mode="live", path=temp_ledger_file)
    mock_provider = MagicMock(return_value="live response 1")

    res = ledger.get_or_execute(
        model="llama3.2",
        prompt="Explain momentum trading",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider,
    )

    assert res == "live response 1"
    mock_provider.assert_called_once()

    # Check that ledger file has recorded entry
    with open(temp_ledger_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    key = list(data.keys())[0]
    assert data[key]["response"] == "live response 1"
    assert data[key]["prompt"] == "Explain momentum trading"


def test_replay_mode_zero_live_calls_and_miss_error(temp_ledger_file):
    # First, record a prompt using LIVE mode
    live_ledger = LLMLedger(mode="live", path=temp_ledger_file)
    mock_live = MagicMock(return_value="recorded answer")
    live_ledger.get_or_execute(
        model="llama3.2",
        prompt="Existing prompt",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_live,
    )

    # Now load in REPLAY mode
    replay_ledger = LLMLedger(mode="replay", path=temp_ledger_file)
    mock_should_not_be_called = MagicMock()

    # Hit case: returns recorded response with zero live provider calls
    res = replay_ledger.get_or_execute(
        model="llama3.2",
        prompt="Existing prompt",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_should_not_be_called,
    )
    assert res == "recorded answer"
    mock_should_not_be_called.assert_not_called()

    # Miss case: raises explicit LedgerMissError (which is a subclass of RuntimeError)
    with pytest.raises(LedgerMissError) as exc_info:
        replay_ledger.get_or_execute(
            model="llama3.2",
            prompt="Missing prompt that was never recorded",
            temperature=0.0,
            seed=42,
            json_format=False,
            live_provider=mock_should_not_be_called,
        )
    
    assert "not found in ledger" in str(exc_info.value)
    mock_should_not_be_called.assert_not_called()


def test_auto_mode_records_only_unseen_prompts(temp_ledger_file):
    auto_ledger = LLMLedger(mode="auto", path=temp_ledger_file)
    mock_provider = MagicMock(side_effect=["first response", "second response"])

    # Call 1: Unseen prompt -> calls live provider
    res1 = auto_ledger.get_or_execute(
        model="llama3.2",
        prompt="Test prompt A",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider,
    )
    assert res1 == "first response"
    assert mock_provider.call_count == 1

    # Call 2: Seen prompt -> returns from ledger without calling provider
    res2 = auto_ledger.get_or_execute(
        model="llama3.2",
        prompt="Test prompt A",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider,
    )
    assert res2 == "first response"
    # Call count should STILL be 1 (provider was not called second time)
    assert mock_provider.call_count == 1

    # Call 3: New unseen prompt -> calls live provider
    res3 = auto_ledger.get_or_execute(
        model="llama3.2",
        prompt="Test prompt B",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider,
    )
    assert res3 == "second response"
    assert mock_provider.call_count == 2


def test_ollama_client_integration(temp_ledger_file):
    ledger = LLMLedger(mode="auto", path=temp_ledger_file)
    client = OllamaClient(temperature=0.0, seed=42, ledger=ledger)

    with patch("ollama.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "ollama mocked response"}}
        
        # 1st execution (Live/Auto) -> calls Ollama
        res1 = client.generate("Analyze signal", json_format=True)
        assert res1 == "ollama mocked response"
        mock_chat.assert_called_once()

        # 2nd execution (Auto hit) -> served from ledger
        res2 = client.generate("Analyze signal", json_format=True)
        assert res2 == "ollama mocked response"
        # mock_chat should not have been called a second time
        assert mock_chat.call_count == 1


def test_environment_variable_mode_override():
    os.environ["LLM_LEDGER_MODE"] = "replay"
    try:
        ledger = LLMLedger()
        assert ledger.mode == LedgerMode.REPLAY
    finally:
        os.environ.pop("LLM_LEDGER_MODE", None)
