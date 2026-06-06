from sqlalchemy import text
from memory.relational.repositories.base_repository import BaseRepository
from memory.relational.models.prediction_probe_model import PredictionProbeModel
from memory.relational.database import SessionLocal

class PredictionRepository(BaseRepository):
    def save(self, probe, date, day_index, theory_id=None, reflection_id=None):
        """Persist a prediction probe with its context."""
        direction = probe.direction.value if hasattr(probe.direction, 'value') else probe.direction
        
        model = PredictionProbeModel(
            date=date,
            day_index=day_index,
            direction=direction,
            confidence=probe.confidence,
            tension=getattr(probe, 'tension', None),
            invalidation=getattr(probe, 'invalidation', None),
            theory_id=theory_id,
            reflection_id=reflection_id
        )
        return self._save(model)