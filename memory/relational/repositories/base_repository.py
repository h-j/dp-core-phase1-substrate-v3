import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Assume SessionLocal is defined in memory.relational.database
# This is a common pattern for managing SQLAlchemy sessions.
try:
    from memory.relational.database import SessionLocal
except ImportError:
    # Fallback for testing or if database.py is not yet created
    # In a real scenario, this ImportError should be resolved.
    logging.warning(
        "SessionLocal not found in memory.relational.database. "
        "BaseRepository will not be able to create sessions automatically."
    )
    SessionLocal = None


class BaseRepository:
    """
    Base class for all repositories, providing common database operations.
    Manages its own session lifecycle for each operation.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_session(self) -> Session:
        """
        Retrieves a new database session.
        Returns a SQLAlchemy Session object.
        """
        if SessionLocal:
            return SessionLocal()  # SessionLocal() returns a session object
        raise RuntimeError(
            "SessionLocal is not configured. Cannot get database session."
        )

    def _save(self, model_instance):
        """
        Saves a model instance to the database.
        """
        with self._get_session() as session:
            session.add(model_instance)
            try:
                session.commit()
                session.refresh(model_instance)
                return model_instance
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"Error saving {type(model_instance).__name__}: {e}")
                raise

    def get_by_id(self, model_class, item_id: int):
        """Retrieves an item by its ID."""
        with self._get_session() as session:
            try:
                return (
                    session.query(model_class).filter(model_class.id == item_id).first()
                )
            except SQLAlchemyError as e:
                # For read operations, rollback might not be strictly necessary, but it's harmless.
                session.rollback()
                self.logger.error(
                    f"Error getting {model_class.__name__} by ID {item_id}: {e}"
                )
                raise
