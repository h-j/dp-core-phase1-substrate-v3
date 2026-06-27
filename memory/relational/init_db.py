# Import the package to register everything defined in the models folder
import memory.relational.models  # noqa: F401
from memory.market.market_observation_model import \
    MarketObservationModel  # noqa: F401
from memory.relational.base import Base
from memory.relational.models.abstraction_model import AbstractionModel
from memory.relational.models.observation_model import ObservationModel
from memory.relational.models.prediction_probe_model import \
    PredictionProbeModel  # noqa: F401
from memory.relational.postgres_client import engine

Base.metadata.create_all(bind=engine)

print("Database schema initialized.")
