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
except (ImportError, ModuleNotFoundError, NoSuchModuleError):
    fallback_url = "sqlite:///market_memory.db"
    engine = create_engine(fallback_url, echo=False)

from memory.relational.base import Base
import memory.relational.models  # noqa: F401
Base.metadata.create_all(engine)

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