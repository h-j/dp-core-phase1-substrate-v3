from market.schemas.market_observation import MarketObservation
from memory.market.market_observation_model import MarketObservationModel
from memory.relational.postgres_client import SessionLocal
from typing import List, Union


class MarketObservationRepository:

    def save(self, market_observation):

        with SessionLocal() as session:
            model = MarketObservationModel(
                id=market_observation.id,
                created_at=market_observation.created_at,
                market_name=market_observation.market_name,
                observation_text=market_observation.observation_text,
                trend_state=market_observation.trend_state,
                volatility_state=market_observation.volatility_state,
                liquidity_state=market_observation.liquidity_state,
                breadth_state=market_observation.breadth_state,
                macro_sentiment=market_observation.macro_sentiment,
                contradiction_markers=self._serialize(
                    market_observation.contradiction_markers
                ),
                descriptors=self._serialize(
                    market_observation.descriptors
                ),
                body_pct=market_observation.body_pct,
                upper_wick_pct=market_observation.upper_wick_pct,
                lower_wick_pct=market_observation.lower_wick_pct,
                close_position_pct=market_observation.close_position_pct,
                open_position_pct=market_observation.open_position_pct,
                candle_type=market_observation.candle_type,
                participation_strength=market_observation.participation_strength,
                participation_confirmation=market_observation.participation_confirmation,
                observation_source=market_observation.observation_source
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "market_observation_id": market_observation.id
        }

    def list_recent(self, limit: int = 10):

        with SessionLocal() as session:
            models = (
                session.query(MarketObservationModel)
                .order_by(MarketObservationModel.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                self._to_schema(model)
                for model in models
            ]

    def count(self) -> int:

        with SessionLocal() as session:
            return session.query(MarketObservationModel).count()

    def _to_schema(self, model):

        return MarketObservation(
            id=model.id,
            created_at=model.created_at,
            market_name=model.market_name,
            observation_text=model.observation_text,
            trend_state=model.trend_state,
            volatility_state=model.volatility_state,
            liquidity_state=model.liquidity_state,
            breadth_state=model.breadth_state,
            macro_sentiment=model.macro_sentiment,
            contradiction_markers=self._deserialize(
                model.contradiction_markers
            ),
            descriptors=self._deserialize(
                model.descriptors
            ),
            body_pct=model.body_pct or 0.0,
            upper_wick_pct=model.upper_wick_pct or 0.0,
            lower_wick_pct=model.lower_wick_pct or 0.0,
            close_position_pct=model.close_position_pct or 0.0,
            open_position_pct=model.open_position_pct or 0.0,
            candle_type=model.candle_type or "neutral",
            participation_strength=model.participation_strength or "normal",
            participation_confirmation=model.participation_confirmation or "normal",
            observation_source=model.observation_source
        )

    def _serialize(self, values: List[str]) -> str:

        return "\n".join(values)

    def _deserialize(self, value: Union[str, None]) -> List[str]:

        if not value:
            return []

        return [
            item
            for item in value.splitlines()
            if item
        ]
