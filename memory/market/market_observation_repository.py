from market.schemas.market_observation import MarketObservation
from memory.market.market_observation_model import MarketObservationModel
from memory.relational.postgres_client import SessionLocal


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
            observation_source=model.observation_source
        )

    def _serialize(self, values: list[str]) -> str:

        return "\n".join(values)

    def _deserialize(self, value: str | None) -> list[str]:

        if not value:
            return []

        return [
            item
            for item in value.splitlines()
            if item
        ]
