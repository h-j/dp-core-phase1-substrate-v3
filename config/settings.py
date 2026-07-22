"""
Centralized Runtime Configuration for DP-Core.

Runtime parameters for PostgreSQL, Neo4j, DuckDB, Ollama LLM, and LLM Ledger.
Configure environment overrides in a local `.env` file (never committed to git).
"""
import pathlib
from typing import Any, Dict

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    try:
        from pydantic import BaseSettings

        class SettingsConfigDict(dict):
            pass

    except Exception:
        from pydantic import BaseModel

        class BaseSettings(BaseModel):
            pass

        class SettingsConfigDict(dict):
            pass


class Settings(BaseSettings):
    """
    Central runtime settings instance for DP-Core reflective cognition substrate.
    """

    # -----------------------------------------------------------------------
    # Ollama LLM Configuration
    # Set OLLAMA_MODEL to your local model tag (e.g., 'llama3.2', 'llama3', 'mistral')
    # -----------------------------------------------------------------------
    OLLAMA_MODEL: str = "llama3.2"

    # -----------------------------------------------------------------------
    # PostgreSQL Connection Parameters
    # Override via environment variables or local .env file
    # -----------------------------------------------------------------------
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dp_core"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""

    # -----------------------------------------------------------------------
    # Neo4j Lineage Graph Parameters
    # Insert real URI, username, and password for graph persistence
    # -----------------------------------------------------------------------
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # -----------------------------------------------------------------------
    # DuckDB Market Memory Path
    # Local DuckDB database file location for market snapshots
    # -----------------------------------------------------------------------
    DUCKDB_PATH: str = "market_memory.duckdb"

    # -----------------------------------------------------------------------
    # LLM Ledger & Auditing Parameters
    # LLM_LEDGER_MODE can be 'live', 'replay', or 'auto'
    # -----------------------------------------------------------------------
    LLM_AUDIT_ENABLED: bool = True
    LLM_LEDGER_MODE: str = "auto"
    LLM_LEDGER_PATH: str = "data/llm_ledger.json"

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# ---------------------------------------------------------------------------
# Cognition Tuning Parameters
# Loaded from config/cognition_tuning.yaml.
# ---------------------------------------------------------------------------
def _load_cognition_tuning() -> Dict[str, Any]:
    yaml_path = pathlib.Path(__file__).parent / "cognition_tuning.yaml"
    if not yaml_path.exists():
        return {}
    try:
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


cognition_tuning: Dict[str, Any] = _load_cognition_tuning()
