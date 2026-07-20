"""
OllamaClient — LLM interface for DP-Core reflective cognition.

Phase 6 (2026-07-20): Added content-addressable prompt/response cache.
  - Cache key: SHA-256(model + prompt + temperature + seed + json_format)
  - Cache backend: data/llm_cache/<hash>.json (inspectable, no SQLite dep)
  - On cache hit: returns stored response without calling Ollama.
  - On cache miss: calls Ollama and stores the response.
  - Offline mode (--offline flag or REPLAY_OFFLINE=1 env): raises RuntimeError
    on cache miss rather than calling the LLM.
    This enables fully deterministic replay verification without Ollama.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

import ollama

from config.settings import settings

logger = logging.getLogger(__name__)

# Offline mode: set REPLAY_OFFLINE=1 env or use run.py --offline flag
_OFFLINE_MODE: bool = os.environ.get("REPLAY_OFFLINE", "0").strip() == "1"

# Default cache directory (overridable for tests)
_CACHE_DIR: Path = Path("data/llm_cache")


def _cache_key(model: str, prompt: str, temperature: float, seed: Optional[int], json_format: bool) -> str:
    payload = f"{model}|{prompt}|{temperature}|{seed}|{json_format}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
    def __init__(self, temperature: float = 0.0, seed: Optional[int] = None):
        self.temperature = temperature
        self.seed = seed

    def generate(self, prompt: str, json_format: bool = False) -> str:
        model = settings.OLLAMA_MODEL
        key = _cache_key(model, prompt, self.temperature, self.seed, json_format)

        cached = _read_cache(key)
        if cached is not None:
            logger.debug("[OllamaClient] Cache hit: %s", key[:16])
            return cached

        if _OFFLINE_MODE:
            raise RuntimeError(
                f"[OllamaClient] Offline mode: cache miss for key {key[:16]}. "
                "Run with Ollama first to warm the cache, then replay offline."
            )

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

        content = response["message"]["content"]
        _write_cache(key, content)
        logger.debug("[OllamaClient] Cache miss → stored: %s", key[:16])
        return content
