from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from memory.relational.models.base import Base

# Local SQLite configuration for development
SQLALCHEMY_DATABASE_URL = "sqlite:///./dp_cognition.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)