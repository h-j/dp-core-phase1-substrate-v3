from memory.relational.base import Base
from memory.relational.postgres_client import engine

from memory.relational.models.observation_model import ObservationModel
from memory.relational.models.abstraction_model import AbstractionModel
from memory.relational.models.theory_model import TheoryModel
from memory.relational.models.validation_model import ValidationModel
from memory.relational.models.reflection_model import ReflectionModel
from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.models.reflective_memory_model import (
    ReflectiveMemoryModel
)


Base.metadata.create_all(bind=engine)

print("Database schema initialized.")
