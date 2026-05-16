from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    OLLAMA_MODEL: str = "llama3"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dp_core"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    DUCKDB_PATH: str = "market_memory.duckdb"

    class Config:
        env_file = ".env"


settings = Settings()
