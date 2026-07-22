"""
Tests for LLMLedger and OllamaClient integration across RECORD/LIVE, REPLAY, and AUTO modes.
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
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
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
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 1
    header = json.loads(lines[0])
    assert header["type"] == "header"
    assert header["format"] == "jsonl"


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

    # Check JSONL header + 1 record line
    with open(temp_ledger_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 2
    header = json.loads(lines[0])
    record = json.loads(lines[1])
    assert header["type"] == "header"
    assert record["response"] == "live response 1"
    assert record["prompt"] == "Explain momentum trading"
    assert "prompt_hash" in record
    assert "replay_metadata" in record


def test_replay_mode_zero_live_calls_and_miss_error(temp_ledger_file):
    # First, record a prompt using LIVE mode
    live_ledger = LLMLedger(mode="record", path=temp_ledger_file)
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
    assert "Zero live calls permitted" in str(exc_info.value)
    mock_should_not_be_called.assert_not_called()


def test_auto_mode_replays_existing_and_records_unseen(temp_ledger_file):
    ledger = LLMLedger(mode="auto", path=temp_ledger_file)
    mock_provider_1 = MagicMock(return_value="response for p1")

    # Call 1 (unseen): calls provider & records
    res1 = ledger.get_or_execute(
        model="llama3.2",
        prompt="Prompt 1",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider_1,
    )
    assert res1 == "response for p1"
    assert mock_provider_1.call_count == 1

    # Call 2 (seen): returns recorded without provider call
    mock_provider_2 = MagicMock()
    res1_replay = ledger.get_or_execute(
        model="llama3.2",
        prompt="Prompt 1",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider_2,
    )
    assert res1_replay == "response for p1"
    mock_provider_2.assert_not_called()

    # Call 3 (new unseen prompt): calls new provider
    mock_provider_3 = MagicMock(return_value="response for p2")
    res2 = ledger.get_or_execute(
        model="llama3.2",
        prompt="Prompt 2",
        temperature=0.0,
        seed=42,
        json_format=False,
        live_provider=mock_provider_3,
    )
    assert res2 == "response for p2"
    mock_provider_3.assert_called_once()


def test_ollama_client_integration_with_ledger(temp_ledger_file):
    ledger = LLMLedger(mode="auto", path=temp_ledger_file)
    client = OllamaClient(model="llama3.2", ledger=ledger)

    mock_chat_response = {"message": {"content": "ollama live output"}}
    with patch("ollama.chat", return_value=mock_chat_response) as mock_chat:
        res = client.generate("Test prompt for OllamaClient")
        assert res == "ollama live output"
        mock_chat.assert_called_once()

    # Second call should serve from ledger without calling ollama.chat
    with patch("ollama.chat") as mock_chat_2:
        res2 = client.generate("Test prompt for OllamaClient")
        assert res2 == "ollama live output"
        mock_chat_2.assert_not_called()
