"""
PostgreSQL Relational Client — Lazy & Service-Gated Connection Engine.

Defers database connection away from module import/collection time,
allowing clean pytest collection without external service dependencies.
"""
import logging
import os
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

from memory.relational.base import Base

logger = logging.getLogger("postgres_client")


DATABASE_URL = (
    f"postgresql://"
    f"{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

_engine = None
_engine_initialized = False


def get_engine():
    global _engine, _engine_initialized
    if _engine_initialized:
        return _engine
    _engine_initialized = True
    try:
        engine_inst = create_engine(DATABASE_URL, echo=False)
        with engine_inst.connect() as _:
            pass
        _engine = engine_inst
        # Run table creation & startup validation
        try:
            from memory.relational.base import Base
            import memory.relational.models  # noqa: F401
            from memory.market.market_observation_model import MarketObservationModel  # noqa: F401
            from memory.market.strategic_memory_model import StrategicMemoryModel as MarketStrategicMemoryModel  # noqa: F401
            from memory.relational.models.prediction_probe_model import PredictionProbeModel  # noqa: F401
            from memory.relational.models.transition_pressure_model import TransitionPressureModel  # noqa: F401
            from memory.relational.schema_validator import validate_schema_startup

            Base.metadata.create_all(_engine)
            validate_schema_startup(_engine)
        except Exception as e:
            logger.warning(f"PostgreSQL startup schema validation warning: {e}")
    except Exception as exc:
        _engine = None
        logger.debug(f"PostgreSQL not connected: {exc}")
    return _engine


class LazyEngineProxy:
    def __getattr__(self, name: str) -> Any:
        eng = get_engine()
        if eng is None:
            raise RuntimeError(
                "PostgreSQL unavailable or misconfigured. Ensure Postgres is running and DP_TEST_POSTGRES=1 is set."
            )
        return getattr(eng, name)


engine = LazyEngineProxy()


class SessionContext:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()


def SessionLocal(*args, **kwargs):
    eng = get_engine()
    if eng is None:
        raise RuntimeError(
            "PostgreSQL unavailable or misconfigured. Ensure Postgres is running (set DP_TEST_POSTGRES=1)."
        )
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False)
    return SessionContext(factory(*args, **kwargs))
