"""
OllamaClient — LLM interface for DP-Core reflective cognition.

Phase 6 (2026-07-20): Content-addressable prompt/response ledger integration.
  - Delegates prompt recording and deterministic replay to LLMLedger.
  - Supports Live, Replay, and Auto modes.
  - Preserves exact interface boundary: OllamaClient.generate(prompt, json_format).
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

import ollama

from config.settings import settings
from interfaces.llm_ledger import LLMLedger, compute_prompt_key

logger = logging.getLogger(__name__)


# Offline mode helper (for backward compatibility)
def _offline_mode() -> bool:
    return os.environ.get("REPLAY_OFFLINE", "0").strip() == "1"


# Default cache directory helper
_CACHE_DIR: Path = Path("data/llm_cache")


def _cache_key(model: str, prompt: str, temperature: float, seed: Optional[int], json_format: bool) -> str:
    return compute_prompt_key(model, prompt, temperature, seed, json_format)


def _read_cache(key: str) -> Optional[str]:
    cache_file = _CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("response")
        except Exception:
            return None
    return None


def _write_cache(key: str, response: str) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = _CACHE_DIR / f"{key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"response": response}, f, ensure_ascii=False)
    except Exception as exc:
        logger.warning("[OllamaClient] Cache write failed: %s", exc)


class OllamaClient:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.0,
        seed: Optional[int] = None,
        mode: Optional[str] = None,
        ledger: Optional[LLMLedger] = None,
    ):
        self.model = model or getattr(settings, "OLLAMA_MODEL", "llama3.2")
        self.temperature = temperature
        self.seed = seed
        self.ledger = ledger if ledger is not None else LLMLedger(mode=mode)

    def generate(self, prompt: str, json_format: bool = False) -> str:
        model = self.model or getattr(settings, "OLLAMA_MODEL", "llama3.2")

        def _live_provider() -> str:
            options = {
                "temperature": self.temperature,
                "top_p": 1,
            }
            if self.seed is not None:
                options["seed"] = self.seed

            response = ollama.chat(
                model=model,
                options=options,
                format="json" if json_format else "",
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]

        return self.ledger.get_or_execute(
            model=model,
            prompt=prompt,
            temperature=self.temperature,
            seed=self.seed,
            json_format=json_format,
            live_provider=_live_provider,
        )
