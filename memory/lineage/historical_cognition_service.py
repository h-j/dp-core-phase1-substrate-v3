from memory.relational.repositories.reflection_repository import ReflectionRepository
from memory.relational.repositories.reflective_memory_repository import (
    ReflectiveMemoryRepository
)
from memory.relational.repositories.theory_repository import TheoryRepository
from memory.relational.repositories.validation_repository import ValidationRepository


class HistoricalCognitionService:

    def __init__(
        self,
        theory_repository=None,
        reflection_repository=None,
        validation_repository=None,
        reflective_memory_repository=None
    ):

        self.theory_repository = theory_repository or TheoryRepository()
        self.reflection_repository = (
            reflection_repository or ReflectionRepository()
        )
        self.validation_repository = (
            validation_repository or ValidationRepository()
        )
        self.reflective_memory_repository = (
            reflective_memory_repository or ReflectiveMemoryRepository()
        )

    def build_context(self, limit: int = 5) -> str:

        theories = self.theory_repository.list_recent(limit=limit)
        reflections = self.reflection_repository.list_recent(limit=limit)
        validations = self.validation_repository.list_recent(limit=limit)
        reflective_memories = (
            self.reflective_memory_repository.list_recent(limit=limit)
        )

        sections = [
            self._format_reflective_memory_section(reflective_memories),
            self._format_section(
                "PREVIOUS THEORIES",
                [theory.summary for theory in theories]
            ),
            self._format_section(
                "PREVIOUS REFLECTIONS",
                [
                    reflection.reflection_summary
                    for reflection in reflections
                ]
            ),
            self._format_section(
                "PREVIOUS VALIDATIONS",
                [
                    validation.validation_summary
                    for validation in validations
                ]
            )
        ]

        return "\n\n".join(sections)

    def _format_reflective_memory_section(self, reflective_memories):

        if not reflective_memories:
            return "RECENT REFLECTIVE MEMORY:\n\n* None recorded yet."

        lines = ["RECENT REFLECTIVE MEMORY:"]

        for memory in reflective_memories:
            lines.append(
                f"* Trajectory: {memory.cognition_trajectory_summary}"
            )

            if memory.persistent_uncertainties:
                lines.append(
                    "* Persistent uncertainties: "
                    + "; ".join(memory.persistent_uncertainties[:3])
                )

            if memory.contradiction_hotspots:
                lines.append(
                    "* Contradiction hotspots: "
                    + "; ".join(memory.contradiction_hotspots[:3])
                )

        return "\n".join(lines)

    def _format_section(self, title: str, values: list[str]) -> str:

        if not values:
            return f"{title}:\n\n* None recorded yet."

        lines = [f"{title}:"]

        for value in values:
            lines.append(f"* {value}")

        return "\n".join(lines)
