from memory.relational.repositories.base_repository import BaseRepository
from memory.relational.models.prediction_result_model import PredictionResultModel

class PredictionResultRepository(BaseRepository):
    def save(self, result, date, day_index, prediction_id):
        """Persist the scoring result of a prior prediction."""
        model = PredictionResultModel(
            date=date,
            day_index=day_index,
            prediction_id=prediction_id,
            prior_direction=result.prior_direction,
            actual_direction=result.actual_direction,
            direction_score=result.direction_score,
            partial_score=getattr(result, 'partial_score', 0.0),
            invalidation_triggered=result.invalidation_triggered
        )
        return self._save(model)