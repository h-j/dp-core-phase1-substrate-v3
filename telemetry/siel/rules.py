from enum import Enum
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    INFO = "INFO"


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    passed: bool
    error_message: Optional[str] = None
    recommended_fix: Optional[str] = None


class InvariantRule:
    """Base class for all SIEL scientific invariant rules."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: RuleSeverity,
        recommended_fix: str,
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity
        self.recommended_fix = recommended_fix

    def evaluate(self, report_data: Dict[str, Any], manifest_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        raise NotImplementedError


class StoryTheoryCountSyncRule(InvariantRule):
    def __init__(self):
        super().__init__(
            rule_id="SIEL-001",
            name="STORY_THEORY_COUNT_SYNC",
            description="Asserts that theory count mentioned in narrative story summary equals theories generated in compilation metrics.",
            severity=RuleSeverity.CRITICAL,
            recommended_fix="Update story_summary builder to consume compilation_metrics.theories_generated directly.",
        )

    def evaluate(self, report_data: Dict[str, Any], manifest_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        story = report_data.get("story_summary", "")
        compilation = report_data.get("compilation_metrics", {})
        comp_theories = compilation.get("theories_generated", 0)

        # Extract number of theories from story summary text: e.g., "evolved X theories"
        match = re.search(r"evolved\s+(\d+)\s+theories", story, re.IGNORECASE)
        if match:
            story_theories = int(match.group(1))
            if story_theories != comp_theories:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    passed=False,
                    error_message=f"Story summary claims {story_theories} theories evolved, but compilation_metrics reports {comp_theories}.",
                    recommended_fix=self.recommended_fix,
                )

        return RuleResult(rule_id=self.rule_id, rule_name=self.name, severity=self.severity, passed=True)


class TimelineDaySyncRule(InvariantRule):
    def __init__(self):
        super().__init__(
            rule_id="SIEL-002",
            name="TIMELINE_DAY_SYNC",
            description="Asserts that timeline entry count equals total replay days.",
            severity=RuleSeverity.CRITICAL,
            recommended_fix="Ensure ReplayAnalysisEngine.record_day() appends an entry for every step t in the replay loop.",
        )

    def evaluate(self, report_data: Dict[str, Any], manifest_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        timeline = report_data.get("timeline", [])
        days = report_data.get("days", 0)

        if days > 0 and len(timeline) != days:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                error_message=f"Timeline count ({len(timeline)}) does not equal total replay days ({days}).",
                recommended_fix=self.recommended_fix,
            )

        return RuleResult(rule_id=self.rule_id, rule_name=self.name, severity=self.severity, passed=True)


class ExecutionHashSyncRule(InvariantRule):
    def __init__(self):
        super().__init__(
            rule_id="SIEL-003",
            name="EXECUTION_HASH_SYNC",
            description="Asserts that execution hash in report metadata matches execution hash in replay_manifest.json.",
            severity=RuleSeverity.CRITICAL,
            recommended_fix="Bind executor.execution_hash during initialization and write to metadata and manifest simultaneously.",
        )

    def evaluate(self, report_data: Dict[str, Any], manifest_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        report_hash = report_data.get("execution_hash", "unknown")
        manifest_hash = manifest_data.get("execution_hash", "unknown") if manifest_data else "unknown"

        if report_hash == "unknown" and manifest_hash != "unknown":
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                error_message=f"Report execution hash is 'unknown', but manifest hash is '{manifest_hash}'.",
                recommended_fix=self.recommended_fix,
            )

        if manifest_hash != "unknown" and report_hash != manifest_hash:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                error_message=f"Report execution hash ({report_hash}) disagrees with manifest hash ({manifest_hash}).",
                recommended_fix=self.recommended_fix,
            )

        return RuleResult(rule_id=self.rule_id, rule_name=self.name, severity=self.severity, passed=True)


class EEFLearningScoreHarmonyRule(InvariantRule):
    def __init__(self):
        super().__init__(
            rule_id="SIEL-007",
            name="LEARNING_SCORE_HARMONY",
            description="Asserts that composite learning score is within bounds [0.0, 1.0] and present when EEF metrics exist.",
            severity=RuleSeverity.CRITICAL,
            recommended_fix="Populate eef_dashboard.composite_scores.learning_score via EEFEvaluator.",
        )

    def evaluate(self, report_data: Dict[str, Any], manifest_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        eef = report_data.get("eef_dashboard", {})
        if eef:
            composite = eef.get("composite_scores", {})
            learning_score = composite.get("learning_score")
            if learning_score is not None:
                if not (0.0 <= learning_score <= 1.0):
                    return RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        passed=False,
                        error_message=f"EEF learning score ({learning_score}) is out of valid range [0.0, 1.0].",
                        recommended_fix=self.recommended_fix,
                    )

        return RuleResult(rule_id=self.rule_id, rule_name=self.name, severity=self.severity, passed=True)


def get_default_invariant_rules() -> List[InvariantRule]:
    return [
        StoryTheoryCountSyncRule(),
        TimelineDaySyncRule(),
        ExecutionHashSyncRule(),
        EEFLearningScoreHarmonyRule(),
    ]
