"""
LLMLedger — Dedicated I/O Ledger for LLM calls supporting Record/Live, Replay, and Auto modes.

Implements an append-only JSONL ledger preserving the existing LLM interface boundary
while enabling fully deterministic replay, recording of unseen prompts, and explicit error
handling on ledger misses.
"""
from datetime import datetime, timezone
import enum
import hashlib
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class LedgerMode(str, enum.Enum):
    RECORD = "record"
    LIVE = "live"
    REPLAY = "replay"
    AUTO = "auto"

    @classmethod
    def from_str(cls, val: str) -> "LedgerMode":
        val_lower = str(val).strip().lower()
        if val_lower in ("record", "live"):
            return cls.LIVE
        for mode in cls:
            if mode.value == val_lower:
                return mode
        raise ValueError(
            f"Invalid LedgerMode '{val}'. Supported modes: 'record', 'live', 'replay', 'auto'"
        )


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

    Persists an append-only JSONL format:
      - Line 1: Header metadata dict `{"type": "header", "ledger_version": "1.0", ...}`
      - Lines 2+: Call records containing `prompt_hash`, `prompt`, `response`, `model_digest`, etc.
    """

    def __init__(self, mode: Optional[str] = None, path: Optional[Path] = None):
        self.path = Path(path) if path is not None else get_default_ledger_path()
        self.mode = self._resolve_mode(mode)
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._header: Optional[Dict[str, Any]] = None
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
        """Loads ledger entries from JSONL or legacy JSON format."""
        self._entries = {}
        if not self.path.exists():
            self._ensure_header()
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self._ensure_header()
                    return

                # Check if file starts with JSONL header or array/object
                first_char = content[0]
                if first_char == "{":
                    lines = content.splitlines()
                    # Attempt JSONL parse
                    try:
                        line0 = json.loads(lines[0])
                        if line0.get("type") == "header":
                            self._header = line0
                            record_lines = lines[1:]
                        else:
                            record_lines = lines
                    except Exception:
                        record_lines = lines

                    for line in record_lines:
                        line_str = line.strip()
                        if not line_str:
                            continue
                        try:
                            item = json.loads(line_str)
                            key = item.get("prompt_hash") or item.get("key")
                            if key and "response" in item:
                                self._entries[key] = item
                        except Exception:
                            continue

                else:
                    # Fallback to standard JSON dictionary
                    try:
                        raw_data = json.loads(content)
                        if isinstance(raw_data, dict):
                            for k, v in raw_data.items():
                                if isinstance(v, dict) and "response" in v:
                                    self._entries[k] = v
                    except Exception:
                        pass

        except Exception as exc:
            logger.warning("[LLMLedger] Failed to read ledger from %s: %s", self.path, exc)

        self._ensure_header()

    def _ensure_header(self) -> None:
        if self._header is None:
            self._header = {
                "type": "header",
                "ledger_version": "1.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "format": "jsonl",
            }
            if not self.path.exists():
                try:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(self._header, ensure_ascii=False) + "\n")
                except Exception as exc:
                    logger.warning("[LLMLedger] Failed to write header to %s: %s", self.path, exc)

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
            "[LLMLedger] Request | Mode: %s | Prompt Hash: %s",
            active_mode.value.upper(),
            key[:16],
        )

        if active_mode == LedgerMode.REPLAY:
            if key in self._entries:
                entry = self._entries[key]
                logger.info("[LLMLedger] Mode: REPLAY | Hit | Hash: %s", key[:16])
                return entry["response"]

            # Check legacy llm_cache backend if available
            legacy_resp = self._check_legacy_cache(key)
            if legacy_resp is not None:
                logger.info("[LLMLedger] Mode: REPLAY | Legacy cache hit | Hash: %s", key[:16])
                self._record_entry(key, model, prompt, temperature, seed, json_format, legacy_resp)
                return legacy_resp

            logger.error("[LLMLedger] Mode: REPLAY | MISS | Hash: %s", key[:16])
            raise LedgerMissError(
                f"[LLMLedger] Offline mode: cache miss for prompt hash {key[:16]}. "
                f"Prompt hash '{key[:16]}' not found in ledger '{self.path}'. "
                f"Zero live calls permitted in replay mode."
            )

        if active_mode == LedgerMode.AUTO:
            if key in self._entries:
                entry = self._entries[key]
                logger.info("[LLMLedger] Mode: AUTO | Hit | Hash: %s", key[:16])
                return entry["response"]

            legacy_resp = self._check_legacy_cache(key)
            if legacy_resp is not None:
                logger.info("[LLMLedger] Mode: AUTO | Legacy cache hit | Hash: %s", key[:16])
                self._record_entry(key, model, prompt, temperature, seed, json_format, legacy_resp)
                return legacy_resp

            logger.info(
                "[LLMLedger] Mode: AUTO | Unseen prompt -> executing live provider | Hash: %s",
                key[:16],
            )
            response_text = live_provider()
            self._record_entry(key, model, prompt, temperature, seed, json_format, response_text)
            return response_text

        # Mode == LIVE / RECORD
        logger.info(
            "[LLMLedger] Mode: LIVE/RECORD | Executing live provider & appending | Hash: %s",
            key[:16],
        )
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
        record = {
            "prompt_hash": key,
            "key": key,
            "model_digest": model,
            "model": model,
            "prompt": prompt,
            "response": response,
            "timestamp": time.time(),
            "iso_timestamp": datetime.now(timezone.utc).isoformat(),
            "replay_metadata": {
                "temperature": temperature,
                "seed": seed,
                "json_format": json_format,
            },
        }

        self._entries[key] = record
        self._append_to_file(record)

    def _append_to_file(self, record: Dict[str, Any]) -> None:
        """Appends a single JSON record to the JSONL file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # If file does not exist, write header line first
            if not self.path.exists():
                with open(self.path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(self._header, ensure_ascii=False) + "\n")

            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("[LLMLedger] Failed to append record to %s: %s", self.path, exc)

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
