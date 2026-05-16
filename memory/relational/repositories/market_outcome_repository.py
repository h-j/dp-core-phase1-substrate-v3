import json

from market.schemas.market_outcome import MarketOutcome
from memory.relational.models.market_outcome_model import MarketOutcomeModel
from memory.relational.postgres_client import SessionLocal


class MarketOutcomeRepository:
    """Repository for persisting market outcomes."""

    def save(self, market_outcome: MarketOutcome):
        """Save a market outcome to PostgreSQL."""

        contradictions_json = json.dumps(
            market_outcome.outcome_contradictions
        )

        with SessionLocal() as session:
            model = MarketOutcomeModel(
                id=market_outcome.id,
                created_at=market_outcome.created_at,
                market_name=market_outcome.market_name,
                related_observation_id=market_outcome.related_observation_id,
                outcome_summary=market_outcome.outcome_summary,
                realized_trend=market_outcome.realized_trend,
                realized_volatility=market_outcome.realized_volatility,
                realized_breadth=market_outcome.realized_breadth,
                realized_liquidity=market_outcome.realized_liquidity,
                outcome_contradictions=contradictions_json,
                outcome_confidence=market_outcome.outcome_confidence
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "market_outcome_id": market_outcome.id
        }

    def list_recent(self, limit: int = 20):
        """Retrieve recent market outcomes."""

        with SessionLocal() as session:
            models = (
                session.query(MarketOutcomeModel)
                .order_by(MarketOutcomeModel.created_at.desc())
                .limit(limit)
                .all()
            )

            outcomes = []
            for model in models:
                contradictions = json.loads(
                    model.outcome_contradictions or "[]"
                )
                
                outcome = MarketOutcome(
                    id=model.id,
                    created_at=model.created_at,
                    market_name=model.market_name,
                    related_observation_id=model.related_observation_id,
                    outcome_summary=model.outcome_summary,
                    realized_trend=model.realized_trend,
                    realized_volatility=model.realized_volatility,
                    realized_breadth=model.realized_breadth,
                    realized_liquidity=model.realized_liquidity,
                    outcome_contradictions=contradictions,
                    outcome_confidence=model.outcome_confidence
                )
                outcomes.append(outcome)

            return outcomes
