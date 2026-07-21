import uuid
from typing import Dict, Any, List, Optional
from telemetry.siel.certification import CertificationLevel, ReportCertification
from telemetry.siel.rules import InvariantRule, RuleSeverity, RuleResult, get_default_invariant_rules


class ScientificIntegrityError(Exception):
    """Raised when critical scientific invariants fail during report validation."""
    pass


class ScientificIntegrityValidator:
    """
    Pure validation gate for Replay Report models before persistence or rendering.
    """

    SEVERITY_WEIGHTS = {
        RuleSeverity.CRITICAL: 40.0,
        RuleSeverity.HIGH: 20.0,
        RuleSeverity.MEDIUM: 10.0,
        RuleSeverity.INFO: 2.0,
    }

    def __init__(self, rules: Optional[List[InvariantRule]] = None):
        self.rules = rules if rules is not None else get_default_invariant_rules()

    def validate(
        self,
        report_data: Dict[str, Any],
        manifest_data: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
    ) -> ReportCertification:
        """
        Evaluates report data against registered rules and computes certification.
        """
        results: List[RuleResult] = []
        passed_count = 0
        failed_count = 0
        critical_failed_count = 0

        total_possible_weight = 0.0
        failed_weight = 0.0

        remediations: List[str] = []

        for rule in self.rules:
            weight = self.SEVERITY_WEIGHTS.get(rule.severity, 10.0)
            total_possible_weight += weight

            res = rule.evaluate(report_data, manifest_data)
            results.append(res)

            if res.passed:
                passed_count += 1
            else:
                failed_count += 1
                failed_weight += weight
                if rule.severity == RuleSeverity.CRITICAL:
                    critical_failed_count += 1
                if res.recommended_fix and res.recommended_fix not in remediations:
                    remediations.append(res.recommended_fix)

        # Compute Integrity Score (0.0 to 100.0)
        if total_possible_weight > 0:
            score = max(0.0, round(100.0 * (1.0 - (failed_weight / total_possible_weight)), 2))
        else:
            score = 100.0

        # Determine Certification Level
        if critical_failed_count > 0 or score < 75.0:
            level = CertificationLevel.INVALID_REJECTED
        elif score >= 100.0 and critical_failed_count == 0:
            level = CertificationLevel.CERTIFIED_GOLD
        elif score >= 90.0:
            level = CertificationLevel.CERTIFIED_VALID
        else:
            level = CertificationLevel.WARNING_PROVISIONAL

        cert = ReportCertification(
            certificate_id=f"CERT-{uuid.uuid4().hex[:8].upper()}",
            level=level,
            integrity_score=score,
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            critical_failures_count=critical_failed_count,
            details=[r.model_dump() for r in results],
            remediation_recommendations=remediations,
        )

        if strict_mode and level == CertificationLevel.INVALID_REJECTED:
            failed_msgs = [r.error_message for r in results if not r.passed and r.error_message]
            raise ScientificIntegrityError(
                f"Scientific Integrity Gate failed with score {score}%! "
                f"Critical Failures: {critical_failed_count}. Issues: {failed_msgs}"
            )

        return cert
