"""
Attribution models for causal validation analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MechanismComponent:
    """A single testable sub-component of a theory's mechanism."""
    component_id: str
    description: str
    observable: str
    expected_behavior: str
    dependency: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "description": self.description,
            "observable": self.observable,
            "expected_behavior": self.expected_behavior,
            "dependency": self.dependency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MechanismComponent":
        return cls(
            component_id=data["component_id"],
            description=data["description"],
            observable=data["observable"],
            expected_behavior=data["expected_behavior"],
            dependency=data.get("dependency")
        )

@dataclass
class AttributionResult:
    """Captures WHY a theory succeeded or failed."""
    theory_id: str
    theory_claim: str
    outcome: str
    components_tested: List[str] = field(default_factory=list)
    components_passed: List[str] = field(default_factory=list)
    components_failed: List[str] = field(default_factory=list)
    falsification_triggered: Optional[str] = None
    falsification_conditions_checked: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    actual_outcome: str = ""
    divergence_point: str = ""
    divergence_severity: float = 0.0
    attribution_reasoning: str = ""
    root_cause_component: Optional[str] = None
    attribution_confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    market_snapshot: Optional[Dict[str, Any]] = None
    
    def is_falsified(self) -> bool:
        return self.outcome == "falsified"
    
    def get_mutation_guidance(self) -> str:
        if self.outcome == "validated":
            return "Theory validated."
        guidance = f"Theory {self.outcome}. "
        if self.components_failed:
            guidance += f"Failed components: {', '.join(self.components_failed)}. "
        if self.root_cause_component:
            guidance += f"Root cause: {self.root_cause_component}. "
        return guidance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theory_id": self.theory_id,
            "theory_claim": self.theory_claim,
            "outcome": self.outcome,
            "components_passed": self.components_passed,
            "components_failed": self.components_failed,
            "falsification_triggered": self.falsification_triggered,
            "attribution_reasoning": self.attribution_reasoning,
            "root_cause_component": self.root_cause_component,
            "timestamp": self.timestamp
        }