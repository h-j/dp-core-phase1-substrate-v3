"""Instrumentation for structured theory lifecycle tracing.

Tracks theories from generation through persistence, retrieval, and consumption.
Measures structured cognition survival rate across the cognition pipeline.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class StructuredTheoryEvent:
    """Single event in structured theory lifecycle."""

    timestamp: str
    stage: str  # generation, persisted, retrieved, consumed, classified
    theory_id: str
    has_structured: bool
    event_data: Dict = field(default_factory=dict)


@dataclass
class StructuredTheoryMetrics:
    """Aggregate metrics for structured theory lifecycle."""

    generated_count: int = 0
    generated_with_structured: int = 0

    persisted_count: int = 0
    persisted_with_structured: int = 0

    retrieved_count: int = 0
    retrieved_with_structured: int = 0

    consumed_count: int = 0
    consumed_with_structured: int = 0

    classified_count: int = 0
    classified_theory_types: Dict[str, int] = field(
        default_factory=lambda: {
            "observation": 0,
            "hypothesis": 0,
            "conditional": 0,
            "falsifiable": 0,
            "unknown": 0,
        }
    )

    def survival_rate(self) -> float:
        """Calculate structured cognition survival rate."""
        if self.generated_with_structured == 0:
            return 0.0

        # Count theories that were generated with structured data
        # and successfully consumed with structured data
        if self.generated_count == 0:
            return 0.0

        return (self.consumed_with_structured / self.generated_with_structured) * 100.0

    def __str__(self) -> str:
        """Human-readable metrics summary."""
        lines = [
            "\n" + "=" * 70,
            "STRUCTURED COGNITION LIFECYCLE METRICS",
            "=" * 70,
            f"Generated (total):        {self.generated_count}",
            f"Generated (structured):   {self.generated_with_structured}",
            f"",
            f"Persisted (total):        {self.persisted_count}",
            f"Persisted (structured):   {self.persisted_with_structured}",
            f"",
            f"Retrieved (total):        {self.retrieved_count}",
            f"Retrieved (structured):   {self.retrieved_with_structured}",
            f"",
            f"Consumed (total):         {self.consumed_count}",
            f"Consumed (structured):    {self.consumed_with_structured}",
            f"",
            f"Classified (total):       {self.classified_count}",
            f"  - Observation:          {self.classified_theory_types.get('observation', 0)}",
            f"  - Hypothesis:           {self.classified_theory_types.get('hypothesis', 0)}",
            f"  - Conditional:          {self.classified_theory_types.get('conditional', 0)}",
            f"  - Falsifiable:          {self.classified_theory_types.get('falsifiable', 0)}",
            f"  - Unknown:              {self.classified_theory_types.get('unknown', 0)}",
            f"",
            f"STRUCTURED SURVIVAL RATE: {self.survival_rate():.1f}%",
            "=" * 70 + "\n",
        ]
        return "\n".join(lines)


class StructuredCognitionTracer:
    """Traces and instruments structured theory lifecycle."""

    def __init__(self):
        """Initialize tracer."""
        self.events: List[StructuredTheoryEvent] = []
        self.metrics = StructuredTheoryMetrics()
        self._theory_cache: Dict[str, Dict] = {}

    def trace_generation(self, theory_id: str, theory_obj) -> None:
        """Trace theory generation event."""
        has_structured = False
        structured_keys = []

        # Check if theory has structured data
        if hasattr(theory_obj, "summary"):
            try:
                if isinstance(theory_obj.summary, str):
                    parsed = json.loads(theory_obj.summary)
                    if isinstance(parsed, dict):
                        has_structured = True
                        structured_keys = list(parsed.keys())
            except (json.JSONDecodeError, TypeError):
                pass

        self.metrics.generated_count += 1
        if has_structured:
            self.metrics.generated_with_structured += 1

        event = StructuredTheoryEvent(
            timestamp=datetime.now().isoformat(),
            stage="generation",
            theory_id=theory_id,
            has_structured=has_structured,
            event_data={"structured_keys": structured_keys},
        )
        self.events.append(event)
        self._theory_cache[theory_id] = {
            "has_structured": has_structured,
            "generated": True,
        }

        status = "✓" if has_structured else "✗"
        print(
            f"[STRUCTURED] {status} Generated: {theory_id[:12]}... (structured={has_structured})"
        )

    def trace_persisted(self, theory_id: str, theory_model) -> None:
        """Trace theory persistence event."""
        has_structured = False

        if (
            hasattr(theory_model, "summary_structured")
            and theory_model.summary_structured
        ):
            has_structured = True

        self.metrics.persisted_count += 1
        if has_structured:
            self.metrics.persisted_with_structured += 1

        event = StructuredTheoryEvent(
            timestamp=datetime.now().isoformat(),
            stage="persisted",
            theory_id=theory_id,
            has_structured=has_structured,
            event_data={},
        )
        self.events.append(event)

        if theory_id in self._theory_cache:
            self._theory_cache[theory_id]["persisted"] = True
            self._theory_cache[theory_id]["persisted_with_structured"] = has_structured

        status = "✓" if has_structured else "✗"
        print(
            f"[STRUCTURED] {status} Persisted: {theory_id[:12]}... (structured={has_structured})"
        )

    def trace_retrieved(self, theory_id: str, theory_model) -> None:
        """Trace theory retrieval event."""
        has_structured = False

        if (
            hasattr(theory_model, "summary_structured")
            and theory_model.summary_structured
        ):
            has_structured = True

        self.metrics.retrieved_count += 1
        if has_structured:
            self.metrics.retrieved_with_structured += 1

        event = StructuredTheoryEvent(
            timestamp=datetime.now().isoformat(),
            stage="retrieved",
            theory_id=theory_id,
            has_structured=has_structured,
            event_data={},
        )
        self.events.append(event)

        if theory_id in self._theory_cache:
            self._theory_cache[theory_id]["retrieved"] = True
            self._theory_cache[theory_id]["retrieved_with_structured"] = has_structured

        status = "✓" if has_structured else "✗"
        print(
            f"[STRUCTURED] {status} Retrieved: {theory_id[:12]}... (structured={has_structured})"
        )

    def trace_consumed(
        self, theory_id: str, consumer_name: str, has_structured: bool
    ) -> None:
        """Trace theory consumption event."""
        self.metrics.consumed_count += 1
        if has_structured:
            self.metrics.consumed_with_structured += 1

        event = StructuredTheoryEvent(
            timestamp=datetime.now().isoformat(),
            stage="consumed",
            theory_id=theory_id,
            has_structured=has_structured,
            event_data={"consumer": consumer_name},
        )
        self.events.append(event)

        if theory_id in self._theory_cache:
            self._theory_cache[theory_id]["consumed"] = True
            self._theory_cache[theory_id]["consumed_by"] = consumer_name

        status = "✓" if has_structured else "✗"
        print(
            f"[STRUCTURED] {status} Consumed by {consumer_name}: {theory_id[:12]}... (structured={has_structured})"
        )

    def classify_theory(self, theory_id: str, theory_classification: str) -> None:
        """Classify theory type and record classification."""
        valid_types = [
            "observation",
            "hypothesis",
            "conditional",
            "falsifiable",
            "unknown",
        ]
        theory_type = (
            theory_classification.lower()
            if theory_classification.lower() in valid_types
            else "unknown"
        )

        self.metrics.classified_count += 1
        self.metrics.classified_theory_types[theory_type] += 1

        event = StructuredTheoryEvent(
            timestamp=datetime.now().isoformat(),
            stage="classified",
            theory_id=theory_id,
            has_structured=True,
            event_data={"classification": theory_type},
        )
        self.events.append(event)

        if theory_id in self._theory_cache:
            self._theory_cache[theory_id]["classification"] = theory_type

        print(f"[THEORY_QUALITY] Classified: {theory_id[:12]}... as {theory_type}")

    def get_metrics(self) -> StructuredTheoryMetrics:
        """Get aggregated metrics."""
        return self.metrics

    def print_summary(self) -> None:
        """Print lifecycle metrics summary."""
        print(str(self.metrics))

    def get_event_log(self) -> List[StructuredTheoryEvent]:
        """Get full event log."""
        return self.events.copy()


# Global tracer instance
_tracer_instance: Optional[StructuredCognitionTracer] = None


def get_tracer() -> StructuredCognitionTracer:
    """Get or create global tracer instance."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = StructuredCognitionTracer()
    return _tracer_instance


def reset_tracer() -> None:
    """Reset tracer (useful for testing)."""
    global _tracer_instance
    _tracer_instance = StructuredCognitionTracer()
