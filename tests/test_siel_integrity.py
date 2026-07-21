import pytest
from telemetry.siel.certification import CertificationLevel, ReportCertification
from telemetry.siel.validator import ScientificIntegrityValidator, ScientificIntegrityError
from telemetry.siel.rules import StoryTheoryCountSyncRule, TimelineDaySyncRule, ExecutionHashSyncRule


def test_siel_certification_gold_on_valid_report():
    report_data = {
        "days": 5,
        "execution_hash": "a1b2c3d4e5f6",
        "story_summary": "During this period, DP generated 0 experiences, evolved 3 theories, extracted 5 lessons...",
        "timeline": [{}, {}, {}, {}, {}],
        "compilation_metrics": {"theories_generated": 3},
        "eef_dashboard": {"composite_scores": {"learning_score": 0.45}},
    }
    manifest_data = {"execution_hash": "a1b2c3d4e5f6"}

    validator = ScientificIntegrityValidator()
    cert = validator.validate(report_data, manifest_data)

    assert cert.level == CertificationLevel.CERTIFIED_GOLD
    assert cert.integrity_score == 100.0
    assert cert.failed_rules_count == 0
    assert cert.critical_failures_count == 0


def test_siel_certification_rejected_on_theory_count_mismatch():
    report_data = {
        "days": 5,
        "execution_hash": "a1b2c3d4e5f6",
        "story_summary": "During this period, DP generated 0 experiences, evolved 0 theories, extracted 5 lessons...",
        "timeline": [{}, {}, {}, {}, {}],
        "compilation_metrics": {"theories_generated": 3},
    }
    manifest_data = {"execution_hash": "a1b2c3d4e5f6"}

    validator = ScientificIntegrityValidator()
    cert = validator.validate(report_data, manifest_data)

    assert cert.level == CertificationLevel.INVALID_REJECTED
    assert cert.critical_failures_count > 0
    assert cert.failed_rules_count >= 1
    assert any("SIEL-001" in detail["rule_id"] for detail in cert.details if not detail["passed"])


def test_siel_strict_mode_raises_exception():
    report_data = {
        "days": 5,
        "execution_hash": "a1b2c3d4e5f6",
        "story_summary": "During this period, DP generated 0 experiences, evolved 0 theories...",
        "timeline": [{}],  # Mismatch: 1 entry for 5 days
        "compilation_metrics": {"theories_generated": 3},
    }

    validator = ScientificIntegrityValidator()
    with pytest.raises(ScientificIntegrityError):
        validator.validate(report_data, strict_mode=True)
