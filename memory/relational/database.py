"""Relational database shim — delegate to Postgres client.

This module previously created a local SQLite engine for development.
All runtime code should use PostgreSQL. Importing this module will
raise if the Postgres client is unavailable.
"""

try:
    from memory.relational.postgres_client import SessionLocal, engine, Base
except Exception as exc:
    raise RuntimeError(
        "Postgres relational client unavailable. Ensure PostgreSQL is configured and running."
    ) from exc


def init_db():
    """Initialize database tables using the Postgres engine."""
    Base.metadata.create_all(bind=engine)
