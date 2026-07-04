import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from cognition.schemas.knowledge.evidence_gap import EvidenceGap
from cognition.schemas.knowledge.mechanism import Mechanism
from cognition.schemas.knowledge.open_question import OpenQuestion
from cognition.schemas.knowledge.principle import Principle
from cognition.schemas.knowledge.reconciliation_report import \
    ReconciliationReport
from cognition.schemas.knowledge.world_model import WorldModel


class KnowledgeRepository:
    """
    Handles local JSON persistence for Principle, WorldModel, OpenQuestion, ReconciliationReport, and EvidenceGap entities.
    """

    def __init__(self, base_path: Optional[Path] = None):
        project_root = Path(__file__).parent.parent.parent
        self.base_path = Path(base_path) if base_path else project_root / "data"

        self.principles_path = self.base_path / "principles"
        self.world_models_path = self.base_path / "world_models"
        self.open_questions_path = self.base_path / "open_questions"
        self.reconciliation_reports_path = self.base_path / "reconciliation_reports"
        self.evidence_gaps_path = self.base_path / "evidence_gaps"
        self.mechanisms_path = self.base_path / "mechanisms"

        self.principles_path.mkdir(parents=True, exist_ok=True)
        self.world_models_path.mkdir(parents=True, exist_ok=True)
        self.open_questions_path.mkdir(parents=True, exist_ok=True)
        self.reconciliation_reports_path.mkdir(parents=True, exist_ok=True)
        self.evidence_gaps_path.mkdir(parents=True, exist_ok=True)
        self.mechanisms_path.mkdir(parents=True, exist_ok=True)

        self.principles: Dict[str, Principle] = {}
        self.world_models: Dict[str, WorldModel] = {}
        self.open_questions: Dict[str, OpenQuestion] = {}
        self.reconciliation_reports: Dict[str, ReconciliationReport] = {}
        self.evidence_gaps: Dict[str, EvidenceGap] = {}
        self.mechanisms: Dict[str, Mechanism] = {}

        self.load_all()

    def load_all(self):
        """Loads all entities from disk into memory caches."""
        self.principles.clear()
        self.world_models.clear()
        self.open_questions.clear()
        self.reconciliation_reports.clear()
        self.evidence_gaps.clear()
        self.mechanisms.clear()

        # Load principles
        for file_path in self.principles_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.principles[data["id"]] = Principle.from_dict(data)
            except Exception as e:
                print(f"WARNING: Failed to load principle {file_path}: {e}")

        # Load world models
        for file_path in self.world_models_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.world_models[data["id"]] = WorldModel.from_dict(data)
            except Exception as e:
                print(f"WARNING: Failed to load world model {file_path}: {e}")

        # Load open questions
        for file_path in self.open_questions_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.open_questions[data["id"]] = OpenQuestion.from_dict(data)
            except Exception as e:
                print(f"WARNING: Failed to load open question {file_path}: {e}")

        # Load reconciliation reports
        for file_path in self.reconciliation_reports_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.reconciliation_reports[data["id"]] = (
                        ReconciliationReport.from_dict(data)
                    )
            except Exception as e:
                print(f"WARNING: Failed to load reconciliation report {file_path}: {e}")

        # Load evidence gaps
        for file_path in self.evidence_gaps_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.evidence_gaps[data["id"]] = EvidenceGap.from_dict(data)
            except Exception as e:
                print(f"WARNING: Failed to load evidence gap {file_path}: {e}")

        # Load mechanisms
        for file_path in self.mechanisms_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.mechanisms[data["id"]] = Mechanism.from_dict(data)
            except Exception as e:
                print(f"WARNING: Failed to load mechanism {file_path}: {e}")

    def save_principle(self, principle: Principle):
        """Persists a Principle object to disk."""
        self.principles[principle.id] = principle
        file_path = self.principles_path / f"{principle.id}.json"
        with open(file_path, "w") as f:
            json.dump(principle.to_dict(), f, indent=2)

    def get_principle(self, pid: str) -> Optional[Principle]:
        """Gets a principle by its ID."""
        return self.principles.get(pid)

    def list_principles(self, status: Optional[str] = None) -> List[Principle]:
        """Lists all cached principles, optionally filtered by status."""
        principles = list(self.principles.values())
        if status:
            principles = [p for p in principles if p.status.value == status]
        return principles

    def save_world_model(self, wm: WorldModel):
        """Persists a WorldModel object to disk."""
        self.world_models[wm.id] = wm
        file_path = self.world_models_path / f"{wm.id}.json"
        with open(file_path, "w") as f:
            json.dump(wm.to_dict(), f, indent=2)

    def get_world_model(self, wmid: str) -> Optional[WorldModel]:
        """Gets a world model by its ID."""
        return self.world_models.get(wmid)

    def get_latest_world_model(self) -> Optional[WorldModel]:
        """Gets the most recently saved world model sorted by step and created_at."""
        if not self.world_models:
            return None
        wms = list(self.world_models.values())
        # Sort by step, then by created_at
        wms.sort(key=lambda x: (x.step, x.created_at))
        return wms[-1]

    def save_open_question(self, oq: OpenQuestion):
        """Persists an OpenQuestion object to disk."""
        self.open_questions[oq.id] = oq
        file_path = self.open_questions_path / f"{oq.id}.json"
        with open(file_path, "w") as f:
            json.dump(oq.to_dict(), f, indent=2)

    def get_open_question(self, oqid: str) -> Optional[OpenQuestion]:
        """Gets an open question by its ID."""
        return self.open_questions.get(oqid)

    def list_open_questions(self, status: Optional[str] = None) -> List[OpenQuestion]:
        """Lists all cached open questions, optionally filtered by status."""
        questions = list(self.open_questions.values())
        if status:
            questions = [q for q in questions if q.status.value == status]
        return questions

    def save_reconciliation_report(self, report: ReconciliationReport):
        """Persists a ReconciliationReport object to disk."""
        self.reconciliation_reports[report.id] = report
        file_path = self.reconciliation_reports_path / f"{report.id}.json"
        with open(file_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

    def list_reconciliation_reports(self) -> List[ReconciliationReport]:
        """Lists all cached reconciliation reports sorted by step."""
        reports = list(self.reconciliation_reports.values())
        reports.sort(key=lambda x: (x.step, x.created_at))
        return reports

    def save_evidence_gap(self, gap: EvidenceGap):
        """Persists an EvidenceGap object to disk."""
        self.evidence_gaps[gap.id] = gap
        file_path = self.evidence_gaps_path / f"{gap.id}.json"
        with open(file_path, "w") as f:
            json.dump(gap.to_dict(), f, indent=2)

    def list_evidence_gaps(self) -> List[EvidenceGap]:
        """Lists all cached evidence gaps."""
        return list(self.evidence_gaps.values())

    def save_mechanism(self, mechanism: Mechanism):
        """Persists a Mechanism object to disk."""
        self.mechanisms[mechanism.id] = mechanism
        file_path = self.mechanisms_path / f"{mechanism.id}.json"
        with open(file_path, "w") as f:
            json.dump(mechanism.to_dict(), f, indent=2)

    def get_mechanism(self, mid: str) -> Optional[Mechanism]:
        """Gets a mechanism by its ID."""
        return self.mechanisms.get(mid)

    def list_mechanisms(self) -> List[Mechanism]:
        """Lists all cached mechanisms."""
        return list(self.mechanisms.values())

    def clear(self):
        """Clears memory caches and deletes files from base directory."""
        self.principles.clear()
        self.world_models.clear()
        self.open_questions.clear()
        self.reconciliation_reports.clear()
        self.evidence_gaps.clear()
        self.mechanisms.clear()

        for file_path in self.principles_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting principle {file_path}: {e}")

        for file_path in self.world_models_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting world model {file_path}: {e}")

        for file_path in self.open_questions_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting open question {file_path}: {e}")

        for file_path in self.reconciliation_reports_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting reconciliation report {file_path}: {e}")

        for file_path in self.evidence_gaps_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting evidence gap {file_path}: {e}")

        for file_path in self.mechanisms_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting mechanism {file_path}: {e}")
