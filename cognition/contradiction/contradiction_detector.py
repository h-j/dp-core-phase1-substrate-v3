import re
import json
from typing import List, Dict, Any, Optional, Set, Tuple
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
        "regime_secondary_conflict_score": 0.3
    }

    def __init__(self):
        pass

    def detect(
        self,
        current_theory: Any, # Assuming Theory object
        historical_theories: List[Any], # Assuming list of Theory objects
        validations: List[Any], # Not used in this specific structural detection, but part of interface
        reflections: List[Any], # Not used in this specific structural detection, but part of interface
        current_observation: Any, # Assuming MarketObservation object
        historical_observations: List[Any], # Not used in this specific structural detection, but part of interface
    ) -> Dict[str, Any]:
        """
        Detects contradictions and assigns a score.
        """
        contradictions = []
        total_score = 0.0
        pair_scores = []
        
        curr_data = self._parse_theory_summary(current_theory)
        curr_regime = getattr(current_theory, 'regime_subtype', 'neutral').lower()

        # Compare current theory with historical theories
        for hist_theory in historical_theories:
            hist_data = self._parse_theory_summary(hist_theory)
            hist_regime_subtype = getattr(hist_theory, 'regime_subtype', 'neutral').lower()

            lexical_conflict_score = 0.0
            structural_conflict_score = 0.0
            structural_indicators = []
            
            # A. Claim vs Claim (High Weight: 0.6)
            claim_score, claim_ind = self._compare_fields(curr_data["claim"], hist_data["claim"], weight=0.6)
            structural_conflict_score += claim_score
            structural_indicators.extend(claim_ind)

            # B. Falsified_if vs Falsified_if (High Weight: 0.6)
            fals_score, fals_ind = self._compare_fields(curr_data["falsified_if"], hist_data["falsified_if"], weight=0.6)
            structural_conflict_score += fals_score
            structural_indicators.extend(fals_ind)

            # C. Claim vs Branch (Medium Weight: 0.4)
            # Check if current claim contradicts historical branch scenarios
            cb_score, cb_ind = self._compare_fields(curr_data["claim"], hist_data["if_branch"], weight=0.4)
            structural_conflict_score += cb_score
            structural_indicators.extend(cb_ind)

            # D. Branch vs Branch (Low Weight: 0.2)
            # We mostly ignore "else" vs "else" unless they are polar opposites
            bb_score, bb_ind = self._compare_fields(curr_data["if_branch"], hist_data["if_branch"], weight=0.2)
            structural_conflict_score += bb_score
            structural_indicators.extend(bb_ind)

            # Legacy Keyword checks on the Claim only
            current_trend = self._extract_trend_keywords(curr_data["claim"], curr_regime)
            hist_trend = self._extract_trend_keywords(hist_data["claim"], hist_regime_subtype)

            # Compare 'else_branch' fields (medium weight)
            else_branch_conflict_score, else_branch_indicators = self._compare_fields(
                curr_data.get("else_branch", ""),
                hist_data.get("else_branch", ""),
                weight=0.2 # Medium weight
            )
            structural_conflict_score += else_branch_conflict_score
            structural_indicators.extend(else_branch_indicators)

            # --- Legacy Structural Conflict Detection (can be refined to use structured fields) ---
            # This section can be further refined to use the structured fields more directly.
            # For now, it operates on the general summary (claim) and regime subtype.
            current_trend_keywords = self._extract_trend_keywords(curr_data.get("claim", ""), curr_regime)
            hist_trend_keywords = self._extract_trend_keywords(hist_data.get("claim", ""), hist_regime_subtype)
            
            # Only add to structural_conflict_score if not already covered by field comparison
            if (any(k in current_trend_keywords for k in ["higher", "continuation"]) and any(k in hist_trend_keywords for k in ["lower", "rejection"])) or \
               (any(k in hist_trend_keywords for k in ["higher", "continuation"]) and any(k in current_trend_keywords for k in ["lower", "rejection"])):
                if "Trend: continuation vs rejection" not in structural_indicators: # Avoid double counting
                    structural_conflict_score += self.CONFIG["trend_conflict_score"]
                    structural_indicators.append("Trend: continuation vs rejection")

            # 2. Volatility Conflict (expansion vs stability/compression)
            current_vol_keywords = self._extract_volatility_keywords(curr_data.get("claim", ""), curr_regime)
            hist_vol_keywords = self._extract_volatility_keywords(hist_data.get("claim", ""), hist_regime_subtype)
            if (any(k in current_vol_keywords for k in ["expansion", "high"]) and any(k in hist_vol_keywords for k in ["compressed", "stable"])) or \
               (any(k in hist_vol_keywords for k in ["expansion", "high"]) and any(k in current_vol_keywords for k in ["compressed", "stable"])):
                structural_conflict_score += self.CONFIG["volatility_conflict_score"]
                structural_indicators.append("Volatility: expansion vs stability")

            # 3. Participation Conflict (weakening vs elevated)
            current_part_keywords = self._extract_participation_keywords(curr_data.get("claim", ""), curr_regime)
            hist_part_keywords = self._extract_participation_keywords(hist_data.get("claim", ""), hist_regime_subtype)
            if (any(k in current_part_keywords for k in ["weakening", "deteriorated"]) and any(k in hist_part_keywords for k in ["elevated", "strong"])) or \
               (any(k in hist_part_keywords for k in ["weakening", "deteriorated"]) and any(k in current_part_keywords for k in ["elevated", "strong"])):
                structural_conflict_score += self.CONFIG["participation_conflict_score"]
                structural_indicators.append("Participation: weakening vs elevated")

            # 4. Regime Subtype Conflict (direct contradiction between distinct regimes)
            if curr_regime != 'neutral' and hist_regime_subtype != 'neutral' and curr_regime != hist_regime_subtype:
                # Assign higher score for direct regime contradiction
                if (curr_regime == "expansion_confirmed" and hist_regime_subtype in ["pressure_loaded_range", "liquidity_constrained", "fatigue", "pressure_loaded"]) or \
                   (hist_regime_subtype == "expansion_confirmed" and curr_regime in ["pressure_loaded_range", "liquidity_constrained", "fatigue", "pressure_loaded"]):
                    structural_conflict_score += self.CONFIG["regime_direct_conflict_score"]
                    structural_indicators.append(f"Regime Subtype: {curr_regime} vs {hist_regime_subtype}")
                elif (curr_regime == "pressure_loaded_range" and hist_regime_subtype == "liquidity_constrained") or \
                     (hist_regime_subtype == "pressure_loaded_range" and curr_regime == "liquidity_constrained"):
                    structural_conflict_score += self.CONFIG["regime_secondary_conflict_score"]
                    structural_indicators.append(f"Regime Subtype: {curr_regime} vs {hist_regime_subtype}")

            if structural_indicators:
                contradictions.append(f"Structural: {'; '.join(structural_indicators)}")

            # Aggregate score for this pair
            pair_score = lexical_conflict_score + structural_conflict_score
            total_score += pair_score
            pair_scores.append(pair_score)

            # Debug print for each pair
            print(f"\n[CONTRADICTION MATCHES (Field-Aware)]")
            print(f"theory A (claim): {curr_data.get('claim', '')}")
            print(f"theory B (claim): {hist_data.get('claim', '')}")
            print(f"lexical conflict: {lexical_conflict_score:.3f}")
            print(f"structural conflict: {structural_conflict_score:.3f} ({'; '.join(structural_indicators)})")
            print(f"final score (pair): {pair_score:.3f}")

        # Normalize score (simple sum for now, can be refined)
        # If no historical theories, score is 0.0
        score_divisor = len(historical_theories) if historical_theories else 1
        
        max_score = max(pair_scores) if pair_scores else 0.0
        mean_score = total_score / score_divisor if score_divisor else 0.0
        normalized_score = min(
            1.0, 
            (self.CONFIG["max_score_weight"] * max_score) + (self.CONFIG["mean_score_weight"] * mean_score)
        )

        print(f"\n[CONTRADICTION SCORE]")
        print(f"pair_scores={[f'{s:.3f}' for s in pair_scores]}")
        print(f"max={max_score:.3f}")
        print(f"mean={mean_score:.3f}")
        print(f"final={normalized_score:.3f}")

        return {
            "score": normalized_score,
            "indicators": contradictions,
            "summary": f"Detected {len(contradictions)} contradictions with a total score of {normalized_score:.2f}.",
        }

    def _parse_theory_summary(self, theory: Any) -> Dict[str, str]:
        """Parses the theory summary (which should be JSON) into a dict."""
        # Prefer structured summary fields when available on the object
        # 1) If the object provides a structured summary attribute, use it
        structured = None
        # dict-like theory (e.g., snapshot) may contain 'theory_summary_structured'
        # v4.0: Specifically checking for 'mechanism' and 'forbidden_state'
        if isinstance(theory, dict):
            structured = theory.get("theory_summary_structured") or theory.get("summary_structured") or theory

        # object attribute (e.g., ORM model or Theory object)
        if structured is None:
            structured = getattr(theory, "summary_structured", None) or getattr(theory, "theory_summary_structured", None)

        # If structured is a JSON string, attempt to parse
        if isinstance(structured, str):
            try:
                parsed = json.loads(structured)
                if isinstance(parsed, dict):
                    # Coerce values to strings to prevent crashes in downstream text processing (e.g., if LLM returns nested dicts)
                    return {k: v if isinstance(v, str) else json.dumps(v) for k, v in {key: parsed.get(key, "") for key in ["mechanism", "claim", "falsified_if", "if_branch", "else_branch", "forbidden_state"]}.items()}
            except Exception:
                structured = None

        # If structured is already a dict-like object
        if isinstance(structured, dict):
            # Coerce values to strings
            return {k: v if isinstance(v, str) else json.dumps(v) for k, v in {key: structured.get(key, "") for key in ["claim", "falsified_if", "if_branch", "else_branch", "unless"]}.items()}

        # Otherwise, try parsing the free-text summary
        summary_text = getattr(theory, 'summary', getattr(theory, 'abstraction', ''))
        try:
            parsed = json.loads(summary_text)
            if isinstance(parsed, dict) and ("claim" in parsed or "falsified_if" in parsed):
                return {k: v if isinstance(v, str) else json.dumps(v) for k, v in {key: parsed.get(key, "") for key in ["claim", "falsified_if", "if_branch", "else_branch", "unless"]}.items()}
        except json.JSONDecodeError:
            pass # Not a JSON, fallback to old behavior

        # Fallback for old text-based theories or if JSON parsing fails
        return {"claim": summary_text, "falsified_if": "", "if_branch": "", "else_branch": "", "unless": ""}

    def _compare_fields(self, field_a: str, field_b: str, weight: float) -> Tuple[float, List[str]]:
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
            if (tokens_a & set_a and tokens_b & set_b) or (tokens_a & set_b and tokens_b & set_a):
                explicit_conflict = True
                indicators.append(f"Field conflict: {field_a[:30]} vs {field_b[:30]}")
                break
        
        # Score based on explicit conflict and inverse of similarity
        if explicit_conflict:
            score = weight * (1.0 - similarity) # Higher conflict if explicit and low similarity
        elif similarity < 0.3: # Low similarity without explicit conflict
            score = weight * 0.1 # Small penalty for very different claims

        return score, indicators

    def _extract_trend_keywords(self, summary: str, regime_subtype: str) -> List[str]:
        keywords = []
        directional = re.sub(
            r"\brejection\s+(high|low|level|upper|lower|zone)\b",
            "",
            summary,
        )
        if any(w in directional for w in ["continuation", "higher", "upward", "strengthening"]):
            keywords.append("continuation")
        if any(w in directional for w in ["lower", "downward", "downtrend", "reversal"]):
            keywords.append("rejection")
        if re.search(r"\brejection\b", directional):
            keywords.append("rejection")
        if any(w in summary for w in ["range_bound", "range", "persistence"]): # This line was the bug
            keywords.append("range_bound")
        
        # Infer from regime subtype
        if regime_subtype in ["expansion_confirmed"]:
            keywords.append("continuation")
        if regime_subtype in ["fatigue", "pressure_loaded_range", "pressure_loaded"]:
            keywords.append("rejection")
        
        return list(set(keywords)) # Return unique keywords

    def _extract_volatility_keywords(self, summary: str, regime_subtype: str) -> List[str]:
        keywords = []
        if "expansion" in summary or "expanded" in summary or "high volatility" in summary:
            keywords.append("expansion")
        if "compression" in summary or "compressed" in summary or "stability" in summary or "stable" in summary or "low volatility" in summary:
            keywords.append("compressed")
        
        # Infer from regime subtype
        if regime_subtype in ["expansion_confirmed"]:
            keywords.append("expansion")
        if regime_subtype in ["liquidity_constrained", "pressure_loaded_range"]:
            keywords.append("compressed")
        
        return list(set(keywords))

    def _extract_participation_keywords(self, summary: str, regime_subtype: str) -> List[str]:
        keywords = []
        if "weakening" in summary or "deteriorated" in summary or "weak" in summary or "low participation" in summary:
            keywords.append("weakening")
        if "elevated" in summary or "strong" in summary or "broad" in summary or "high participation" in summary:
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