"""
LLM I/O Ledger Verification Script

Demonstrates:
  1. Execution 1: Prompts are recorded to the ledger in AUTO/LIVE mode.
  2. Execution 2: Responses are served entirely from the ledger in REPLAY mode with zero live LLM calls.
  3. Verification: Exact output matching between initial execution and deterministic replay.
  4. Logging: Logging the execution mode for every request.
"""
import json
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("verify_llm_ledger")

from interfaces.llm_ledger import LLMLedger, LedgerMode, LedgerMissError
from interfaces.ollama_client import OllamaClient


def run_verification() -> bool:
    logger.info("=== Starting LLM I/O Ledger End-to-End Verification ===")

    with tempfile.NamedTemporaryFile(suffix="_ledger.json", delete=False) as tmp:
        ledger_path = Path(tmp.name)
    if ledger_path.exists():
        ledger_path.unlink()

    test_prompts = [
        ("Evaluate regime transition probability for RELIANCE", True),
        ("Synthesize dialectical contradictions in sentiment indicator", False),
        ("Calculate Bayesian conviction score for window W3", True),
    ]

    mock_ollama_responses = {
        test_prompts[0][0]: '{"regime": "BULL", "probability": 0.82}',
        test_prompts[1][0]: "Contradiction detected between sentiment and volume indicators.",
        test_prompts[2][0]: '{"conviction_score": 0.91, "confidence": "HIGH"}',
    }

    def mock_chat_side_effect(model, options, format, messages):
        prompt = messages[0]["content"]
        resp_text = mock_ollama_responses.get(prompt, "Default mock response")
        return {"message": {"content": resp_text}}

    logger.info("--- Execution 1: Recording Prompts (Mode: AUTO / LIVE) ---")
    ledger_run1 = LLMLedger(mode="auto", path=ledger_path)
    client_run1 = OllamaClient(temperature=0.0, seed=42, ledger=ledger_run1)

    live_call_counter = MagicMock(side_effect=mock_chat_side_effect)

    outputs_run1 = []
    with patch("ollama.chat", side_effect=live_call_counter):
        for prompt, json_fmt in test_prompts:
            resp = client_run1.generate(prompt, json_format=json_fmt)
            outputs_run1.append(resp)
            logger.info("Run 1 Result: prompt='%s...' -> response='%s...'", prompt[:30], resp[:30])

    logger.info("Run 1 Live LLM call count: %d", live_call_counter.call_count)
    assert live_call_counter.call_count == 3, f"Expected 3 live calls, got {live_call_counter.call_count}"
    assert ledger_path.exists(), "Ledger file was not created automatically!"

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger_data = json.load(f)
    logger.info("Ledger file automatically created at %s with %d entries.", ledger_path, len(ledger_data))
    assert len(ledger_data) == 3

    logger.info("--- Execution 2: Deterministic Replay (Mode: REPLAY) ---")
    ledger_run2 = LLMLedger(mode="replay", path=ledger_path)
    client_run2 = OllamaClient(temperature=0.0, seed=42, ledger=ledger_run2)

    replay_mock_chat = MagicMock(side_effect=AssertionError("Live LLM called during REPLAY mode!"))

    outputs_run2 = []
    with patch("ollama.chat", side_effect=replay_mock_chat):
        for prompt, json_fmt in test_prompts:
            resp = client_run2.generate(prompt, json_format=json_fmt)
            outputs_run2.append(resp)
            logger.info("Run 2 Replay Result: prompt='%s...' -> response='%s...'", prompt[:30], resp[:30])

    logger.info("Run 2 Live LLM call count: %d (Zero live calls verified)", replay_mock_chat.call_count)
    assert replay_mock_chat.call_count == 0, "Replay mode performed live calls!"

    logger.info("--- Verification: Outputs Match & Missing Prompt Error ---")
    assert outputs_run1 == outputs_run2, "Outputs between live execution and replay DO NOT MATCH!"
    logger.info("SUCCESS: 100%% output matching between Live execution and Replay!")

    # Test explicit error on missing entry in REPLAY mode
    logger.info("--- Verification: Explicit Error on Unseen Prompt in REPLAY Mode ---")
    with patch("ollama.chat", side_effect=replay_mock_chat):
        try:
            client_run2.generate("Unseen prompt never recorded before")
            logger.error("FAILED: Missing prompt did not raise LedgerMissError!")
            return False
        except LedgerMissError as exc:
            logger.info("SUCCESS: Explicit error caught on missing ledger entry: %s", exc)

    # Cleanup temporary ledger file
    if ledger_path.exists():
        ledger_path.unlink()

    logger.info("=== ALL LLM I/O LEDGER VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
