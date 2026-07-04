import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cognition.contradiction.contradiction_detector import \
    ContradictionDetector
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.knowledge.mechanism import Mechanism
from cognition.schemas.knowledge.principle import (FalsifiablePrediction,
                                                   MaturationEntry, Principle,
                                                   PrincipleStatus)
from cognition.schemas.knowledge.world_model import WorldModel
from cognition.schemas.theory.theory import (Branch, MechanismComponent,
                                             Theory, TheoryStructured)
from flows.knowledge_flow.knowledge_compression_engine import \
    KnowledgeCompressionEngine
from flows.knowledge_flow.mechanism_engine import MechanismEngine
from flows.knowledge_flow.world_model_engine import WorldModelEngine
from memory.knowledge.knowledge_repository import KnowledgeRepository
from memory.lineage.theory_lineage import TheoryRecord


class TestPhase2Integration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = KnowledgeRepository(base_path=Path(self.temp_dir))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mechanism_engine_and_promotion(self):
        """Test MechanismEngine extracting mechanisms and promoting candidate concepts."""
        engine = MechanismEngine(knowledge_repo=self.repo)

        # Create theories referencing a candidate concept DELIVERY_EXHAUSTION across 3 different lineages
        t1 = Theory(
            id="t1",
            thesis="test",
            summary="Theory 1",
            lineage_id="lineage_a",
            confidence_state=ConfidenceState(),
            summary_structured=TheoryStructured(
                claim="Deliv exh claim",
                mechanism="delivery",
                if_branch=Branch(condition="cond", action="act"),
                else_branch=Branch(condition="cond", action="act"),
                unless="",
                falsified_if="fail",
                mechanism_components=[
                    MechanismComponent(
                        component_id="comp1",
                        description="desc",
                        observable="obs",
                        expected_behavior="beh",
                        concept_tags=["DELIVERY_EXHAUSTION"],
                        relation_type="AMPLIFIES",
                    )
                ],
            ),
        )
        t2 = Theory(
            id="t2",
            thesis="test",
            summary="Theory 2",
            lineage_id="lineage_b",
            confidence_state=ConfidenceState(),
            summary_structured=TheoryStructured(
                claim="Deliv exh claim 2",
                mechanism="delivery",
                if_branch=Branch(condition="cond", action="act"),
                else_branch=Branch(condition="cond", action="act"),
                unless="",
                falsified_if="fail",
                mechanism_components=[
                    MechanismComponent(
                        component_id="comp1",
                        description="desc",
                        observable="obs",
                        expected_behavior="beh",
                        concept_tags=["DELIVERY_EXHAUSTION"],
                        relation_type="AMPLIFIES",
                    )
                ],
            ),
        )
        t3 = Theory(
            id="t3",
            thesis="test",
            summary="Theory 3",
            lineage_id="lineage_c",
            confidence_state=ConfidenceState(),
            summary_structured=TheoryStructured(
                claim="Deliv exh claim 3",
                mechanism="delivery",
                if_branch=Branch(condition="cond", action="act"),
                else_branch=Branch(condition="cond", action="act"),
                unless="",
                falsified_if="fail",
                mechanism_components=[
                    MechanismComponent(
                        component_id="comp1",
                        description="desc",
                        observable="obs",
                        expected_behavior="beh",
                        concept_tags=["DELIVERY_EXHAUSTION"],
                        relation_type="AMPLIFIES",
                    )
                ],
            ),
        )

        # 1. Process first theory (1 lineage) -> Should remain candidate
        mechs = engine.process_theories([t1], step=1)
        self.assertEqual(len(mechs), 1)
        self.assertEqual(mechs[0].name, "DELIVERY_EXHAUSTION")
        self.assertEqual(mechs[0].concept_type, "candidate")

        # 2. Process t2 and t3 (total 3 unique lineages) -> Should promote to core
        mechs = engine.process_theories([t2, t3], step=2)
        # Find the delivery exhaustion mechanism
        delivery_exh = [m for m in mechs if m.name == "DELIVERY_EXHAUSTION"][0]
        self.assertEqual(delivery_exh.concept_type, "core")

    def test_semantic_contradiction_detector(self):
        """Test ContradictionDetector triggers on opposing relation types of similar concept tags."""
        detector = ContradictionDetector(verbose=True)

        t_curr = Theory(
            id="curr",
            thesis="test",
            summary="Current",
            lineage_id="lineage_curr",
            confidence_state=ConfidenceState(),
            summary_structured=TheoryStructured(
                claim="Current claim",
                mechanism="delivery",
                if_branch=Branch(condition="cond", action="act"),
                else_branch=Branch(condition="cond", action="act"),
                unless="",
                falsified_if="fail",
                mechanism_components=[
                    MechanismComponent(
                        component_id="comp1",
                        description="desc",
                        observable="obs",
                        expected_behavior="beh",
                        concept_tags=["DELIVERY_EXHAUSTION"],
                        relation_type="AMPLIFIES",
                    )
                ],
            ),
        )

        t_hist = Theory(
            id="hist",
            thesis="test",
            summary="Historical",
            lineage_id="lineage_hist",
            confidence_state=ConfidenceState(),
            summary_structured=TheoryStructured(
                claim="Historical claim",
                mechanism="delivery",
                if_branch=Branch(condition="cond", action="act"),
                else_branch=Branch(condition="cond", action="act"),
                unless="",
                falsified_if="fail",
                mechanism_components=[
                    MechanismComponent(
                        component_id="comp1",
                        description="desc",
                        observable="obs",
                        expected_behavior="beh",
                        concept_tags=["DELIVERY_EXHAUSTION"],
                        relation_type="DAMPENS",  # CONTRADICTION! AMPLIFIES vs DAMPENS
                    )
                ],
            ),
        )

        res = detector.detect(
            current_theory=t_curr,
            historical_theories=[t_hist],
            validations=[],
            reflections=[],
        )

        self.assertTrue(res["score"] > 0.3)
        has_semantic_msg = any(
            "Semantic Contradiction: Concept 'DELIVERY_EXHAUSTION'" in ind
            for ind in res.get("indicators", [])
        )
        self.assertTrue(has_semantic_msg)

    def test_principle_maturation_and_boundaries(self):
        """Test Principle maturation counterfactual roadmap and boundary discovery."""
        compression = KnowledgeCompressionEngine()

        principle = Principle(
            statement="Volume confirmation is key",
            created_at_step=1,
            status=PrincipleStatus.EMERGING,
            falsifiable_predictions=[
                FalsifiablePrediction(
                    target_component="volume_confirmation",
                    expected_status="passed",
                    applicability_filter={"regime_subtype": "trend"},
                    empirical_support_count=0,
                    empirical_failure_count=0,
                )
            ],
        )

        # Mock prediction history: 4 successful attributions, 2 failed
        pred_history = [
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"validation_score": 1.0},
                "components_failed": [],  # passes
            }
        ] * 4 + [
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"validation_score": 0.0},
                "components_failed": ["volume_confirmation"],  # fails
            }
        ] * 2

        validated = compression.validate_principle(principle, pred_history)

        # Verify boundaries
        self.assertEqual(validated.valid_under.get("trend"), 4)
        self.assertEqual(validated.fails_under.get("trend"), 2)

        # Verify maturation entry and counterfactual roadmap logs
        self.assertTrue(len(validated.maturation_history) > 0)
        entry = validated.maturation_history[0]
        self.assertEqual(entry.status_before, "emerging")
        # Since it only had 4 support counts and 2 contradictions, it won't satisfy TRUSTED (needs support >= 5 and contradictions == 0)
        self.assertEqual(entry.status_after, "emerging")
        self.assertIn("0 contradiction count", entry.promotion_requirements_remaining)
        self.assertIn(
            "+1 validating observations", entry.promotion_requirements_remaining
        )

    def test_world_model_descriptive_constraints(self):
        """Test WorldModelEngine parses explanatory constraints and maps them to policy limits."""
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "narrative_summary": "High volatility observed.",
                "dominant_mechanisms": [],
                "active_constraints": [],
                "explanatory_constraints": ["HIGH_UNCERTAINTY", "LOW_LIQUIDITY"],
                "applicable_regimes": ["range_bound"],
                "stability": "Stable",
            }
        )

        wm_engine = WorldModelEngine(llm_client=mock_client)
        principle = Principle(
            statement="Volume confirmation is key",
            created_at_step=1,
            status=PrincipleStatus.TRUSTED,
        )
        wm = wm_engine.synthesize(active_principles=[principle], step=1)

        self.assertIn("HIGH_UNCERTAINTY", wm.explanatory_constraints)
        self.assertIn("LOW_LIQUIDITY", wm.explanatory_constraints)

        # Test deterministic mapping in world model
        self.assertEqual(wm.regime_constraints["range_bound"]["max_confidence"], 0.42)
        self.assertEqual(
            wm.regime_constraints["range_bound"]["blocked_bias"], "bullish"
        )

    def test_mechanism_lifecycle_transitions(self):
        """Test MechanismEngine status transitions (candidate -> active -> stable -> retired) using production thresholds."""
        # Enforce production thresholds with test_mode=False
        engine = MechanismEngine(knowledge_repo=self.repo, test_mode=False)

        # Create a candidate mechanism
        mech = Mechanism(
            mechanism_id="MECH_999",
            canonical_name="VOLUME_DIVERGENCY",
            concept_tags=["VOLUME_DIVERGENCY"],
            relation_type="AMPLIFIES",
            first_seen=1,
            last_seen=1,
            days_active=1,
            times_reused=0,
            times_modified=0,
            times_retired=0,
            support_count=0,
            contradiction_count=0,
            prediction_helped=0,
            prediction_harmed=0,
            status="candidate",
            regimes_seen=["neutral"],
            name="VOLUME_DIVERGENCY",
            description="Volume divergency fails",
            concept_type="candidate",
            associated_theory_ids=[],
            associated_lineages=[],
            created_at_step=1,
        )
        mech.id = "MECH_999"
        self.repo.save_mechanism(mech)

        # 1. Initially candidate with 1 day active and 0 support
        mechs = engine.process_theories([], step=2)
        m = self.repo.get_mechanism("MECH_999")
        self.assertEqual(m.status, "candidate")

        # 2. Promotes to active with 3 days active
        m.days_active = 3
        self.repo.save_mechanism(m)
        mechs = engine.process_theories([], step=3)
        m = self.repo.get_mechanism("MECH_999")
        self.assertEqual(m.status, "active")

        # 3. Does not promote to stable with days_active=10 but support=0
        m.days_active = 10
        self.repo.save_mechanism(m)
        mechs = engine.process_theories([], step=4)
        m = self.repo.get_mechanism("MECH_999")
        self.assertEqual(m.status, "active")

        # 4. Promotes to stable with days_active=10, support=8, helped=4, contradiction=0
        m.support_count = 8
        m.prediction_helped = 4
        self.repo.save_mechanism(m)
        mechs = engine.process_theories([], step=5)
        m = self.repo.get_mechanism("MECH_999")
        self.assertEqual(m.status, "stable")

        # 5. Transitions to retired when contradictions exceed threshold (contradictions > 1.5 * support)
        m.contradiction_count = 15  # 15 > 1.5 * 8 (12)
        m.support_count = 8
        self.repo.save_mechanism(m)
        mechs = engine.process_theories([], step=6)
        m = self.repo.get_mechanism("MECH_999")
        self.assertEqual(m.status, "retired")


if __name__ == "__main__":
    unittest.main()
