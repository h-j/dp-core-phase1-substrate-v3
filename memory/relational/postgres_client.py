from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import sessionmaker

from config.settings import settings


DATABASE_URL = (
    f"postgresql://"
    f"{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

try:
    engine = create_engine(DATABASE_URL, echo=False)
    # Verify the database connection early; raise if unavailable
    with engine.connect() as _:
        pass
except (ImportError, ModuleNotFoundError, NoSuchModuleError, Exception) as exc:
    raise RuntimeError(
        f"PostgreSQL unavailable or misconfigured: {exc}. Ensure Postgres is running and settings are correct."
    ) from exc

from memory.relational.base import Base
import memory.relational.models  # noqa: F401
Base.metadata.create_all(engine)

# PHASE 4: Fail-fast schema validation (startup check)
from memory.relational.schema_validator import validate_schema_startup
validate_schema_startup(engine)

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


SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

SessionLocal = lambda *args, **kwargs: SessionContext(SessionFactory(*args, **kwargs))