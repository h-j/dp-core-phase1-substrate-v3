from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.validation.validation_event import ValidationEvent
from cognition.confidence.confidence_evolution_engine import (
    ConfidenceEvolutionEngine
)
from cognition.contradiction.contradiction_detector import (
    ContradictionDetector
)

from flows.observation_flow.abstraction_flow import AbstractionFlow
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from flows.reflection_flow.reflection_flow import ReflectionFlow

from market.examples.sample_nifty_observations import (
    SAMPLE_NIFTY_OBSERVATIONS
)
from market.regime.market_regime_classifier import MarketRegimeClassifier

from memory.lineage.historical_cognition_service import (
    HistoricalCognitionService
)
from memory.reflection.reflective_memory_synthesizer import (
    ReflectiveMemorySynthesizer
)
from memory.market.historical_market_memory_service import (
    HistoricalMarketMemoryService
)
from memory.market.market_observation_repository import (
    MarketObservationRepository
)

from memory.relational.repositories.observation_repository import (
    ObservationRepository
)

from memory.relational.repositories.abstraction_repository import (
    AbstractionRepository
)

from memory.relational.repositories.theory_repository import (
    TheoryRepository
)

from memory.relational.repositories.validation_repository import (
    ValidationRepository
)

from memory.relational.repositories.reflection_repository import (
    ReflectionRepository
)

from memory.relational.repositories.confidence_repository import (
    ConfidenceRepository
)

from memory.relational.repositories.reflective_memory_repository import (
    ReflectiveMemoryRepository
)


def main():

    observation_repository = ObservationRepository()

    abstraction_repository = AbstractionRepository()

    theory_repository = TheoryRepository()

    validation_repository = ValidationRepository()

    reflection_repository = ReflectionRepository()

    confidence_repository = ConfidenceRepository()

    reflective_memory_repository = ReflectiveMemoryRepository()

    market_observation_repository = MarketObservationRepository()

    market_regime_classifier = MarketRegimeClassifier()

    historical_market_memory_service = HistoricalMarketMemoryService(
        market_observation_repository=market_observation_repository
    )

    contradiction_detector = ContradictionDetector()

    confidence_evolution_engine = ConfidenceEvolutionEngine()

    reflective_memory_synthesizer = ReflectiveMemorySynthesizer()

    historical_cognition_service = HistoricalCognitionService(
        theory_repository=theory_repository,
        reflection_repository=reflection_repository,
        validation_repository=validation_repository,
        reflective_memory_repository=reflective_memory_repository
    )

    print("\n===================================")
    print("DP PERSISTENT REFLECTIVE COGNITION")
    print("===================================\n")

    sample_index = (
        market_observation_repository.count()
        % len(SAMPLE_NIFTY_OBSERVATIONS)
    )

    market_observation = SAMPLE_NIFTY_OBSERVATIONS[sample_index]

    market_regime = market_regime_classifier.classify(
        market_observation
    )

    market_observation_repository.save(market_observation)

    print("MARKET OBSERVATION SAVED")
    print(f"OBSERVATION: {market_observation.observation_text}")
    print(f"REGIME: {market_regime}\n")

    market_memory_context = historical_market_memory_service.build_context()

    print("MARKET MEMORY RETRIEVED\n")

    observation = ObservationEvent(
        source_type="market",
        raw_content=(
            f"Market: {market_observation.market_name}\n"
            f"Observation: {market_observation.observation_text}\n"
            f"Trend state: {market_observation.trend_state}\n"
            f"Volatility state: {market_observation.volatility_state}\n"
            f"Liquidity state: {market_observation.liquidity_state}\n"
            f"Breadth state: {market_observation.breadth_state}\n"
            f"Macro sentiment: {market_observation.macro_sentiment}\n"
            "Contradiction markers: "
            f"{', '.join(market_observation.contradiction_markers)}\n"
            f"Classified regime: {market_regime}"
        )
    )

    observation_repository.save(observation)

    print("OBSERVATION SAVED\n")

    abstraction_flow = AbstractionFlow()

    abstraction = abstraction_flow.process(
        observation
    )

    abstraction_repository.save(abstraction)

    print("ABSTRACTION SAVED\n")

    historical_context = historical_cognition_service.build_context()

    print("HISTORICAL COGNITION RETRIEVED\n")

    recent_reflective_memories = reflective_memory_repository.list_recent(
        limit=1
    )

    reflective_memory_summary = ""

    if recent_reflective_memories:
        reflective_memory_summary = (
            recent_reflective_memories[0].cognition_trajectory_summary
        )

    theory_flow = TheoryGenerationFlow()

    theory = theory_flow.process(
        abstraction,
        historical_context=historical_context,
        market_memory_context=market_memory_context,
        current_market_observation=observation.raw_content,
        reflective_memory_summary=reflective_memory_summary
    )

    recent_confidence_states = confidence_repository.list_recent(limit=1)

    if recent_confidence_states:
        latest_confidence_state = recent_confidence_states[0]
        theory.confidence_state.empirical_confidence = (
            latest_confidence_state.empirical_confidence
        )
        theory.confidence_state.regime_confidence = (
            latest_confidence_state.regime_confidence
        )
        theory.confidence_state.reflection_confidence = (
            latest_confidence_state.reflection_confidence
        )
        theory.confidence_state.theoretical_coherence = (
            latest_confidence_state.theoretical_coherence
        )
        theory.confidence_state.contradiction_pressure = (
            latest_confidence_state.contradiction_pressure
        )

        print("CONFIDENCE BASELINE RETRIEVED\n")

    theory_repository.save(theory)

    print("THEORY SAVED\n")

    validation = ValidationEvent(
        theory_id=theory.id,
        validation_summary=(
            "NIFTY grounding observation checked against current "
            "market structure and contradiction markers."
        ),
        observed_behavior=(
            market_observation.observation_text
        ),
        expected_behavior=(
            "Market-grounded theory should account for trend, "
            "breadth, liquidity, volatility, and contradiction markers."
        )
    )

    validation_repository.save(validation)

    print("VALIDATION SAVED\n")

    reflection_flow = ReflectionFlow()

    reflection = reflection_flow.process(
        theory,
        validation
    )

    reflection_repository.save(reflection)

    print("REFLECTION SAVED\n")

    recent_theories = theory_repository.list_recent()

    recent_validations = validation_repository.list_recent()

    recent_reflections = reflection_repository.list_recent()

    contradiction_result = contradiction_detector.detect(
        current_theory=theory,
        historical_theories=recent_theories,
        validations=recent_validations,
        reflections=recent_reflections
    )

    print("CONTRADICTION PRESSURE EVALUATED")
    print(f"SCORE: {contradiction_result['score']}")
    print(f"SUMMARY: {contradiction_result['summary']}\n")

    evolved_confidence_state = confidence_evolution_engine.evolve(
        confidence_state=theory.confidence_state,
        validation=validation,
        reflection=reflection,
        contradiction_result=contradiction_result,
        recent_validations=recent_validations
    )

    confidence_repository.save(evolved_confidence_state)

    print("CONFIDENCE STATE UPDATED")
    print(
        "EMPIRICAL: "
        f"{evolved_confidence_state.empirical_confidence}"
    )
    print(
        "REGIME: "
        f"{evolved_confidence_state.regime_confidence}"
    )
    print(
        "REFLECTION: "
        f"{evolved_confidence_state.reflection_confidence}"
    )
    print(
        "COHERENCE: "
        f"{evolved_confidence_state.theoretical_coherence}"
    )
    print(
        "CONTRADICTION PRESSURE: "
        f"{evolved_confidence_state.contradiction_pressure}\n"
    )

    recent_confidence_states = confidence_repository.list_recent()

    reflective_memory_state = reflective_memory_synthesizer.synthesize(
        theories=recent_theories,
        reflections=recent_reflections,
        validations=recent_validations,
        confidence_states=recent_confidence_states,
        contradiction_result=contradiction_result,
        market_observations=(
            market_observation_repository.list_recent(limit=10)
        )
    )

    reflective_memory_repository.save(reflective_memory_state)

    print("REFLECTIVE MEMORY SYNTHESIZED")
    print(
        "TRAJECTORY: "
        f"{reflective_memory_state.cognition_trajectory_summary}"
    )
    print(
        "HOTSPOTS: "
        f"{'; '.join(reflective_memory_state.contradiction_hotspots)}\n"
    )

    print("===================================")
    print("PERSISTENT COGNITION COMPLETE")
    print("===================================\n")


if __name__ == "__main__":

    main()
