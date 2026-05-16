from sqlalchemy import create_engine
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

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)