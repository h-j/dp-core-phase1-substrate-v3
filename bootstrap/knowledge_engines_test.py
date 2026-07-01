import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from cognition.schemas.knowledge.principle import (FalsifiablePrediction,
                                                   Principle, PrincipleStatus)
from cognition.schemas.knowledge.world_model import WorldModel
from flows.knowledge_flow.knowledge_compression_engine import \
    KnowledgeCompressionEngine
from flows.knowledge_flow.world_model_engine import WorldModelEngine
from flows.theory_flow.attribution import AttributionResult


class TestKnowledgeEngines(unittest.TestCase):
    def test_grouping_and_compression(self):
        """Verify experiences, lineages, and attributions are grouped and compressed correctly."""
        # Mock LLM Client
        mock_llm = MagicMock()
        mock_response = {
            "statement": "Volume confirmation is only predictive when participation expands.",
            "applicability_filter": {"regime_subtype": "trend"},
            "falsifiable_predictions": [
                {
                    "target_component": "volume_confirmation",
                    "expected_status": "passed",
                    "applicability_filter": {"regime_subtype": "trend"},
                }
            ],
        }
        mock_llm.generate.return_value = json.dumps(mock_response)

        engine = KnowledgeCompressionEngine(llm_client=mock_llm)

        # Mock experiences and attributions
        mock_exp1 = MagicMock()
        mock_exp1.lineage_id = "theory-1"
        mock_exp1.target_regime = {"regime_subtype": "trend"}

        mock_exp2 = MagicMock()
        mock_exp2.lineage_id = "theory-2"
        mock_exp2.target_regime = {"regime_subtype": "range_bound"}

        attr1 = AttributionResult(
            theory_id="theory-1",
            theory_claim="Claim 1",
            outcome="higher",
            components_tested=["volume_confirmation"],
            components_passed=["volume_confirmation"],
            components_failed=[],
        )

        attr2 = AttributionResult(
            theory_id="theory-2",
            theory_claim="Claim 2",
            outcome="lower",
            components_tested=["volume_confirmation"],
            components_passed=[],
            components_failed=["volume_confirmation"],
        )

        principles = engine.compress(
            experiences=[mock_exp1, mock_exp2],
            theory_lineages=[],
            attributions=[attr1, attr2],
            step=5,
        )

        # Assertions
        self.assertEqual(len(principles), 1)
        p = principles[0]
        self.assertEqual(
            p.statement,
            "Volume confirmation is only predictive when participation expands.",
        )
        self.assertEqual(p.status, PrincipleStatus.CANDIDATE)
        self.assertEqual(len(p.falsifiable_predictions), 1)
        self.assertEqual(
            p.falsifiable_predictions[0].target_component, "volume_confirmation"
        )
        self.assertEqual(p.falsifiable_predictions[0].expected_status, "passed")
        self.assertEqual(
            p.falsifiable_predictions[0].applicability_filter["regime_subtype"], "trend"
        )
        self.assertIn("theory-1", p.associated_lineage_ids)
        self.assertIn("theory-2", p.associated_lineage_ids)

    def test_retrospective_validation(self):
        """Verify principles are correctly backtested and promoted/retired."""
        engine = KnowledgeCompressionEngine(llm_client=MagicMock())

        fp = FalsifiablePrediction(
            target_component="volume_confirmation",
            expected_status="passed",
            applicability_filter={"regime_subtype": "trend"},
        )
        p = Principle(
            status=PrincipleStatus.CANDIDATE,
            statement="Test statement.",
            created_at_step=2,
            falsifiable_predictions=[fp],
        )

        # Mock prediction history
        # 4 records matching trend context where volume_confirmation passed (no failure)
        # 1 record matching trend context where volume_confirmation failed
        # 2 records matching non-trend context (ignored)
        history = [
            # Matching, supported
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            # Matching, contradicted
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
            # Not matching
            {
                "regime_subtype": "range_bound",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            {
                "regime_subtype": "range_bound",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
        ]

        validated_p = engine.validate_principle(p, history)

        # Total evaluations = 5 matching, support = 4, contradiction = 1
        # Accuracy = 4 / 5 = 80% (>= 70%, support >= 5 -> promotes to ACTIVE)
        self.assertEqual(validated_p.support_count, 4)
        self.assertEqual(validated_p.contradiction_count, 1)
        self.assertEqual(validated_p.confidence, 0.8)
        self.assertEqual(validated_p.status, PrincipleStatus.EMERGING)

        # Scenario 2: High contradiction rate (accuracy < 50%) -> retires
        fp2 = FalsifiablePrediction(
            target_component="volume_confirmation",
            expected_status="passed",
            applicability_filter={"regime_subtype": "trend"},
        )
        p2 = Principle(
            status=PrincipleStatus.CANDIDATE,
            statement="Test statement 2.",
            created_at_step=2,
            falsifiable_predictions=[fp2],
        )
        history2 = [
            # 1 support, 4 contradictions
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 1.0},
                "components_failed": [],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
            {
                "regime_subtype": "trend",
                "prior_prediction_result": {"direction_score": 0.0},
                "components_failed": ["volume_confirmation"],
            },
        ]

        validated_p2 = engine.validate_principle(p2, history2)
        self.assertEqual(validated_p2.status, PrincipleStatus.RETIRED)

    def test_contradiction_resolution_and_mutation(self):
        """Verify active principles mutate correctly on contradiction."""
        mock_llm = MagicMock()
        mock_response = {
            "statement": "Volume confirmation is only predictive when participation expands in trend.",
            "applicability_filter_updates": {"volatility_regime": "expanded"},
        }
        mock_llm.generate.return_value = json.dumps(mock_response)

        engine = KnowledgeCompressionEngine(llm_client=mock_llm)

        fp = FalsifiablePrediction(
            target_component="volume_confirmation",
            expected_status="passed",
            applicability_filter={"regime_subtype": "trend"},
        )
        p = Principle(
            status=PrincipleStatus.ACTIVE,
            statement="Volume confirmation passes in trend.",
            created_at_step=1,
            falsifiable_predictions=[fp],
        )

        # Contradiction: volume_confirmation fails under trend regime
        attr = AttributionResult(
            theory_id="theory-10",
            theory_claim="Trend claim",
            outcome="higher",
            components_tested=["volume_confirmation"],
            components_passed=[],
            components_failed=["volume_confirmation"],
        )

        updated_principles = engine.resolve_contradictions(
            active_principles=[p],
            latest_attribution=attr,
            current_regime_context={
                "regime_subtype": "trend",
                "volatility_regime": "compressed",
            },
            step=10,
        )

        self.assertEqual(len(updated_principles), 1)
        p_up = updated_principles[0]
        # Should transition back to CANDIDATE for re-validation, statements and applicability filters should be updated
        self.assertEqual(p_up.status, PrincipleStatus.CANDIDATE)
        self.assertEqual(
            p_up.statement,
            "Volume confirmation is only predictive when participation expands in trend.",
        )
        self.assertEqual(
            p_up.falsifiable_predictions[0].applicability_filter["volatility_regime"],
            "expanded",
        )
        self.assertEqual(len(p_up.revision_history), 1)
        self.assertEqual(p_up.revision_history[0].revision_step, 10)

    def test_world_model_synthesis(self):
        """Verify narrative synthesis and structured overrides constraints generation."""
        mock_llm = MagicMock()
        # Mock unified narrative and constraints synthesis
        mock_llm.generate.return_value = json.dumps(
            {
                "narrative_summary": "System in consolidation equilibrium.",
                "regime_constraints": {
                    "range_bound": {"blocked_bias": "bullish", "max_confidence": 0.4}
                },
            }
        )

        wm_engine = WorldModelEngine(llm_client=mock_llm)

        p = Principle(
            status=PrincipleStatus.ACTIVE,
            statement="Volume fails in range bound.",
            created_at_step=5,
        )

        wm = wm_engine.synthesize(active_principles=[p], step=15)

        self.assertEqual(wm.step, 15)
        self.assertEqual(wm.narrative_summary, "System in consolidation equilibrium.")
        self.assertEqual(wm.active_principle_ids, [p.id])
        self.assertEqual(
            wm.regime_constraints["range_bound"]["blocked_bias"], "bullish"
        )
        self.assertEqual(wm.regime_constraints["range_bound"]["max_confidence"], 0.4)


if __name__ == "__main__":
    unittest.main()
