"""
Scientific Integrity Enforcement Layer (SIEL v1.0)
Guarantees scientific reproducibility, metric provenance tracking,
cross-sectional reconciliation, and integrity certification.
"""

from telemetry.siel.certification import CertificationLevel, ReportCertification
from telemetry.siel.rules import InvariantRule, RuleSeverity, RuleResult
from telemetry.siel.validator import ScientificIntegrityValidator, ScientificIntegrityError
from telemetry.siel.provenance import MetricProvenanceRecord, ProvenanceTracker
from telemetry.siel.canonical_report import CanonicalReplayReport, ReportMetadata, NarrativeSummary

__all__ = [
    "CertificationLevel",
    "ReportCertification",
    "InvariantRule",
    "RuleSeverity",
    "RuleResult",
    "ScientificIntegrityValidator",
    "ScientificIntegrityError",
    "MetricProvenanceRecord",
    "ProvenanceTracker",
    "CanonicalReplayReport",
    "ReportMetadata",
    "NarrativeSummary",
]
