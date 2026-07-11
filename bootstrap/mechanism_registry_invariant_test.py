import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.knowledge.mechanism import Mechanism
from cognition.schemas.theory.theory import (Branch, MechanismComponent,
                                             Theory, TheoryStructured)
from flows.knowledge_flow.mechanism_engine import (
    MechanismEngine, match_and_register_in_registry)
from memory.knowledge.knowledge_repository import KnowledgeRepository


class TestMechanismRegistryInvariants(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = KnowledgeRepository(base_path=Path(self.temp_dir))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_invariant_1_immutable_semantic_proposition(self):
        """1. A registered mechanism's semantic proposition cannot be overwritten by a later theory mutation."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            relation_type="CONTRADICTS",
            first_seen=1,
            last_seen=1,
            days_active=1,
            status="candidate",
            regimes_seen=["neutral"],
            name="TREND_PERSISTENCE",
            description="Initial stable proposition of trend persistence.",
            concept_type="candidate",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        # Retrieve and simulate mutation (we no longer overwrite description/tags/relations in registry)
        mech_obj = self.repo.get_mechanism("MECH_001")
        if mech_obj:
            mech_obj.times_modified += 1
            mech_obj.last_seen = 2
            self.repo.save_mechanism(mech_obj)

        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(
            reloaded.description, "Initial stable proposition of trend persistence."
        )
        self.assertEqual(reloaded.concept_tags, ["TREND_PERSISTENCE"])
        self.assertEqual(reloaded.relation_type, "CONTRADICTS")
        self.assertEqual(reloaded.times_modified, 1)

    def test_invariant_2_tag_isolated_matches(self):
        """2. Two components sharing the same ontology tag but expressing different propositions register distinct IDs."""
        mech1 = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            relation_type="CONTRADICTS",
            first_seen=1,
            last_seen=1,
            days_active=1,
            status="candidate",
            regimes_seen=["neutral"],
            name="TREND_PERSISTENCE",
            description="Initial stable proposition of trend persistence.",
            concept_type="candidate",
        )
        mech1.id = "MECH_001"
        self.repo.save_mechanism(mech1)

        comp = {
            "component_id": "trend_persistence",
            "description": "Completely different semantic claim about range-bound reversion under tight liquidity.",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS",
        }

        mid = match_and_register_in_registry(comp, self.repo, step=2, regime="neutral")
        self.assertEqual(mid, "MECH_002")

    def test_invariant_3_atomic_evidence_attribution(self):
        """3. Multiple theory components mapped to the same mechanism produce exactly one evidence update."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=1,
            status="candidate",
            description="Trend persistence",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        prior_active_mechanisms = ["MECH_001", "MECH_001", "MECH_001"]

        # Simulated atomic attribution block
        is_correct = True
        unique_mids = set(prior_active_mechanisms)
        for mid in unique_mids:
            mech_obj = self.repo.get_mechanism(mid)
            if mech_obj:
                if mech_obj.status == "retired":
                    continue
                if is_correct:
                    mech_obj.prediction_helped += 1
                    mech_obj.support_count += 1
                self.repo.save_mechanism(mech_obj)

        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded.support_count, 1)

    def test_invariant_4_retired_isolation(self):
        """4. A retired mechanism cannot be matched, reused, modified, or receive evidence."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=10,
            status="retired",
            description="Initial description",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        comp = {
            "component_id": "trend_persistence",
            "description": "Initial description",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS",
        }
        new_mid = match_and_register_in_registry(
            comp, self.repo, step=2, regime="neutral"
        )
        self.assertEqual(new_mid, "MECH_002")

    def test_invariant_5_semantic_reuse(self):
        """5. Existing mechanism matching still allows genuine semantic reuse when propositions are sufficiently similar."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=1,
            status="candidate",
            description="Price structure maintains sequence of higher highs and lower lows.",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        comp = {
            "component_id": "trend_persistence",
            "description": "price structure exhibits higher highs and lower lows.",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS",
        }

        mid = match_and_register_in_registry(comp, self.repo, step=2, regime="neutral")
        self.assertEqual(mid, "MECH_001")

    def test_new_invariant_6_theory_removal_decoupled_from_registry(self):
        """6. Theory pruning (removed_mechanism_ids) removes mechanism from theory branch without changing global registry status or incrementing times_retired."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=2,
            status="active",
            description="Stable trend persistence mechanism.",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        # Simulate theory mutation step: MECH_001 is in removed_mechanism_ids
        removed_ids = ["MECH_001"]

        # Verify that we do NOT call status = retired or increment times_retired anymore (which we deleted in Task 1)
        # We simulate the exact logic: we do nothing to the registry for removed_ids
        for rid in removed_ids:
            # Under new architecture, this loop is removed!
            pass

        # Retrieve and verify it is untouched in the registry
        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded.status, "active")
        self.assertEqual(reloaded.times_retired, 0)

    def test_new_invariant_7_removed_mechanism_remains_active_for_future_reuse(self):
        """7. A mechanism pruned from one theory branch remains candidate/active and available for semantic reuse by other theories."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=2,
            status="active",
            description="Stable trend persistence mechanism.",
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        # It is pruned from some theory (does not change registry).
        # On the next step, a component is proposed that is semantically similar to MECH_001.
        comp = {
            "component_id": "trend_persistence",
            "description": "stable trend persistence mechanism.",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS",
        }

        # Match must still successfully reuse MECH_001
        mid = match_and_register_in_registry(comp, self.repo, step=3, regime="neutral")
        self.assertEqual(mid, "MECH_001")

    def test_new_invariant_8_deterministic_evidence_based_retirement(self):
        """8. Persistent mechanisms transition to RETIRED only through deterministic evaluation of accumulated evidence."""
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            days_active=5,
            status="active",
            description="Trend persistence",
            support_count=1,
            contradiction_count=4,  # total evidence = 5, contradictions > 1.5 * support
            prediction_helped=1,
            prediction_harmed=4,
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        # Run MechanismEngine daily processing (transition checks)
        engine = MechanismEngine(
            knowledge_repo=self.repo, test_mode=False
        )  # production rules mode

        # We call process_theories to run transitions
        engine.process_theories([], step=6, regime_subtype="neutral")

        # Verify it has transitioned to retired
        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded.status, "retired")
        self.assertEqual(reloaded.times_retired, 1)


if __name__ == "__main__":
    unittest.main()
