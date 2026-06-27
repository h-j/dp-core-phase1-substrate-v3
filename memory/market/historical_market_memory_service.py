from memory.market.market_observation_repository import \
    MarketObservationRepository


class HistoricalMarketMemoryService:

    def __init__(self, market_observation_repository=None):

        self.market_observation_repository = (
            market_observation_repository or MarketObservationRepository()
        )

    def build_context(self, limit: int = 10) -> str:

        observations = self.market_observation_repository.list_recent(limit=limit)

        if not observations:
            return "RECENT MARKET MEMORY:\n\n* None recorded yet."

        lines = ["RECENT MARKET MEMORY:"]

        for observation in observations:
            lines.append(f"* {observation.observation_text}")

            if observation.contradiction_markers:
                lines.append(
                    "  Contradictions: " + "; ".join(observation.contradiction_markers)
                )

        return "\n".join(lines)
