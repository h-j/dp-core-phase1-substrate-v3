import unittest
from pathlib import Path
import tempfile
import os
from datetime import datetime, timezone

from cognition.schemas.knowledge.principle import (
    Principle,
    PrincipleStatus,
    FalsifiablePrediction,
    PrincipleRevision,
)
from cognition.schemas.knowledge.world_model import WorldModel
from cognition.schemas.knowledge.open_question import OpenQuestion, QuestionStatus
from memory.knowledge.knowledge_repository import KnowledgeRepository

class TestKnowledgeSchemasAndRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = KnowledgeRepository(base_path=Path(self.temp_dir))

    def tearDown(self):
        self.repo.clear()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_principle_serialization(self):
        """Verify Principle schema serialization and deserialization."""
        pred = FalsifiablePrediction(
            target_component="volume_confirmation",
            expected_status="passed",
            applicability_filter={"regime": "range_bound", "volatility": "normal"}
        )
        
        rev = PrincipleRevision(
            revision_step=1,
            previous_statement="Old statement.",
            updated_statement="New statement.",
            change_reason="Empirical drift."
        )

        p = Principle(
            status=PrincipleStatus.ACTIVE,
            statement="Volume confirmation is only predictive when participation and volatility expand.",
            associated_lineage_ids=["lineage-123"],
            supporting_theory_ids=["theory-456"],
            contradicting_theory_ids=["theory-789"],
            supporting_experience_ids=["exp-000"],
            falsifiable_predictions=[pred],
            confidence=0.85,
            support_count=10,
            contradiction_count=2,
            created_at_step=5,
            revision_history=[rev]
        )

        d = p.to_dict()
        self.assertEqual(d["status"], "active")
        self.assertEqual(d["statement"], p.statement)
        self.assertEqual(d["created_at_step"], 5)
        self.assertEqual(d["confidence"], 0.85)
        self.assertEqual(len(d["falsifiable_predictions"]), 1)
        self.assertEqual(d["falsifiable_predictions"][0]["target_component"], "volume_confirmation")
        self.assertEqual(len(d["revision_history"]), 1)
        self.assertEqual(d["revision_history"][0]["revision_step"], 1)

        # Reconstruct
        reconstructed = Principle.from_dict(d)
        self.assertEqual(reconstructed.id, p.id)
        self.assertEqual(reconstructed.status, PrincipleStatus.ACTIVE)
        self.assertEqual(reconstructed.statement, p.statement)
        self.assertEqual(reconstructed.confidence, 0.85)
        self.assertEqual(len(reconstructed.falsifiable_predictions), 1)
        self.assertEqual(reconstructed.falsifiable_predictions[0].target_component, "volume_confirmation")
        self.assertEqual(len(reconstructed.revision_history), 1)
        self.assertEqual(reconstructed.revision_history[0].revision_step, 1)

    def test_world_model_serialization(self):
        """Verify WorldModel schema serialization and deserialization."""
        wm = WorldModel(
            step=10,
            narrative_summary="Market behaves as an equilibrium system.",
            active_principle_ids=["p-1", "p-2"],
            regime_constraints={"range_bound": {"blocked_bias": "bullish", "max_confidence": 0.5}}
        )

        d = wm.to_dict()
        self.assertEqual(d["step"], 10)
        self.assertEqual(d["narrative_summary"], "Market behaves as an equilibrium system.")
        self.assertEqual(d["active_principle_ids"], ["p-1", "p-2"])
        self.assertEqual(d["regime_constraints"]["range_bound"]["blocked_bias"], "bullish")

        # Reconstruct
        reconstructed = WorldModel.from_dict(d)
        self.assertEqual(reconstructed.id, wm.id)
        self.assertEqual(reconstructed.step, 10)
        self.assertEqual(reconstructed.narrative_summary, wm.narrative_summary)
        self.assertEqual(reconstructed.active_principle_ids, ["p-1", "p-2"])
        self.assertEqual(reconstructed.regime_constraints["range_bound"]["blocked_bias"], "bullish")

    def test_open_question_serialization(self):
        """Verify OpenQuestion schema serialization and deserialization."""
        oq = OpenQuestion(
            created_at_step=8,
            question_text="Why did volume confirmation fail despite high participation?",
            source_contradiction_ids=["contra-123"],
            hypothesized_factors=["volatility compression"],
            status=QuestionStatus.ACTIVE,
            resolution_principle_id=None
        )

        d = oq.to_dict()
        self.assertEqual(d["created_at_step"], 8)
        self.assertEqual(d["question_text"], "Why did volume confirmation fail despite high participation?")
        self.assertEqual(d["status"], "active")
        self.assertIsNone(d["resolution_principle_id"])

        # Reconstruct
        reconstructed = OpenQuestion.from_dict(d)
        self.assertEqual(reconstructed.id, oq.id)
        self.assertEqual(reconstructed.created_at_step, 8)
        self.assertEqual(reconstructed.status, QuestionStatus.ACTIVE)
        self.assertIsNone(reconstructed.resolution_principle_id)

    def test_repository_persistence(self):
        """Verify saving and loading from KnowledgeRepository."""
        pred = FalsifiablePrediction(
            target_component="volume_confirmation",
            expected_status="passed",
            applicability_filter={}
        )
        p = Principle(
            status=PrincipleStatus.STABLE,
            statement="Volume confirmation is only predictive when participation and volatility expand.",
            created_at_step=5,
            falsifiable_predictions=[pred]
        )
        
        wm = WorldModel(
            step=12,
            narrative_summary="Grounded equilibrium model.",
            active_principle_ids=[p.id],
            regime_constraints={}
        )
        
        oq = OpenQuestion(
            created_at_step=5,
            question_text="Why did volume confirmation fail?",
            source_contradiction_ids=["contra-456"],
            hypothesized_factors=[]
        )

        # Save
        self.repo.save_principle(p)
        self.repo.save_world_model(wm)
        self.repo.save_open_question(oq)

        # Create new repository instance to load from disk
        new_repo = KnowledgeRepository(base_path=Path(self.temp_dir))
        
        # Verify principle
        loaded_p = new_repo.get_principle(p.id)
        self.assertIsNotNone(loaded_p)
        self.assertEqual(loaded_p.statement, p.statement)
        self.assertEqual(loaded_p.status, PrincipleStatus.STABLE)
        self.assertEqual(len(loaded_p.falsifiable_predictions), 1)
        self.assertEqual(loaded_p.falsifiable_predictions[0].target_component, "volume_confirmation")
        
        # Verify world model
        loaded_wm = new_repo.get_world_model(wm.id)
        self.assertIsNotNone(loaded_wm)
        self.assertEqual(loaded_wm.narrative_summary, wm.narrative_summary)
        self.assertEqual(loaded_wm.step, 12)
        
        # Verify latest world model
        latest_wm = new_repo.get_latest_world_model()
        self.assertIsNotNone(latest_wm)
        self.assertEqual(latest_wm.id, wm.id)
        
        # Verify open question
        loaded_oq = new_repo.get_open_question(oq.id)
        self.assertIsNotNone(loaded_oq)
        self.assertEqual(loaded_oq.question_text, oq.question_text)
        self.assertEqual(loaded_oq.status, QuestionStatus.ACTIVE)

        # Test filtering list methods
        self.assertEqual(len(new_repo.list_principles(status="stable")), 1)
        self.assertEqual(len(new_repo.list_principles(status="candidate")), 0)
        self.assertEqual(len(new_repo.list_open_questions(status="active")), 1)

if __name__ == "__main__":
    unittest.main()
