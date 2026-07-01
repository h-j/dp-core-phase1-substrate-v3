import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import json
from uuid import uuid4

from flows.knowledge_flow.novelty_detection_gate import NoveltyDetectionGate
from flows.knowledge_flow.knowledge_compression_engine import KnowledgeCompressionEngine
from cognition.schemas.knowledge.principle import Principle, PrincipleStatus, FalsifiablePrediction
from cognition.schemas.knowledge.reconciliation_report import ReconciliationReport

def mock_llm_generate(prompt: str, json_format: bool = False) -> str:
    prompt_lower = prompt.lower()
    if "novelty score" in prompt_lower:
        return json.dumps({
            "critique": "The prior theory succeeded and the current state is consistent.",
            "decision": "REINFORCE",
            "explanation": "No new structural behavior noticed."
        })
    elif "consolidate the following multiple narrow principles" in prompt_lower:
        return json.dumps({
            "statement": "Consolidated broad volume confirmation mechanism.",
            "applicability_filter": {
                "regime_subtype": "range_bound",
                "volatility_regime": "compressed"
            },
            "expected_status": "failed"
        })
    elif "exceptionally high empirical support" in prompt_lower:
        return json.dumps({
            "statement": "Broad generalized volume confirmation mechanism statement.",
            "applicability_filter": {
                "regime_subtype": None,
                "volatility_regime": "compressed"
            }
        })
    elif "high contradictions" in prompt_lower:
        return json.dumps({
            "split_required": True,
            "principles": [
                {
                    "statement": "Split statement 1...",
                    "applicability_filter": { "regime_subtype": "momentum" }
                },
                {
                    "statement": "Split statement 2...",
                    "applicability_filter": { "regime_subtype": "fatigue" }
                }
            ]
        })
    return "{}"

class TestKnowledgeReconciliation(unittest.TestCase):
    
    def test_reconciliation_report_serialization(self):
        """Test ReconciliationReport schema attributes."""
        report = ReconciliationReport(
            id=str(uuid4()),
            step=10,
            merged_count=3,
            generalized_count=1,
            retired_count=2,
            restricted_count=1,
            knowledge_debt_before=15.0,
            knowledge_debt_after=9.0,
            coverage_before=0.20,
            coverage_after=0.45,
            compression_ratio_before="10→8→0→5→1",
            compression_ratio_after="10→8→0→3→1",
            summary_text="Debt decreased"
        )
        self.assertEqual(report.step, 10)
        self.assertEqual(report.merged_count, 3)
        self.assertEqual(report.knowledge_debt_after, 9.0)

    @patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_llm_generate)
    def test_novelty_detection_gate(self, mock_gen):
        """Test novelty scoring calculations and critique decisions."""
        gate = NoveltyDetectionGate()
        
        # Test case 1: prior theory succeeded, active principle coverage exists
        p = Principle(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            status=PrincipleStatus.ACTIVE,
            statement="Volume fails under range",
            associated_lineage_ids=["lineage-1"],
            falsifiable_predictions=[
                FalsifiablePrediction(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc),
                    target_component="volume_confirmation",
                    expected_status="failed",
                    applicability_filter={"regime_subtype": "range_bound"}
                )
            ],
            created_at_step=0
        )
        
        score = gate.compute_novelty_score(
            regime_similarity=0.9,
            prior_prediction={"confidence": 0.8},
            prior_prediction_result={"direction_score": 1.0}, # error = 0.2
            prior_attribution=MagicMock(components_failed=[]), # succeeded
            active_principles=[p],
            regime_subtype="range_bound"
        )
        self.assertAlmostEqual(score, 0.065)
        
        decision, final_score, rationale = gate.is_novel(
            observation={"regime_similarity": 0.9},
            regime_subtype="range_bound",
            prior_theory=MagicMock(summary="Prior theory claim"),
            prior_prediction={"confidence": 0.8},
            prior_prediction_result={"direction_score": 1.0},
            prior_attribution=MagicMock(components_failed=[]),
            active_principles=[p]
        )
        self.assertEqual(decision, "REINFORCE")
        self.assertIn("succeeded", rationale)

    @patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_llm_generate)
    def test_hierarchical_merging(self, mock_gen):
        """Test merging of related candidate principles targeting the same component."""
        engine = KnowledgeCompressionEngine()
        
        p1 = Principle(
            id="p1-id",
            created_at=datetime.now(timezone.utc),
            status=PrincipleStatus.CANDIDATE,
            statement="Volume fails under compressed volatility.",
            associated_lineage_ids=["lin-1"],
            falsifiable_predictions=[
                FalsifiablePrediction(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc),
                    target_component="volume_confirmation",
                    expected_status="failed",
                    applicability_filter={"volatility_regime": "compressed"}
                )
            ],
            support_count=3,
            contradiction_count=0,
            created_at_step=0
        )
        
        p2 = Principle(
            id="p2-id",
            created_at=datetime.now(timezone.utc),
            status=PrincipleStatus.CANDIDATE,
            statement="Volume validation fails when volatility compresses.",
            associated_lineage_ids=["lin-2"],
            falsifiable_predictions=[
                FalsifiablePrediction(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc),
                    target_component="volume_confirmation",
                    expected_status="failed",
                    applicability_filter={"volatility_regime": "compressed"}
                )
            ],
            support_count=2,
            contradiction_count=0,
            created_at_step=0
        )
        
        merged_p, count = engine.hierarchical_merge([p1, p2])
        self.assertEqual(count, 1)
        reconciled_actives = [p for p in merged_p if p.status != PrincipleStatus.RETIRED]
        self.assertEqual(len(reconciled_actives), 1)
        self.assertEqual(reconciled_actives[0].statement, "Consolidated broad volume confirmation mechanism.")
        self.assertEqual(reconciled_actives[0].support_count, 5)

    @patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_llm_generate)
    def test_knowledge_reconciliation_engine(self, mock_gen):
        """Test the full reconciliation pass covering generalization, splits, and Knowledge Debt."""
        engine = KnowledgeCompressionEngine()
        
        p_high_support = Principle(
            id="p-high-id",
            created_at=datetime.now(timezone.utc),
            status=PrincipleStatus.ACTIVE,
            statement="High support principle.",
            associated_lineage_ids=["lin-3"],
            falsifiable_predictions=[
                FalsifiablePrediction(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc),
                    target_component="absorption_rate",
                    expected_status="passed",
                    applicability_filter={"regime_subtype": "momentum"}
                )
            ],
            support_count=8,
            contradiction_count=1,
            created_at_step=0
        )
        
        p_high_contradiction = Principle(
            id="p-contra-id",
            created_at=datetime.now(timezone.utc),
            status=PrincipleStatus.ACTIVE,
            statement="Contradicted principle.",
            associated_lineage_ids=["lin-4"],
            falsifiable_predictions=[
                FalsifiablePrediction(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc),
                    target_component="price_structure",
                    expected_status="failed",
                    applicability_filter={"regime_subtype": "neutral"}
                )
            ],
            support_count=1,
            contradiction_count=4,
            created_at_step=0
        )
        
        prediction_history = [
            {"theory_id": "lin-3", "components_failed": []},
            {"theory_id": "lin-4", "components_failed": ["price_structure"]}
        ]
        
        reconciled, stats = engine.reconcile_knowledge(
            principles=[p_high_support, p_high_contradiction],
            prediction_history=prediction_history,
            open_questions=[],
            step=10
        )
        
        stable_principles = [p for p in reconciled if p.status == PrincipleStatus.CANONICAL]
        self.assertEqual(len(stable_principles), 1)
        self.assertEqual(stable_principles[0].statement, "Broad generalized volume confirmation mechanism statement.")
        
        candidates = [p for p in reconciled if p.status == PrincipleStatus.CANDIDATE]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].statement, "Split statement 1...")
        self.assertEqual(candidates[1].statement, "Split statement 2...")

if __name__ == "__main__":
    unittest.main()
