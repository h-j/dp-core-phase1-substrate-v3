import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

from cognition.contradiction.llm_contradiction_auditor import \
    LLMContradictionAuditor
from cognition.schemas.theory.theory import (  # Import Theory Pydantic model
    Branch, Theory, TheoryStructured)
from flows.reflection_flow.reflection_flow import ReflectionFlow


class ContradictionDetector:
    """
    Detects contradictions between current and historical theories,
    considering both lexical and structural tension.
    """

    CONFIG = {
        "max_score_weight": 0.7,
        "mean_score_weight": 0.3,
        "threshold_synthesis": 0.38,
        "lexical_weight_base": 0.15,
        "trend_conflict_score": 0.3,
        "range_persistence_score": 0.2,
        "volatility_conflict_score": 0.25,
        "participation_conflict_score": 0.2,
        "regime_direct_conflict_score": 0.4,
        "regime_secondary_conflict_score": 0.3,
    }

    def __init__(self, verbose: bool = False, debug: bool = False):
        self.llm_auditor = LLMContradictionAuditor()
        # debug gates all diagnostic output; verbose is kept for backward compat
        self.debug = debug or verbose
        self.verbose = self.debug

    def detect(
        self,
        current_theory: Any,  # Assuming Theory object
        historical_theories: List[Any],  # Assuming list of Theory objects
        validations: List[
            Any
        ],  # Not used in this specific structural detection, but part of interface
        reflections: List[
            Any
        ],  # Not used in this specific structural detection, but part of interface
        current_observation: Any = None,  # Assuming MarketObservation object
        historical_observations: List[
            Any
        ] = None,  # Not used in this specific structural detection, but part of interface
        skip_intra_lineage_similar: bool = True,
        intra_lineage_similarity_threshold: float = 0.85,
    ) -> Dict[str, Any]:
        """
        Detects contradictions and assigns a score.
        """
        contradictions = []
        llm_audits = []
        total_score = 0.0
        pair_scores = []

        curr_data = self._extract_structured_theory_fields(current_theory)
        curr_regime = getattr(current_theory, "regime_subtype", "neutral").lower()
        compared_count = 0

        # Compare current theory with historical theories
        for hist_theory in historical_theories:
            curr_id = getattr(current_theory, "id", None)
            hist_id = getattr(hist_theory, "id", None)
            if curr_id and hist_id and curr_id == hist_id:
                continue

            curr_lineage = getattr(current_theory, "lineage_id", None)
            hist_lineage = getattr(hist_theory, "lineage_id", None)
            if (
                skip_intra_lineage_similar
                and curr_lineage
                and hist_lineage
                and curr_lineage == hist_lineage
            ):
                curr_summary = getattr(current_theory, "summary", "")
                hist_summary = getattr(hist_theory, "summary", "")
                sem_sim = self._similarity(curr_summary, hist_summary)
                if sem_sim > intra_lineage_similarity_threshold:
                    continue

            compared_count += 1
            hist_data = self._extract_structured_theory_fields(hist_theory)
            hist_regime_subtype = getattr(
                hist_theory, "regime_subtype", "neutral"
            ).lower()

            lexical_conflict_score = 0.0
            structural_conflict_score = 0.0
            structural_indicators = []

            # A. Claim vs Claim (High Weight: 0.6)
            claim_score, claim_ind = self._compare_fields(
                curr_data["claim"],
                hist_data["claim"],
                weight=0.6 * self.CONFIG["lexical_weight_base"],
            )
            structural_conflict_score += claim_score
            structural_indicators.extend(claim_ind)

            # B. Falsified_if vs Falsified_if (High Weight: 0.6)
            fals_score, fals_ind = self._compare_fields(
                curr_data.get("falsified_if", ""),
                hist_data.get("falsified_if", ""),
                weight=0.6 * self.CONFIG["lexical_weight_base"],
            )
            structural_conflict_score += fals_score
            structural_indicators.extend(fals_ind)

            # C. Claim vs Branch (Medium Weight: 0.4)
            # Check if current claim contradicts historical branch scenarios
            cb_score, cb_ind = self._compare_fields(
                curr_data.get("claim", ""), hist_data.get("if_branch", ""), weight=0.4
            )
            structural_conflict_score += cb_score
            structural_indicators.extend(cb_ind)

            # D. Branch vs Branch (Low Weight: 0.2)
            # We mostly ignore "else" vs "else" unless they are polar opposites
            bb_score, bb_ind = self._compare_fields(
                curr_data.get("if_branch", ""),
                hist_data.get("if_branch", ""),
                weight=0.2,
            )
            structural_conflict_score += bb_score
            structural_indicators.extend(bb_ind)

            # Legacy Keyword checks on the Claim only
            current_trend = self._extract_trend_keywords(
                curr_data["claim"], curr_regime
            )
            hist_trend = self._extract_trend_keywords(
                hist_data["claim"], hist_regime_subtype
            )

            # Compare 'else_branch' fields (medium weight)
            else_branch_conflict_score, else_branch_indicators = self._compare_fields(
                curr_data.get("else_branch", ""),
                hist_data.get("else_branch", ""),
                weight=0.2,  # Medium weight
            )
            structural_conflict_score += else_branch_conflict_score
            structural_indicators.extend(else_branch_indicators)

            # --- Legacy Structural Conflict Detection (can be refined to use structured fields) ---
            # This section can be further refined to use the structured fields more directly.
            # For now, it operates on the general summary (claim) and regime subtype.
            current_trend_keywords = self._extract_trend_keywords(
                curr_data.get("claim", ""), curr_regime
            )
            hist_trend_keywords = self._extract_trend_keywords(
                hist_data.get("claim", ""), hist_regime_subtype
            )

            # Only add to structural_conflict_score if not already covered by field comparison
            if (
                any(k in current_trend_keywords for k in ["higher", "continuation"])
                and any(k in hist_trend_keywords for k in ["lower", "rejection"])
            ) or (
                any(k in hist_trend_keywords for k in ["higher", "continuation"])
                and any(k in current_trend_keywords for k in ["lower", "rejection"])
            ):
                if (
                    "Trend: continuation vs rejection" not in structural_indicators
                ):  # Avoid double counting
                    structural_conflict_score += self.CONFIG["trend_conflict_score"]
                    structural_indicators.append("Trend: continuation vs rejection")

            # 2. Volatility Conflict (expansion vs stability/compression)
            current_vol_keywords = self._extract_volatility_keywords(
                curr_data.get("claim", ""), curr_regime
            )
            hist_vol_keywords = self._extract_volatility_keywords(
                hist_data.get("claim", ""), hist_regime_subtype
            )
            if (
                any(k in current_vol_keywords for k in ["expansion", "high"])
                and any(k in hist_vol_keywords for k in ["compressed", "stable"])
            ) or (
                any(k in hist_vol_keywords for k in ["expansion", "high"])
                and any(k in current_vol_keywords for k in ["compressed", "stable"])
            ):
                structural_conflict_score += self.CONFIG["volatility_conflict_score"]
                structural_indicators.append("Volatility: expansion vs stability")

            # 3. Participation Conflict (weakening vs elevated)
            current_part_keywords = self._extract_participation_keywords(
                curr_data.get("claim", ""), curr_regime
            )
            hist_part_keywords = self._extract_participation_keywords(
                hist_data.get("claim", ""), hist_regime_subtype
            )
            if (
                any(k in current_part_keywords for k in ["weakening", "deteriorated"])
                and any(k in hist_part_keywords for k in ["elevated", "strong"])
            ) or (
                any(k in hist_part_keywords for k in ["weakening", "deteriorated"])
                and any(k in current_part_keywords for k in ["elevated", "strong"])
            ):
                structural_conflict_score += self.CONFIG["participation_conflict_score"]
                structural_indicators.append("Participation: weakening vs elevated")

            # 4. Regime Subtype Conflict (direct contradiction between distinct regimes)
            if (
                curr_regime != "neutral"
                and hist_regime_subtype != "neutral"
                and curr_regime != hist_regime_subtype
            ):
                # Assign higher score for direct regime contradiction
                if (
                    curr_regime == "expansion_confirmed"
                    and hist_regime_subtype
                    in [
                        "pressure_loaded_range",
                        "liquidity_constrained",
                        "fatigue",
                        "pressure_loaded",
                    ]
                ) or (
                    hist_regime_subtype == "expansion_confirmed"
                    and curr_regime
                    in [
                        "pressure_loaded_range",
                        "liquidity_constrained",
                        "fatigue",
                        "pressure_loaded",
                    ]
                ):
                    structural_conflict_score += self.CONFIG[
                        "regime_direct_conflict_score"
                    ]
                    structural_indicators.append(
                        f"Regime Subtype: {curr_regime} vs {hist_regime_subtype}"
                    )
                elif (
                    curr_regime == "pressure_loaded_range"
                    and hist_regime_subtype == "liquidity_constrained"
                ) or (
                    hist_regime_subtype == "pressure_loaded_range"
                    and curr_regime == "liquidity_constrained"
                ):
                    structural_conflict_score += self.CONFIG[
                        "regime_secondary_conflict_score"
                    ]
                    structural_indicators.append(
                        f"Regime Subtype: {curr_regime} vs {hist_regime_subtype}"
                    )

            # E. Grounded Ontology Semantic Contradiction Check
            curr_struct = getattr(current_theory, "summary_structured", None)
            hist_struct = getattr(hist_theory, "summary_structured", None)
            if isinstance(current_theory, dict):
                curr_struct = current_theory.get("summary_structured")
            if isinstance(hist_theory, dict):
                hist_struct = hist_theory.get("summary_structured")

            if curr_struct and hist_struct:
                curr_comps = getattr(curr_struct, "mechanism_components", []) or []
                hist_comps = getattr(hist_struct, "mechanism_components", []) or []
                if isinstance(curr_struct, dict):
                    curr_comps = curr_struct.get("mechanism_components") or []
                if isinstance(hist_struct, dict):
                    hist_comps = hist_struct.get("mechanism_components") or []

                for curr_comp in curr_comps:
                    for hist_comp in hist_comps:
                        curr_tags = []
                        hist_tags = []
                        curr_rel = None
                        hist_rel = None

                        if isinstance(curr_comp, dict):
                            curr_tags = curr_comp.get("concept_tags") or []
                            curr_rel = curr_comp.get("relation_type")
                        else:
                            curr_tags = getattr(curr_comp, "concept_tags", []) or []
                            curr_rel = getattr(curr_comp, "relation_type", None)

                        if isinstance(hist_comp, dict):
                            hist_tags = hist_comp.get("concept_tags") or []
                            hist_rel = hist_comp.get("relation_type")
                        else:
                            hist_tags = getattr(hist_comp, "concept_tags", []) or []
                            hist_rel = getattr(hist_comp, "relation_type", None)

                        common_tags = set(curr_tags) & set(hist_tags)
                        if common_tags:
                            is_contradicting_rel = False
                            if curr_rel and hist_rel and curr_rel != hist_rel:
                                if {curr_rel, hist_rel} == {"AMPLIFIES", "DAMPENS"}:
                                    is_contradicting_rel = True
                                elif {curr_rel, hist_rel} == {
                                    "CONTRADICTS",
                                    "CO-OCCURS_WITH",
                                }:
                                    is_contradicting_rel = True

                            if is_contradicting_rel:
                                for tag in common_tags:
                                    structural_conflict_score += 0.4
                                    structural_indicators.append(
                                        f"Semantic Contradiction: Concept '{tag}' relation is '{curr_rel}' in current theory but '{hist_rel}' in historical theory."
                                    )

            if structural_indicators:
                contradictions.append(f"Structural: {'; '.join(structural_indicators)}")

            # Phase 2: Parallel LLM Audit (Optimized: disabled to avoid redundant LLM calls during replay)
            audit = {
                "relationship": "unknown",
                "confidence": 0.0,
                "reasoning": "Optimized: LLM contradiction audit bypassed during replay.",
            }
            llm_audits.append(
                {"theory_id": getattr(hist_theory, "id", "unknown"), "audit": audit}
            )

            # Aggregate score for this pair
            pair_score = lexical_conflict_score + structural_conflict_score
            total_score += pair_score
            pair_scores.append(pair_score)

            # Debug logging for each pair
            if self.debug:
                logger.debug(
                    "[ContradictionDetector] pair: A=%r B=%r lexical=%.3f structural=%.3f score=%.3f indicators=%s",
                    curr_data.get('claim', '')[:80],
                    hist_data.get('claim', '')[:80],
                    lexical_conflict_score,
                    structural_conflict_score,
                    pair_score,
                    '; '.join(structural_indicators)
                )

        # Normalize score (simple sum for now, can be refined)
        # If no historical theories, score is 0.0
        score_divisor = compared_count if compared_count else 1

        max_score = max(pair_scores) if pair_scores else 0.0
        mean_score = total_score / score_divisor if compared_count else 0.0
        normalized_score = min(
            1.0,
            (self.CONFIG["max_score_weight"] * max_score)
            + (self.CONFIG["mean_score_weight"] * mean_score),
        )

        if self.debug:
            logger.debug(
                "[ContradictionDetector] final: pair_scores=%s max=%.3f mean=%.3f normalized=%.3f",
                [f'{s:.3f}' for s in pair_scores], max_score, mean_score, normalized_score
            )

        return {
            "score": normalized_score,
            "indicators": contradictions,
            "llm_contradiction_audit": llm_audits,
            "summary": f"Detected {len(contradictions)} contradictions with a total score of {normalized_score:.2f}.",
        }

    def _extract_structured_theory_fields(self, theory: Theory) -> Dict[str, str]:
        """
        Extracts relevant fields from a Theory object's summary_structured for comparison.
        Ensures all fields are strings for consistent text processing.
        """
        structured = theory.summary_structured
        if not structured:
            return {
                "mechanism": "unknown",
                "claim": theory.summary,
                "if_branch": "unknown",
                "else_branch": "unknown",
                "unless": "unknown",
                "falsified_if": "unknown",
                "forbidden_state": "unknown",
            }

        return {
            "mechanism": structured.mechanism if structured.mechanism else "",
            "claim": structured.claim,
            "if_branch": f"{structured.if_branch.condition}: {structured.if_branch.action}",
            "else_branch": f"{structured.else_branch.condition}: {structured.else_branch.action}",
            "unless": structured.unless if structured.unless else "",
            "falsified_if": structured.falsified_if,
            "forbidden_state": (
                structured.forbidden_state if structured.forbidden_state else ""
            ),
        }

    def _compare_fields(
        self, field_a: str, field_b: str, weight: float
    ) -> Tuple[float, List[str]]:
        """Compares two fields for contradiction and returns score and indicators."""
        score = 0.0
        indicators = []

        # Tokenize and normalize
        tokens_a = self._token_set(field_a)
        tokens_b = self._token_set(field_b)

        # Simple lexical overlap (similarity) - high similarity means less contradiction
        similarity = self._similarity(field_a, field_b)

        # Check for explicit opposing keywords (e.g., continuation vs rejection)
        opposing_pairs = [
            ({"continuation", "higher"}, {"rejection", "lower"}),
            ({"expansion", "expanding"}, {"compression", "compressed"}),
            ({"strengthening", "strong"}, {"weakening", "weak"}),
            ({"support"}, {"resistance"}),
        ]

        explicit_conflict = False
        for set_a, set_b in opposing_pairs:
            if (tokens_a & set_a and tokens_b & set_b) or (
                tokens_a & set_b and tokens_b & set_a
            ):
                explicit_conflict = True
                indicators.append(f"Field conflict: {field_a[:30]} vs {field_b[:30]}")
                break

        # Score based on explicit conflict and inverse of similarity
        if explicit_conflict:
            score = weight * (
                1.0 - similarity
            )  # Higher conflict if explicit and low similarity
        elif similarity < 0.3:  # Low similarity without explicit conflict
            score = weight * 0.1  # Small penalty for very different claims
            indicators.append(
                f"Low semantic similarity: {field_a[:20]}... vs {field_b[:20]}..."
            )

        return score, indicators

    def _extract_trend_keywords(self, summary: str, regime_subtype: str) -> List[str]:
        keywords = []
        directional = re.sub(
            r"\brejection\s+(high|low|level|upper|lower|zone)\b",
            "",
            summary,
        )
        if any(
            w in directional
            for w in ["continuation", "higher", "upward", "strengthening"]
        ):
            keywords.append("continuation")
        if any(
            w in directional for w in ["lower", "downward", "downtrend", "reversal"]
        ):
            keywords.append("rejection")
        if re.search(r"\brejection\b", directional):
            keywords.append("rejection")
        if any(
            w in summary for w in ["range_bound", "range", "persistence"]
        ):  # This line was the bug
            keywords.append("range_bound")

        # Infer from regime subtype
        if regime_subtype in ["expansion_confirmed"]:
            keywords.append("continuation")
        if regime_subtype in ["fatigue", "pressure_loaded_range", "pressure_loaded"]:
            keywords.append("rejection")

        return list(set(keywords))  # Return unique keywords

    def _extract_volatility_keywords(
        self, summary: str, regime_subtype: str
    ) -> List[str]:
        keywords = []
        if (
            "expansion" in summary
            or "expanded" in summary
            or "high volatility" in summary
        ):
            keywords.append("expansion")
        if (
            "compression" in summary
            or "compressed" in summary
            or "stability" in summary
            or "stable" in summary
            or "low volatility" in summary
        ):
            keywords.append("compressed")

        # Infer from regime subtype
        if regime_subtype in ["expansion_confirmed"]:
            keywords.append("expansion")
        if regime_subtype in ["liquidity_constrained", "pressure_loaded_range"]:
            keywords.append("compressed")

        return list(set(keywords))

    def _extract_participation_keywords(
        self, summary: str, regime_subtype: str
    ) -> List[str]:
        keywords = []
        if (
            "weakening" in summary
            or "deteriorated" in summary
            or "weak" in summary
            or "low participation" in summary
        ):
            keywords.append("weakening")
        if (
            "elevated" in summary
            or "strong" in summary
            or "broad" in summary
            or "high participation" in summary
        ):
            keywords.append("elevated")

        # Infer from regime subtype
        if regime_subtype in ["liquidity_constrained", "fatigue", "pressure_loaded"]:
            keywords.append("weakening")
        if regime_subtype in ["expansion_confirmed"]:
            keywords.append("elevated")

        return list(set(keywords))

    def _token_set(self, text: str) -> Set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _similarity(self, a: str, b: str) -> float:
        a_tokens = self._token_set(a)
        b_tokens = self._token_set(b)
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)
