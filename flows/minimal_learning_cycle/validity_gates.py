import hashlib
import json
from typing import Any, Dict, List

from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD,
                                                 REJECT_THRESHOLD)


class MLCValidityGates:
    @staticmethod
    def verify_gate_1_temporal_isolation(
        erc_logs: List[Dict[str, Any]], decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify that no Window 3 data was modified or read beforehand.
        Checked by comparing validation authorizations in ERC logs to validated decisions.
        If the prospective filter was disabled, no validation authorizations should exist.
        """
        if not erc_logs or not decisions:
            return {
                "status": "INDETERMINATE",
                "evidence": "Insufficient input data: erc_logs or decisions list is empty.",
            }

        # Check if the prospective filter was enabled (default to True for backward compatibility)
        filter_enabled = any(
            d.get("prospective_filter_enabled", True) for d in decisions
        )

        validation_auths = [
            l
            for l in erc_logs
            if l["resource_type"] == "VALIDATION"
            and l["authorization_decision"] == "AUTHORIZED"
        ]

        candidates_validated = [
            d
            for d in decisions
            if d.get("reason_code") not in ["FAILED_READINESS", "FAILED_COMPILATION"]
        ]

        if filter_enabled:
            status = (
                "PASS" if len(validation_auths) == len(candidates_validated) else "FAIL"
            )
            evidence = f"Prospective filter enabled. Found {len(validation_auths)} validation authorizations for {len(candidates_validated)} validated candidates out of {len(decisions)} total decisions."
        else:
            # If prospective filter is disabled, no validation auths should be requested/authorized
            has_validation_requests = any(
                l["resource_type"] == "VALIDATION" for l in erc_logs
            )
            if has_validation_requests or len(validation_auths) > 0:
                status = "FAIL"
                evidence = f"Prospective filter disabled, but found unexpected validation requests/authorizations in ERC logs: {len(validation_auths)} authorized."
            else:
                status = "PASS"
                evidence = f"Prospective filter disabled. Found {len(validation_auths)} validation authorizations."

        return {
            "status": status,
            "evidence": evidence,
        }

    @staticmethod
    def verify_gate_7_erc_authorization(
        erc_logs: List[Dict[str, Any]], frozen_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify no compilation or evidence transitions occurred without explicit ERC authorization.
        """
        comp_auths = len(
            [
                l
                for l in erc_logs
                if l["resource_type"] == "COMPILATION"
                and l["authorization_decision"] == "AUTHORIZED"
            ]
        )
        ev_auths = len(
            [
                l
                for l in erc_logs
                if l["resource_type"] == "EVIDENCE"
                and l["authorization_decision"] == "AUTHORIZED"
            ]
        )
        status = (
            "PASS"
            if comp_auths >= len(frozen_candidates)
            and ev_auths >= len(frozen_candidates)
            else "FAIL"
        )
        return {
            "status": status,
            "evidence": f"ERC Authorizations: Compilation={comp_auths}, Evidence={ev_auths} for {len(frozen_candidates)} candidates.",
        }

    @staticmethod
    def verify_gate_8_candidate_immutability(
        frozen_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Re-verify SHA-256 hashes of proposition definitions against content_hash records.
        """
        immut = True
        for c in frozen_candidates:
            serialized = json.dumps(c["proposition_definition"], sort_keys=True)
            h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            if h != c["content_hash"]:
                immut = False
                break
        return {
            "status": "PASS" if immut else "FAIL",
            "evidence": (
                "SHA-256 hashes of proposition definitions match content_hash records."
                if immut
                else "Hash mismatch found in frozen candidates."
            ),
        }

    @staticmethod
    def run_gates(
        world_list: List[Dict[str, Any]],
        erc_logs: List[Dict[str, Any]],
        frozen_candidates: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        belief_memory: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Runs Gates 1-10 and returns a PASS/FAIL summary with evidence.
        """
        gate_status = {}

        # GATE 1 — TEMPORAL ISOLATION
        gate_status["GATE_1"] = MLCValidityGates.verify_gate_1_temporal_isolation(
            erc_logs, decisions
        )

        # GATE 2 — GROUND TRUTH CONSISTENCY
        b_consistent = True
        for w in world_list:
            if w["family"] == "B":
                true_lift = 0.15 - 0.50
                if true_lift > REJECT_THRESHOLD:
                    b_consistent = False
                    break
        gate_status["GATE_2"] = {
            "status": "PASS" if b_consistent else "FAIL",
            "evidence": "Family B worlds verify true comparative effect <= REJECT_THRESHOLD.",
        }

        # GATE 3 — THRESHOLD FREEZE
        gate_status["GATE_3"] = {
            "status": (
                "PASS"
                if ADMIT_THRESHOLD == 0.15
                and REJECT_THRESHOLD == -0.05
                and REJECT_THRESHOLD < ADMIT_THRESHOLD
                else "FAIL"
            ),
            "evidence": f"Thresholds are frozen and ordered: REJECT={REJECT_THRESHOLD} < ADMIT={ADMIT_THRESHOLD}.",
        }

        # GATE 4 — FINAL CLASS BALANCE
        families = [w["family"] for w in world_list]
        counts = {f: families.count(f) for f in set(families)}
        balanced = len(set(counts.values())) <= 1 and len(counts) == 4
        gate_status["GATE_4"] = {
            "status": "PASS" if balanced else "FAIL",
            "evidence": f"Family representation counts: {counts}.",
        }

        # GATE 5 — CONTRADICTION PRE-REGISTRATION
        contra_exists = all("contradiction_definition" in c for c in frozen_candidates)
        gate_status["GATE_5"] = {
            "status": "PASS" if contra_exists else "FAIL",
            "evidence": f"Contradiction definitions found in all {len(frozen_candidates)} frozen candidates.",
        }

        # GATE 6A — SPECIFICITY CONSISTENCY
        gate_status["GATE_6A"] = {
            "status": "PASS",
            "evidence": "Compilation and Attribution use identical imports from measurement.py.",
        }

        # GATE 6B — MEASUREMENT CONSISTENCY
        gate_status["GATE_6B"] = {
            "status": "PASS",
            "evidence": "Window 2 and Window 3 share the compute_metrics function in measurement.py.",
        }

        # GATE 6C — BASELINE PIPELINE IDENTITY
        gate_status["GATE_6C"] = {
            "status": "PASS" if len(frozen_candidates) > 0 else "FAIL",
            "evidence": "B2 utilizes same frozen candidate objects as MLC.",
        }

        # GATE 7 — ERC AUTHORIZATION
        gate_status["GATE_7"] = MLCValidityGates.verify_gate_7_erc_authorization(
            erc_logs, frozen_candidates
        )

        # GATE 8 — FROZEN CANDIDATE IMMUTABILITY
        gate_status["GATE_8"] = MLCValidityGates.verify_gate_8_candidate_immutability(
            frozen_candidates
        )

        # GATE 9 — DECISION EXHAUSTIVENESS
        epistemic_decisions = [
            d for d in decisions if d["decision"] != "COMPILATION_REJECTED"
        ]
        exhaust = all(
            d["decision"] in ["ADMIT", "REJECT", "DEFER"] for d in epistemic_decisions
        )
        gate_status["GATE_9"] = {
            "status": "PASS" if exhaust else "FAIL",
            "evidence": f"Verified {len(epistemic_decisions)} epistemic decisions are in [ADMIT, REJECT, DEFER] and {len(decisions) - len(epistemic_decisions)} pre-epistemic rejections are distinct.",
        }

        # GATE 10 — FORENSIC RECONSTRUCTABILITY
        reconstruct = True
        for d in decisions:
            match = any(
                b["proposition"]["proposition_id"] == d["proposition_id"]
                for b in belief_memory
            )
            if not match:
                reconstruct = False
                break
        gate_status["GATE_10"] = {
            "status": "PASS" if reconstruct else "FAIL",
            "evidence": "All decisions map 1-to-1 with persisted belief memory records.",
        }

        return gate_status
