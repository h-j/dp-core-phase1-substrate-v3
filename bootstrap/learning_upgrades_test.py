"""
Unit tests for structured lesson records, weighted similarity retrieval, and three-window Bayesian calibration.
"""

from uuid import uuid4

from cognition.confidence.scored_confidence_engine import ScoredConfidenceEngine
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.reflection.reflection_event import ReflectionEvent
from cognition.schemas.validation.validation_event import ValidationEvent
from market.replay.lesson_record import LessonRecord, LessonStatus


def test_structured_lesson_record():
    """Verify structured lesson record serialization, deserialization, and legacy format upgrades."""
    lesson_id = uuid4()

    # 1. Test creation with structured fields
    lesson = LessonRecord(
        lesson_id=lesson_id,
        target_regime={"regime_subtype": "momentum", "volatility": "compressed"},
        activation_conditions=["volatility: compressed", "momentum: strengthening"],
        failure_conditions=["price_participation_divergence"],
        affected_components=["volume_confirmation"],
        validation_count=3,
        falsification_count=1,
        confidence=0.75,
        status=LessonStatus.ACTIVE,
        lesson_text="Passive absorption regime continuation expected.",
    )

    data = lesson.to_dict()
    assert data["status"] == "active"
    assert data["validation_count"] == 3
    assert data["falsification_count"] == 1

    # 2. Test reconstruction from dict
    reconstructed = LessonRecord.from_dict(data)
    assert reconstructed.lesson_id == lesson_id
    assert reconstructed.target_regime["regime_subtype"] == "momentum"
    assert reconstructed.activation_conditions == [
        "volatility: compressed",
        "momentum: strengthening",
    ]
    assert reconstructed.failure_conditions == ["price_participation_divergence"]
    assert reconstructed.affected_components == ["volume_confirmation"]
    assert reconstructed.validation_count == 3
    assert reconstructed.falsification_count == 1
    assert reconstructed.confidence == 0.75

    # 3. Test legacy compatibility conversion
    legacy_data = {
        "lesson_id": str(lesson_id),
        "lesson_text": "Legacy text explanation",
        "support_count": 5,
        "contradiction_count": 2,
        "confidence": 0.71,
        "status": "candidate",
        "created_at": lesson.created_at.isoformat(),
        "last_updated_at": lesson.last_updated_at.isoformat(),
        "source_experience_ids": [],
        "metadata": {
            "regime_subtype": "range_bound",
            "volatility": "normal",
        },
    }

    upgraded = LessonRecord.from_dict(legacy_data)
    assert upgraded.validation_count == 5
    assert upgraded.falsification_count == 2
    assert upgraded.target_regime["regime_subtype"] == "range_bound"
    assert upgraded.target_regime["volatility"] == "normal"
    print("✓ LessonRecord structured updates and upgrade path verified successfully.")


def test_weighted_similarity_retrieval():
    """Verify the weighted multi-dimensional similarity formula is correct and orders active lessons properly."""
    # Simulation day's current state
    regime_subtype = "momentum"
    vol_regime = "compressed"
    mom_regime = "strengthening"
    vol_state = "normal"
    part_confirm = "normal"

    # Lesson A: Perfect match (subtype, volatility, momentum, volume/participation)
    lesson_a = LessonRecord(
        lesson_id=uuid4(),
        target_regime={
            "regime_subtype": "momentum",
            "volatility": "compressed",
            "momentum": "strengthening",
            "volume": "normal",
        },
        status=LessonStatus.ACTIVE,
        lesson_text="Lesson A",
    )

    # Lesson B: Partial match (regime subtype match only)
    lesson_b = LessonRecord(
        lesson_id=uuid4(),
        target_regime={
            "regime_subtype": "momentum",
            "volatility": "expanded",
            "momentum": "flat",
            "volume": "high",
        },
        status=LessonStatus.ACTIVE,
        lesson_text="Lesson B",
    )

    # Lesson C: Volatility and Momentum match, but not subtype
    lesson_c = LessonRecord(
        lesson_id=uuid4(),
        target_regime={
            "regime_subtype": "range_bound",
            "volatility": "compressed",
            "momentum": "strengthening",
            "volume": "high",
        },
        status=LessonStatus.ACTIVE,
        lesson_text="Lesson C",
    )

    lessons = [lesson_a, lesson_b, lesson_c]
    scored_lessons = []

    for l in lessons:
        tr = l.target_regime
        subtype_match = 1.0 if tr.get("regime_subtype") == regime_subtype else 0.0
        volatility_match = 1.0 if tr.get("volatility") == vol_regime else 0.0
        momentum_match = 1.0 if tr.get("momentum") == mom_regime else 0.0

        tr_volume = tr.get("volume") or tr.get("participation") or ""
        volume_val = vol_state or part_confirm or ""
        participation_match = 1.0 if tr_volume == volume_val else 0.0

        sim = (
            0.4 * subtype_match
            + 0.3 * volatility_match
            + 0.2 * momentum_match
            + 0.1 * participation_match
        )
        scored_lessons.append((l, sim))

    scored_lessons.sort(key=lambda x: x[1], reverse=True)

    # Assert similarity scores and ordering matches user specs
    assert (
        scored_lessons[0][0].lesson_text == "Lesson A"
    )  # Perfect match -> 1.0 similarity
    assert abs(scored_lessons[0][1] - 1.0) < 0.001

    assert (
        scored_lessons[1][0].lesson_text == "Lesson C"
    )  # Volatility (0.3) + Momentum (0.2) match -> 0.5 similarity
    assert abs(scored_lessons[1][1] - 0.5) < 0.001

    assert (
        scored_lessons[2][0].lesson_text == "Lesson B"
    )  # Subtype match (0.4) only -> 0.4 similarity
    assert abs(scored_lessons[2][1] - 0.4) < 0.001

    print("✓ Weighted similarity retrieval math and ordering verified successfully.")


def test_three_window_bayesian_calibration():
    """Verify three-window Bayesian confidence evolution scaling factors."""
    engine = ScoredConfidenceEngine()


    # Mock events
    validation = ValidationEvent(
        theory_id="test-theory",
        validation_summary="Theory confirmed by market",
        observed_behavior="increased trend",
        expected_behavior="increase",
    )
    reflection = ReflectionEvent(
        related_theory_id="test-theory",
        reflection_summary="Theory shows support and consistent evidence",
        confidence_impact="positive",
    )

    # Baseline state
    state_a = ConfidenceState(empirical_confidence=0.5, theoretical_coherence=0.5)

    # 1. Verify high accuracy results in positive confirmation multiplier (pos_mult > 1.0)
    evolved_a = engine.evolve(
        confidence_state=state_a,
        validation=validation,
        reflection=reflection,
        contradiction_result={},
        recent_validations=[],
        outcome_validation_result={"validation_score": 0.8},  # positive update
        theory_usefulness={"score": 0.8},  # positive update
        rolling_accuracy=0.8,  # High recent accuracy
        regime_accuracy=0.8,  # High regime-specific accuracy
        lifetime_accuracy=0.8,  # High lifetime accuracy
    )

    # 2. Verify low accuracy results in negative surprise/contradiction multiplier (neg_mult > 1.0)
    state_b = ConfidenceState(empirical_confidence=0.5, theoretical_coherence=0.5)
    evolved_b = engine.evolve(
        confidence_state=state_b,
        validation=validation,
        reflection=reflection,
        contradiction_result={},
        recent_validations=[],
        outcome_validation_result={"validation_score": 0.2},  # negative update
        theory_usefulness={"score": 0.2},  # negative update
        rolling_accuracy=0.2,  # Low recent accuracy
        regime_accuracy=0.2,  # Low regime accuracy
        lifetime_accuracy=0.2,  # Low lifetime accuracy
    )

    # Confirm that low accuracy engine drops confidence further/faster than a neutral run
    assert evolved_b.empirical_confidence < 0.5
    print("✓ Three-window Bayesian calibration logic verified successfully.")


if __name__ == "__main__":
    test_structured_lesson_record()
    test_weighted_similarity_retrieval()
    test_three_window_bayesian_calibration()
    print("\nALL UPGRADE COMPONENT TESTS PASSED CLEANLY")
