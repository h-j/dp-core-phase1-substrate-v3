from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.validation.validation_event import ValidationEvent

from flows.observation_flow.abstraction_flow import AbstractionFlow
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from flows.reflection_flow.reflection_flow import ReflectionFlow

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


def main():

    observation_repository = ObservationRepository()

    abstraction_repository = AbstractionRepository()

    theory_repository = TheoryRepository()

    validation_repository = ValidationRepository()

    reflection_repository = ReflectionRepository()

    print("\n===================================")
    print("DP PERSISTENT REFLECTIVE COGNITION")
    print("===================================\n")

    observation = ObservationEvent(
        source_type="manual",
        raw_content=(
            "Momentum strategies strengthen "
            "during expanding liquidity regimes "
            "with strong market participation."
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

    theory_flow = TheoryGenerationFlow()

    theory = theory_flow.process(
        abstraction
    )

    theory_repository.save(theory)

    print("THEORY SAVED\n")

    validation = ValidationEvent(
        theory_id=theory.id,
        validation_summary=(
            "Liquidity expansion historically "
            "showed stronger trend persistence."
        ),
        observed_behavior="Momentum persistence increased.",
        expected_behavior=(
            "Momentum should strengthen "
            "during liquidity expansion."
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

    print("===================================")
    print("PERSISTENT COGNITION COMPLETE")
    print("===================================\n")


if __name__ == "__main__":

    main()
