try:
    from pydantic_settings import BaseSettings
except Exception:
    try:
        from pydantic import BaseSettings
    except Exception:
        from pydantic import BaseModel

        class BaseSettings(BaseModel):
            class Config:
                env_file = ".env"


class Settings(BaseSettings):

    OLLAMA_MODEL: str = "llama3.2"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dp_core"
    POSTGRES_USER: str = "hemantj"
    POSTGRES_PASSWORD: str = ""

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    DUCKDB_PATH: str = "market_memory.duckdb"
    LLM_AUDIT_ENABLED: bool = True
    LLM_LEDGER_MODE: str = "auto"
    LLM_LEDGER_PATH: str = "data/llm_ledger.json"

    class Config:
        env_file = ".env"


settings = Settings()


# ---------------------------------------------------------------------------
# Cognition Tuning Parameters
# Loaded from config/cognition_tuning.yaml (Phase 5 — 2026-07-20).
# Use cognition_tuning["confidence_evolution"]["outcome_high_threshold"]
# to access values. Falls back to an empty dict if the file is missing.
# ---------------------------------------------------------------------------
import pathlib


def _load_cognition_tuning() -> dict:
    yaml_path = pathlib.Path(__file__).parent / "cognition_tuning.yaml"
    if not yaml_path.exists():
        return {}
    try:
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


cognition_tuning: dict = _load_cognition_tuning()
