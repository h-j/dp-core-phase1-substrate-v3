import json
from memory.relational.repositories.base_repository import BaseRepository
from memory.relational.models.transition_pressure_model import TransitionPressureModel

class TransitionPressureRepository(BaseRepository):
    def save(self, pressure, date, day_index):
        """Persist transition pressure state."""
        # v1.4 Adjustment: Serialize drivers to string for Text column
        drivers = pressure.get('drivers', []) if isinstance(pressure, dict) else getattr(pressure, 'drivers', [])
        drivers_json = json.dumps(drivers) if isinstance(drivers, list) else str(drivers)
        
        model = TransitionPressureModel(
            date=date,
            day_index=day_index,
            direction_bias=pressure.direction_bias,
            pressure_score=pressure.pressure_score,
            stability_score=pressure.stability_score,
            breakout_risk=pressure.breakout_risk,
            drivers_json=drivers_json
        )
        return self._save(model)