import time
from typing import Any, Dict, List, Tuple

from flows.minimal_learning_cycle.baselines import (B1AlwaysAdmit,
                                                    B2RetrospectiveOnly,
                                                    B3MatchedRandom)
from flows.minimal_learning_cycle.belief_memory import MLCBeliefMemory
from flows.minimal_learning_cycle.candidate_freeze import MLCCandidateFreeze
from flows.minimal_learning_cycle.decision import MLCDecision
from flows.minimal_learning_cycle.erc import ERCController
from flows.minimal_learning_cycle.evidence_ledger import EvidenceLedger
from flows.minimal_learning_cycle.measurement import MLCMeasurement
from flows.minimal_learning_cycle.oracle import B4Oracle
from flows.minimal_learning_cycle.prospective_validation import \
    MLCProspectiveValidation
from flows.minimal_learning_cycle.readiness import MLCReadiness
from flows.minimal_learning_cycle.schemas import (LifecycleState,
                                                  PropositionSchema,
                                                  validate_state_transition)
from flows.minimal_learning_cycle.competition import MLCCompetitionEngine


class MLCExperimentRunner:
    def __init__(self):
        self.erc = ERCController()
        self.ledger = EvidenceLedger()
        self.belief_memory = MLCBeliefMemory()

        # In-memory tracking of all stages for artifacts
        self.world_registry: List[Dict[str, Any]] = []
        self.ground_truth: List[Dict[str, Any]] = []
        self.propositions: List[Dict[str, Any]] = []
        self.intrinsic_measurements: List[Dict[str, Any]] = []
        self.frozen_candidates: List[Dict[str, Any]] = []
        self.prospective_measurements: List[Dict[str, Any]] = []
        self.decisions: List[Dict[str, Any]] = []
        self.baseline_results: Dict[str, Any] = {
            "b1_decisions": {},
            "b2_decisions": {},
            "b3_decisions": {},
            "b4_decisions": {},
        }

    def run_lifecycle(self, world: Dict[str, Any]) -> Dict[str, Any]:
        world_id = f"WORLD_{world['family']}_SEED_{world['seed']}"
        self.world_registry.append(
            {"world_id": world_id, "family": world["family"], "seed": world["seed"]}
        )

        ground_truth_record = {
            "world_id": world_id,
            "expected_decision": world["expected_decision"],
            "expected_reason": world["expected_reason"],
        }
        self.ground_truth.append(ground_truth_record)

        prop_id = f"PROP_{world_id}"

        # HYPOTHESIS compilation stage
        prop = {
            "proposition_id": prop_id,
            "source_hypothesis_id": f"HYP_{world_id}",
            "trigger_definition": {
                "field": world["trigger_var"],
                "operator": "==",
                "value": 1,
                "lag": 0,
            },
            "target_definition": {
                "field": "outcome",
                "operator": "==",
                "value": world["outcome_map"]["Y0"],
            },
            "scope_definition": [],
            "expected_direction": 1.0,
            "contradiction_definition": {
                "field": "outcome",
                "operator": "==",
                "value": world["outcome_map"]["Y1"],
            },
            "specificity_definition": {"type": "deterministic"},
            "complexity_cost": 1.0,
            "generation_source": "deterministic_compilation",
            "creation_timestamp": time.time(),
            "lifecycle_state": LifecycleState.HYPOTHESIS,
        }

        # Verify schema validation
        assert PropositionSchema.validate(prop)

        lifecycle_history = [LifecycleState.HYPOTHESIS]

        # Architectural Invariant Check: verify compilation validity BEFORE transition to COMPILED_CANDIDATE
        if not MLCMeasurement.verify_proposition_compilation(prop):
            validate_state_transition(
                prop["lifecycle_state"], LifecycleState.COMPILATION_REJECTED
            )
            prop["lifecycle_state"] = LifecycleState.COMPILATION_REJECTED
            lifecycle_history.append(LifecycleState.COMPILATION_REJECTED)

            decision_dict = {
                "decision": "COMPILATION_REJECTED",
                "reason_code": "FAILED_COMPILATION",
                "measured_effect": 0.0,
                "thresholds": {},
                "adequacy_status": "FAIL",
                "coverage_status": "FAIL",
                "proposition_id": prop_id,
                "world_id": world_id,
                "timestamp": time.time(),
            }
            self.decisions.append(decision_dict)
            self.propositions.append(prop)

            # Baselines for early compilation failure
            self.baseline_results["b1_decisions"][world_id] = (
                B1AlwaysAdmit.make_decision(prop_id, world_id)["decision"]
            )
            self.baseline_results["b2_decisions"][world_id] = "COMPILATION_REJECTED"
            self.baseline_results["b3_decisions"][world_id] = (
                B3MatchedRandom.make_decision(prop_id, world_id, world["seed"])[
                    "decision"
                ]
            )
            self.baseline_results["b4_decisions"][world_id] = B4Oracle.make_decision(
                prop_id, world_id, ground_truth_record
            )["decision"]

            # Save to Belief Memory for early deferred
            erc_refs = [
                l["request_id"] for l in self.erc.logs if l["proposition_id"] == prop_id
            ]
            ledger_refs = [
                l["ledger_entry_id"]
                for l in self.ledger.get_records()
                if l["proposition_id"] == prop_id
            ]
            self.belief_memory.store_record(
                prop,
                lifecycle_history,
                {
                    "active_count": 0,
                    "active_target_count": 0,
                    "control_count": 0,
                    "control_target_count": 0,
                },
                {
                    "candidate_effect": 0.0,
                    "control_effect": 0.0,
                    "comparative_effect": 0.0,
                    "prospective_adequacy": "FAIL",
                    "prospective_coverage": "FAIL",
                },
                decision_dict,
                ground_truth_record,
                erc_refs,
                ledger_refs,
            )
            return decision_dict

        # 1. ERC Compilation Authorization Check
        comp_authorized = self.erc.check_and_deduct("COMPILATION", prop_id, 10)
        if not comp_authorized:
            raise RuntimeError(f"Compilation budget check failed for {prop_id}")

        validate_state_transition(
            prop["lifecycle_state"], LifecycleState.COMPILED_CANDIDATE
        )
        prop["lifecycle_state"] = LifecycleState.COMPILED_CANDIDATE
        lifecycle_history.append(LifecycleState.COMPILED_CANDIDATE)

        # 2. ERC Evidence Budget Check
        ev_authorized = self.erc.check_and_deduct("EVIDENCE", prop_id, 20)
        if not ev_authorized:
            raise RuntimeError(f"Evidence budget check failed for {prop_id}")

        validate_state_transition(
            prop["lifecycle_state"], LifecycleState.EVIDENCE_ACCUMULATING
        )
        prop["lifecycle_state"] = LifecycleState.EVIDENCE_ACCUMULATING
        lifecycle_history.append(LifecycleState.EVIDENCE_ACCUMULATING)

        # Populate Evidence Attribution and ledger for Window 2
        active_count = 0
        active_target_count = 0
        control_count = 0
        control_target_count = 0

        for exp in world["window_2"]:
            attr = MLCMeasurement.attribute_experience(
                prop, exp, world["window_2"], "WINDOW_2", world["experiences"]
            )
            self.ledger.append(attr)

            # Count target rates in active vs control for B2 retrospective
            if attr["trigger_activated"]:
                active_count += 1
                if attr["attribution_class"] == "SUPPORT":
                    active_target_count += 1
            else:
                control_count += 1
                if exp["outcome"] == prop["target_definition"]["value"]:
                    control_target_count += 1

        window_2_summary = {
            "active_count": active_count,
            "active_target_count": active_target_count,
            "control_count": control_count,
            "control_target_count": control_target_count,
        }

        # Intrinsic Measurement
        intrinsic_metrics = MLCMeasurement.compute_metrics(
            prop, world["window_2"], "WINDOW_2", world["experiences"]
        )
        self.intrinsic_measurements.append(
            {"proposition_id": prop_id, **intrinsic_metrics}
        )

        # Evaluation Readiness Check
        ready, reason = MLCReadiness.check_readiness(prop, intrinsic_metrics)
        if not ready:
            # Transition directly to DEFERRED
            validate_state_transition(
                prop["lifecycle_state"], LifecycleState.EVALUATION_READY
            )
            validate_state_transition(
                LifecycleState.EVALUATION_READY,
                LifecycleState.FROZEN_EVALUATION_CANDIDATE,
            )
            validate_state_transition(
                LifecycleState.FROZEN_EVALUATION_CANDIDATE,
                LifecycleState.PROSPECTIVELY_EVALUATED,
            )
            validate_state_transition(
                LifecycleState.PROSPECTIVELY_EVALUATED,
                LifecycleState.DEFERRED_PROPOSITION,
            )

            prop["lifecycle_state"] = LifecycleState.DEFERRED_PROPOSITION
            lifecycle_history.extend(
                [
                    LifecycleState.EVALUATION_READY,
                    LifecycleState.FROZEN_EVALUATION_CANDIDATE,
                    LifecycleState.PROSPECTIVELY_EVALUATED,
                    LifecycleState.DEFERRED_PROPOSITION,
                ]
            )
            decision_dict = {
                "decision": "DEFER",
                "reason_code": "FAILED_READINESS",
                "measured_effect": 0.0,
                "thresholds": {},
                "adequacy_status": "FAIL" if "ADEQUACY" in reason else "PASS",
                "coverage_status": "FAIL" if "COVERAGE" in reason else "PASS",
                "proposition_id": prop_id,
                "world_id": world_id,
                "timestamp": time.time(),
            }
            # Audit defer origin classification for early exit
            defer_class = MLCDecision.classify_defer_origin(
                decision_dict, ground_truth_record
            )
            decision_dict["defer_origin_classification"] = defer_class

            self.decisions.append(decision_dict)
            self.propositions.append(prop)

            # Baselines for early readiness failure
            self.baseline_results["b1_decisions"][world_id] = (
                B1AlwaysAdmit.make_decision(prop_id, world_id)["decision"]
            )
            self.baseline_results["b2_decisions"][world_id] = "DEFER"
            self.baseline_results["b3_decisions"][world_id] = (
                B3MatchedRandom.make_decision(prop_id, world_id, world["seed"])[
                    "decision"
                ]
            )
            self.baseline_results["b4_decisions"][world_id] = B4Oracle.make_decision(
                prop_id, world_id, ground_truth_record
            )["decision"]

            # Save to Belief Memory for early deferred
            erc_refs = [
                l["request_id"] for l in self.erc.logs if l["proposition_id"] == prop_id
            ]
            ledger_refs = [
                l["ledger_entry_id"]
                for l in self.ledger.get_records()
                if l["proposition_id"] == prop_id
            ]
            self.belief_memory.store_record(
                prop,
                lifecycle_history,
                window_2_summary,
                {
                    "candidate_effect": 0.0,
                    "control_effect": 0.0,
                    "comparative_effect": 0.0,
                    "prospective_adequacy": "FAIL",
                    "prospective_coverage": "FAIL",
                },
                decision_dict,
                ground_truth_record,
                erc_refs,
                ledger_refs,
            )

            return decision_dict

        validate_state_transition(
            prop["lifecycle_state"], LifecycleState.EVALUATION_READY
        )
        prop["lifecycle_state"] = LifecycleState.EVALUATION_READY
        lifecycle_history.append(LifecycleState.EVALUATION_READY)

        # Freeze Candidate
        frozen = MLCCandidateFreeze.freeze(prop, intrinsic_metrics, window_2_summary)
        self.frozen_candidates.append(frozen)

        validate_state_transition(
            prop["lifecycle_state"], LifecycleState.FROZEN_EVALUATION_CANDIDATE
        )
        prop["lifecycle_state"] = LifecycleState.FROZEN_EVALUATION_CANDIDATE
        lifecycle_history.append(LifecycleState.FROZEN_EVALUATION_CANDIDATE)

        # 3. ERC Validation Check
        val_authorized = self.erc.check_and_deduct("VALIDATION", prop_id, 30)
        if not val_authorized:
            raise RuntimeError(f"Validation budget check failed for {prop_id}")

        validate_state_transition(
            prop["lifecycle_state"], LifecycleState.PROSPECTIVELY_EVALUATED
        )
        prop["lifecycle_state"] = LifecycleState.PROSPECTIVELY_EVALUATED
        lifecycle_history.append(LifecycleState.PROSPECTIVELY_EVALUATED)

        # Unseal Window 3 data now that prospective validation is authorized
        if hasattr(world.get("window_3"), "unseal"):
            world["window_3"].unseal()

        # SEALED/UNSEALED Window 3 access logic
        # Populate ledger for Window 3 experiences
        for exp in world["window_3"]:
            attr = MLCMeasurement.attribute_experience(
                prop, exp, world["window_3"], "WINDOW_3", world["experiences"]
            )
            self.ledger.append(attr)

        # Prospective comparative evaluation
        prospective_res = MLCProspectiveValidation.evaluate(
            prop, world["window_3"], world["experiences"]
        )
        self.prospective_measurements.append(
            {"proposition_id": prop_id, **prospective_res}
        )

        # Decision
        decision_dict = MLCDecision.make_decision(prop_id, world_id, prospective_res)

        # Final state transition
        sys_dec = decision_dict["decision"]
        if sys_dec == "ADMIT":
            target_state = LifecycleState.ADMITTED_BELIEF
        elif sys_dec == "REJECT":
            target_state = LifecycleState.REJECTED_PROPOSITION
        else:
            target_state = LifecycleState.DEFERRED_PROPOSITION

        validate_state_transition(prop["lifecycle_state"], target_state)
        prop["lifecycle_state"] = target_state
        lifecycle_history.append(target_state)

        # Audit defer origin classification
        defer_class = MLCDecision.classify_defer_origin(
            decision_dict, ground_truth_record
        )
        decision_dict["defer_origin_classification"] = defer_class

        self.decisions.append(decision_dict)
        self.propositions.append(prop)

        # Save to Belief Memory
        # Extract ERC and ledger logs references
        erc_refs = [
            l["request_id"] for l in self.erc.logs if l["proposition_id"] == prop_id
        ]
        ledger_refs = [
            l["ledger_entry_id"]
            for l in self.ledger.get_records()
            if l["proposition_id"] == prop_id
        ]

        self.belief_memory.store_record(
            prop,
            lifecycle_history,
            window_2_summary,
            prospective_res,
            decision_dict,
            ground_truth_record,
            erc_refs,
            ledger_refs,
        )

        # Baselines
        self.baseline_results["b1_decisions"][world_id] = B1AlwaysAdmit.make_decision(
            prop_id, world_id
        )["decision"]
        self.baseline_results["b2_decisions"][world_id] = (
            B2RetrospectiveOnly.make_decision(prop_id, world_id, frozen)["decision"]
        )
        self.baseline_results["b3_decisions"][world_id] = B3MatchedRandom.make_decision(
            prop_id, world_id, world["seed"]
        )["decision"]
        self.baseline_results["b4_decisions"][world_id] = B4Oracle.make_decision(
            prop_id, world_id, ground_truth_record
        )["decision"]

        return decision_dict

    def run_lifecycle_with_competition(
        self,
        world: Dict[str, Any],
        num_confounders: int = 2,
        enable_prospective_filter: bool = True,
        enable_learning: bool = False,
        bypass_pruning: bool = False,
        sham_trigger: str = None,
    ) -> Dict[str, Any]:
        """
        Runs the learning cycle with multiple sibling candidates (one correct, and multiple confounding)
        and executes the MLCCompetitionEngine to select the winning candidate based on retrospective (Window 2) metrics.
        The winner is then evaluated prospectively on Window 3 if enable_prospective_filter is True.
        """
        from uuid import uuid4
        from flows.minimal_learning_cycle.config import MIN_COVERAGE
        alternative_group_id = str(uuid4())
        
        world_id = f"WORLD_{world['family']}_SEED_{world['seed']}"
        self.world_registry.append(
            {"world_id": world_id, "family": world["family"], "seed": world["seed"]}
        )

        ground_truth_record = {
            "world_id": world_id,
            "expected_decision": world["expected_decision"],
            "expected_reason": world["expected_reason"],
        }
        self.ground_truth.append(ground_truth_record)

        # Retrieval logic
        rejected_triggers = []
        if enable_learning:
            if sham_trigger:
                rejected_triggers = [sham_trigger]
            else:
                rejected_triggers = self.belief_memory.get_rejected_or_retired_triggers()

        # 1. Compile Candidates
        candidates = []
        
        # Primary candidate (correct, using trigger_var F_0)
        prop1_id = f"PROP_{world_id}_c1"
        prop1 = {
            "proposition_id": prop1_id,
            "source_hypothesis_id": f"HYP_{world_id}_c1",
            "trigger_definition": {
                "field": world["trigger_var"],
                "operator": "==",
                "value": 1,
                "lag": 0,
            },
            "target_definition": {
                "field": "outcome",
                "operator": "==",
                "value": world["outcome_map"]["Y0"],
            },
            "scope_definition": [],
            "expected_direction": 1.0,
            "contradiction_definition": {
                "field": "outcome",
                "operator": "==",
                "value": world["outcome_map"]["Y1"],
            },
            "specificity_definition": {"type": "deterministic"},
            "complexity_cost": 1.0,
            "generation_source": "deterministic_compilation",
            "creation_timestamp": time.time(),
            "lifecycle_state": LifecycleState.HYPOTHESIS,
            "alternative_group_id": alternative_group_id,
        }
        
        primary_pruned = False
        if enable_learning and world["trigger_var"] in rejected_triggers and not bypass_pruning:
            if not hasattr(self, "learning_audit_log"):
                self.learning_audit_log = []
            self.learning_audit_log.append({
                "proposition_id": prop1_id,
                "trigger_field": world["trigger_var"],
                "action": "PRUNED",
                "reason": "PAST_REJECTION"
            })
            primary_pruned = True

        if not primary_pruned:
            candidates.append(prop1)
        
        # Confounding candidates (using non-causal VAR fields)
        f_map = world["feature_map"]
        # Find all available non-causal features
        non_causal_keys = [f"F_{i}" for i in range(1, 10) if f_map.get(f"F_{i}") != world["trigger_var"]]
        
        for idx in range(min(num_confounders, len(non_causal_keys))):
            confounding_var = f_map[non_causal_keys[idx]]
            
            if enable_learning and confounding_var in rejected_triggers and not bypass_pruning:
                if not hasattr(self, "learning_audit_log"):
                    self.learning_audit_log = []
                self.learning_audit_log.append({
                    "proposition_id": f"PROP_{world_id}_c{idx+2}",
                    "trigger_field": confounding_var,
                    "action": "PRUNED",
                    "reason": "PAST_REJECTION"
                })
                continue

            prop_id = f"PROP_{world_id}_c{idx+2}"
            prop = {
                "proposition_id": prop_id,
                "source_hypothesis_id": f"HYP_{world_id}_c{idx+2}",
                "trigger_definition": {
                    "field": confounding_var,
                    "operator": "==",
                    "value": 1,
                    "lag": 0,
                },
                "target_definition": {
                    "field": "outcome",
                    "operator": "==",
                    "value": world["outcome_map"]["Y0"],
                },
                "scope_definition": [],
                "expected_direction": 1.0,
                "contradiction_definition": {
                    "field": "outcome",
                    "operator": "==",
                    "value": world["outcome_map"]["Y1"],
                },
                "specificity_definition": {"type": "deterministic"},
                # Slightly higher complexity to test tie-breaker if lift is identical
                "complexity_cost": 1.1 + (idx * 0.1),
                "generation_source": "deterministic_compilation",
                "creation_timestamp": time.time(),
                "lifecycle_state": LifecycleState.HYPOTHESIS,
                "alternative_group_id": alternative_group_id,
            }
            candidates.append(prop)
            
        # 2. Run compilation and evidence gathering (Window 2) for all candidates
        compiled_candidates = []
        for prop in candidates:
            p_id = prop["proposition_id"]
            lifecycle_history = [LifecycleState.HYPOTHESIS]
            
            # Verify compilation
            if not MLCMeasurement.verify_proposition_compilation(prop):
                continue
                
            # Debit compilation resource
            comp_authorized = self.erc.check_and_deduct("COMPILATION", p_id, 10)
            if not comp_authorized:
                raise RuntimeError(f"Compilation budget check failed for {p_id}")
                
            prop["lifecycle_state"] = LifecycleState.COMPILED_CANDIDATE
            lifecycle_history.append(LifecycleState.COMPILED_CANDIDATE)
            
            # Debit evidence resource
            ev_authorized = self.erc.check_and_deduct("EVIDENCE", p_id, 20)
            if not ev_authorized:
                raise RuntimeError(f"Evidence budget check failed for {p_id}")
                
            prop["lifecycle_state"] = LifecycleState.EVIDENCE_ACCUMULATING
            lifecycle_history.append(LifecycleState.EVIDENCE_ACCUMULATING)
            
            # Attribute experiences for Window 2
            active_count = 0
            active_target_count = 0
            control_count = 0
            control_target_count = 0
            
            for exp in world["window_2"]:
                attr = MLCMeasurement.attribute_experience(
                    prop, exp, world["window_2"], "WINDOW_2", world["experiences"]
                )
                self.ledger.append(attr)
                
                if attr["trigger_activated"]:
                    active_count += 1
                    if attr["attribution_class"] == "SUPPORT":
                        active_target_count += 1
                else:
                    control_count += 1
                    if exp["outcome"] == prop["target_definition"]["value"]:
                        control_target_count += 1
                        
            window_2_summary = {
                "active_count": active_count,
                "active_target_count": active_target_count,
                "control_count": control_count,
                "control_target_count": control_target_count,
            }
            
            intrinsic_metrics = MLCMeasurement.compute_metrics(
                prop, world["window_2"], "WINDOW_2", world["experiences"]
            )
            # Calculate retrospective comparative effect on Window 2
            a_pct = (window_2_summary["active_target_count"] / window_2_summary["active_count"]) if window_2_summary["active_count"] > 0 else 0.50
            c_pct = (window_2_summary["control_target_count"] / window_2_summary["control_count"]) if window_2_summary["control_count"] > 0 else 0.50
            retro_effect = a_pct - c_pct
            intrinsic_metrics["comparative_effect"] = retro_effect
            
            self.intrinsic_measurements.append(
                {"proposition_id": p_id, **intrinsic_metrics}
            )
            
            ready, reason = MLCReadiness.check_readiness(prop, intrinsic_metrics)
            if not ready:
                prop["lifecycle_state"] = LifecycleState.DEFERRED_PROPOSITION
                continue
                
            prop["lifecycle_state"] = LifecycleState.EVALUATION_READY
            lifecycle_history.append(LifecycleState.EVALUATION_READY)
            
            frozen = MLCCandidateFreeze.freeze(prop, intrinsic_metrics, window_2_summary)
            if prop is prop1:
                self.frozen_candidates.append(frozen)
                
            prop["lifecycle_state"] = LifecycleState.FROZEN_EVALUATION_CANDIDATE
            lifecycle_history.append(LifecycleState.FROZEN_EVALUATION_CANDIDATE)
            
            # Construct retrospective results for selection comparator
            retrospective_res = {
                "comparative_effect": retro_effect,
                "prospective_adequacy": "PASS" if intrinsic_metrics.get("sample_adequacy") else "FAIL",
                "prospective_coverage": "PASS" if intrinsic_metrics.get("coverage", 0.0) >= MIN_COVERAGE else "FAIL",
            }
            
            compiled_candidates.append({
                "proposition": prop,
                "prospective_res": retrospective_res,
                "lifecycle_history": lifecycle_history,
                "window_2_summary": window_2_summary,
                "frozen": frozen,
            })
            
        if not compiled_candidates:
            raise RuntimeError("No candidates survived compilation/readiness.")
            
        # 3. Retrospective Selection
        winner_data = MLCCompetitionEngine.select_best_candidate(compiled_candidates)
        winner_prop = winner_data["proposition"]
        winner_id = winner_prop["proposition_id"]
        
        # 4. Evaluation and Decision
        if enable_prospective_filter:
            # Debit validation resource (only for the selected winner!)
            val_authorized = self.erc.check_and_deduct("VALIDATION", winner_id, 30)
            if not val_authorized:
                raise RuntimeError(f"Validation budget check failed for {winner_id}")
                
            winner_prop["lifecycle_state"] = LifecycleState.PROSPECTIVELY_EVALUATED
            winner_data["lifecycle_history"].append(LifecycleState.PROSPECTIVELY_EVALUATED)
            
            # Unseal Window 3
            if hasattr(world.get("window_3"), "unseal"):
                world["window_3"].unseal()
                
            for exp in world["window_3"]:
                attr = MLCMeasurement.attribute_experience(
                    winner_prop, exp, world["window_3"], "WINDOW_3", world["experiences"]
                )
                self.ledger.append(attr)
                
            prospective_res = MLCProspectiveValidation.evaluate(
                winner_prop, world["window_3"], world["experiences"]
            )
            self.prospective_measurements.append(
                {"proposition_id": winner_id, **prospective_res}
            )
            
            decision_dict = MLCDecision.make_decision(winner_id, world_id, prospective_res)
        else:
            # Retrospective Decision (Condition B: No prospective validation)
            winner_prop["lifecycle_state"] = LifecycleState.PROSPECTIVELY_EVALUATED
            winner_data["lifecycle_history"].append(LifecycleState.PROSPECTIVELY_EVALUATED)
            
            retrospective_res = winner_data["prospective_res"]
            decision_dict = MLCDecision.make_decision(winner_id, world_id, retrospective_res)
            
            # Run prospective validation silently to measure true performance (without affecting decision)
            if hasattr(world.get("window_3"), "unseal"):
                world["window_3"].unseal()
            prospective_res = MLCProspectiveValidation.evaluate(
                winner_prop, world["window_3"], world["experiences"]
            )
            self.prospective_measurements.append(
                {"proposition_id": winner_id, **prospective_res}
            )
            
        sys_dec = decision_dict["decision"]
        if sys_dec == "ADMIT":
            target_state = LifecycleState.ADMITTED_BELIEF
        elif sys_dec == "REJECT":
            target_state = LifecycleState.REJECTED_PROPOSITION
        else:
            target_state = LifecycleState.DEFERRED_PROPOSITION
            
        validate_state_transition(winner_prop["lifecycle_state"], target_state)
        winner_prop["lifecycle_state"] = target_state
        winner_data["lifecycle_history"].append(target_state)
        
        defer_class = MLCDecision.classify_defer_origin(
            decision_dict, ground_truth_record
        )
        decision_dict["defer_origin_classification"] = defer_class
        
        self.decisions.append(decision_dict)
        self.propositions.append(winner_prop)
        
        erc_refs = [
            l["request_id"] for l in self.erc.logs if l["proposition_id"] == winner_id
        ]
        ledger_refs = [
            l["ledger_entry_id"]
            for l in self.ledger.get_records()
            if l["proposition_id"] == winner_id
        ]
        
        self.belief_memory.store_record(
            winner_prop,
            winner_data["lifecycle_history"],
            winner_data["window_2_summary"],
            prospective_res,
            decision_dict,
            ground_truth_record,
            erc_refs,
            ledger_refs,
        )
        
        return decision_dict

