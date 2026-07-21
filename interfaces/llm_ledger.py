"""
LLMLedger — Dedicated I/O Ledger for LLM calls supporting Live, Replay, and Auto modes.

Preserves the existing LLM interface boundary while enabling fully deterministic replay,
recording of unseen prompts, and explicit error handling on ledger misses.
"""
import enum
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Any

from config.settings import settings

logger = logging.getLogger(__name__)


class LedgerMode(str, enum.Enum):
    LIVE = "live"
    REPLAY = "replay"
    AUTO = "auto"

    @classmethod
    def from_str(cls, val: str) -> "LedgerMode":
        val_lower = str(val).strip().lower()
        for mode in cls:
            if mode.value == val_lower:
                return mode
        raise ValueError(f"Invalid LedgerMode '{val}'. Supported modes: {[m.value for m in cls]}")


class LedgerMissError(RuntimeError):
    """Raised when a response is requested in REPLAY mode but the entry is not found in the ledger."""
    pass


def get_default_ledger_path() -> Path:
    configured = getattr(settings, "LLM_LEDGER_PATH", "data/llm_ledger.json")
    return Path(configured)


def compute_prompt_key(
    model: str,
    prompt: str,
    temperature: float,
    seed: Optional[int],
    json_format: bool,
) -> str:
    payload = f"{model}|{prompt}|{temperature}|{seed}|{json_format}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMLedger:
    """
    Manages LLM request recording and response replay behind the LLM client interface.

    Modes:
      - LIVE: Always calls live LLM and records prompt/response pair to ledger.
      - REPLAY: Returns recorded response from ledger. Performs zero live LLM calls.
                Raises LedgerMissError if prompt entry is missing.
      - AUTO: Returns recorded response if available; calls live LLM and records only
              unseen prompts.
    """

    def __init__(self, mode: Optional[str] = None, path: Optional[Path] = None):
        self.path = Path(path) if path is not None else get_default_ledger_path()
        self.mode = self._resolve_mode(mode)
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._load_ledger()

    def _resolve_mode(self, explicit_mode: Optional[str]) -> LedgerMode:
        if explicit_mode:
            return LedgerMode.from_str(explicit_mode)
        
        env_mode = os.environ.get("LLM_LEDGER_MODE")
        if env_mode:
            return LedgerMode.from_str(env_mode)

        if os.environ.get("REPLAY_OFFLINE", "0").strip() == "1":
            return LedgerMode.REPLAY

        setting_mode = getattr(settings, "LLM_LEDGER_MODE", "auto")
        return LedgerMode.from_str(setting_mode)

    def _load_ledger(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception as exc:
                logger.warning("[LLMLedger] Failed to load ledger from %s: %s", self.path, exc)
                self._entries = {}
        else:
            self._entries = {}
            self._save_ledger()

    def _save_ledger(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("[LLMLedger] Failed to write ledger to %s: %s", self.path, exc)

    def get_or_execute(
        self,
        model: str,
        prompt: str,
        temperature: float,
        seed: Optional[int],
        json_format: bool,
        live_provider: Callable[[], str],
    ) -> str:
        key = compute_prompt_key(model, prompt, temperature, seed, json_format)
        active_mode = self.mode

        logger.info(
            "[LLMLedger] Request | Mode: %s | Key: %s", active_mode.value.upper(), key[:16]
        )

        if active_mode == LedgerMode.REPLAY:
            if key in self._entries:
                entry = self._entries[key]
                logger.info("[LLMLedger] Mode: REPLAY | Hit | Key: %s", key[:16])
                return entry["response"]
            
            # Check legacy llm_cache backend if available
            legacy_resp = self._check_legacy_cache(key)
            if legacy_resp is not None:
                logger.info("[LLMLedger] Mode: REPLAY | Legacy cache hit | Key: %s", key[:16])
                self._record_entry(key, model, prompt, temperature, seed, json_format, legacy_resp)
                return legacy_resp

            logger.error("[LLMLedger] Mode: REPLAY | MISS | Key: %s", key[:16])
            raise LedgerMissError(
                f"[LLMLedger] Offline mode: cache miss for key {key[:16]}. "
                f"Prompt key '{key[:16]}' not found in ledger '{self.path}'. "
                f"Zero live calls permitted in replay mode."
            )

        if active_mode == LedgerMode.AUTO:
            if key in self._entries:
                entry = self._entries[key]
                logger.info("[LLMLedger] Mode: AUTO | Hit | Key: %s", key[:16])
                return entry["response"]
            
            legacy_resp = self._check_legacy_cache(key)
            if legacy_resp is not None:
                logger.info("[LLMLedger] Mode: AUTO | Legacy cache hit | Key: %s", key[:16])
                self._record_entry(key, model, prompt, temperature, seed, json_format, legacy_resp)
                return legacy_resp
            
            logger.info("[LLMLedger] Mode: AUTO | Unseen prompt -> executing live provider | Key: %s", key[:16])
            response_text = live_provider()
            self._record_entry(key, model, prompt, temperature, seed, json_format, response_text)
            return response_text

        # Mode == LIVE
        logger.info("[LLMLedger] Mode: LIVE | Executing live provider & recording | Key: %s", key[:16])
        response_text = live_provider()
        self._record_entry(key, model, prompt, temperature, seed, json_format, response_text)
        return response_text

    def _record_entry(
        self,
        key: str,
        model: str,
        prompt: str,
        temperature: float,
        seed: Optional[int],
        json_format: bool,
        response: str,
    ) -> None:
        self._entries[key] = {
            "key": key,
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "seed": seed,
            "json_format": json_format,
            "response": response,
            "timestamp": time.time(),
        }
        self._save_ledger()

    def _check_legacy_cache(self, key: str) -> Optional[str]:
        legacy_file = Path("data/llm_cache") / f"{key}.json"
        if legacy_file.exists():
            try:
                with open(legacy_file, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("response")
            except Exception:
                return None
        return None
