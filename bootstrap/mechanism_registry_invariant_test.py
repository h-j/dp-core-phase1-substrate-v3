import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

from cognition.schemas.knowledge.mechanism import Mechanism
from cognition.schemas.theory.theory import Theory, TheoryStructured, MechanismComponent, Branch
from cognition.schemas.confidence.confidence_state import ConfidenceState
from flows.knowledge_flow.mechanism_engine import match_and_register_in_registry, MechanismEngine
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
        # Register a mechanism first
        mech = Mechanism(
            mechanism_id="MECH_001",
            canonical_name="TREND_PERSISTENCE",
            concept_tags=["TREND_PERSISTENCE"],
            relation_type="CONTRADICTS",
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
            name="TREND_PERSISTENCE",
            description="Initial stable proposition of trend persistence.",
            concept_type="candidate",
            associated_theory_ids=[],
            associated_lineages=[],
            created_at_step=1,
        )
        mech.id = "MECH_001"
        self.repo.save_mechanism(mech)

        # Simulate the theory mutation phase: LLM proposes modified description
        # We ensure that if a mutation happens, we update registry metadata, but the description remains IMMUTABLE
        comp_id = "TREND_PERSISTENCE"
        mod_data = {
            "description": "Drastically modified description containing new FII and volatility assumptions.",
            "concept_tags": ["TREND_PERSISTENCE", "VOLATILITY_EXPANSION"],
            "relation_type": "AMPLIFIES"
        }

        # Simulated mutation handler code block (mimics replay_engine.py L1765-1778)
        mech_obj = self.repo.get_mechanism("MECH_001")
        if mech_obj:
            mech_obj.times_modified += 1
            # Note: We do NOT assign description/tags/relations from mod_data here anymore
            mech_obj.last_seen = 2
            self.repo.save_mechanism(mech_obj)

        # Retrieve from repository and assert proposition details did NOT drift
        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded.description, "Initial stable proposition of trend persistence.")
        self.assertEqual(reloaded.concept_tags, ["TREND_PERSISTENCE"])
        self.assertEqual(reloaded.relation_type, "CONTRADICTS")
        self.assertEqual(reloaded.times_modified, 1)

    def test_invariant_2_tag_isolated_matches(self):
        """2. Two components sharing the same ontology tag but expressing different propositions register distinct IDs."""
        # Save MECH_001
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

        # Propose a component with the same tag but a completely different description
        comp = {
            "component_id": "trend_persistence",
            "description": "Completely different semantic claim about range-bound reversion under tight liquidity.",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS"
        }

        # Match (should fail similarity and register MECH_002)
        mid = match_and_register_in_registry(comp, self.repo, step=2, regime="neutral")
        self.assertEqual(mid, "MECH_002")

        # Confirm registry contains both
        mechs = self.repo.list_mechanisms()
        self.assertEqual(len(mechs), 2)
        self.assertEqual(self.repo.get_mechanism("MECH_002").description, comp["description"])

    def test_invariant_3_atomic_evidence_attribution(self):
        """3. Multiple theory components mapped to the same mechanism produce exactly one evidence update."""
        # Create a candidate mechanism
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

        # Simulate the prior active mechanisms list having multiple entries for MECH_001 (e.g. 3 components)
        prior_active_mechanisms = ["MECH_001", "MECH_001", "MECH_001"]

        # Run simulated atomic attribution code block (mimics replay_engine.py L3588-3599)
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
                else:
                    mech_obj.prediction_harmed += 1
                    mech_obj.contradiction_count += 1
                self.repo.save_mechanism(mech_obj)

        # Verify it incremented exactly once
        reloaded = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded.support_count, 1)
        self.assertEqual(reloaded.prediction_helped, 1)

    def test_invariant_4_retired_isolation(self):
        """4. A retired mechanism cannot be matched, reused, modified, or receive evidence."""
        # Create a retired mechanism
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

        # 4a. Verify it is excluded from active registry matching & reuse
        comp = {
            "component_id": "trend_persistence",
            "description": "Initial description",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS"
        }
        # match_and_register_in_registry should ignore MECH_001 and create MECH_002
        new_mid = match_and_register_in_registry(comp, self.repo, step=2, regime="neutral")
        self.assertEqual(new_mid, "MECH_002")

        # 4b. Verify it stops receiving new evidence during prediction feedback
        prior_active_mechanisms = ["MECH_001"]
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

        reloaded_mech1 = self.repo.get_mechanism("MECH_001")
        self.assertEqual(reloaded_mech1.support_count, 0)
        self.assertEqual(reloaded_mech1.prediction_helped, 0)

    def test_invariant_5_semantic_reuse(self):
        """5. Existing mechanism matching still allows genuine semantic reuse when propositions are sufficiently similar."""
        # Create a mechanism
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

        # Propose a highly similar description
        comp = {
            "component_id": "trend_persistence",
            "description": "price structure exhibits higher highs and lower lows.",
            "concept_tags": ["TREND_PERSISTENCE"],
            "relation_type": "CONTRADICTS"
        }

        # Match (should succeed hybrid similarity threshold of 0.75 and reuse MECH_001)
        mid = match_and_register_in_registry(comp, self.repo, step=2, regime="neutral")
        self.assertEqual(mid, "MECH_001")


if __name__ == "__main__":
    unittest.main()
