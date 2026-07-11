from typing import Any, Dict, List


class MLCCompetitionEngine:
    @staticmethod
    def select_best_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compares multiple sibling candidates pairwise based on:
        1. prospective adequacy/coverage compliance
        2. absolute comparative effect (lift) on validation data
        3. complexity cost (as a tie-breaker)
        
        Returns the winning candidate dict.
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty.")
            
        if len(candidates) == 1:
            return candidates[0]
            
        best = candidates[0]
        
        for current in candidates[1:]:
            best = MLCCompetitionEngine._compare_pair(best, current)
            
        return best

    @staticmethod
    def _compare_pair(c1: Dict[str, Any], c2: Dict[str, Any]) -> Dict[str, Any]:
        p1 = c1["proposition"]
        p2 = c2["proposition"]
        
        res1 = c1["prospective_res"]
        res2 = c2["prospective_res"]
        
        # 1. Compare compliance (adequacy and coverage)
        # PASS is preferred over FAIL
        score1 = 0
        score2 = 0
        
        if res1.get("prospective_adequacy") == "PASS":
            score1 += 1
        if res1.get("prospective_coverage") == "PASS":
            score1 += 1
            
        if res2.get("prospective_adequacy") == "PASS":
            score2 += 1
        if res2.get("prospective_coverage") == "PASS":
            score2 += 1
            
        if score1 > score2:
            return c1
        elif score2 > score1:
            return c2
            
        # 2. Compare signed lift in expected direction
        dir1 = p1.get("expected_direction", 1.0)
        dir2 = p2.get("expected_direction", 1.0)
        lift1 = res1.get("comparative_effect", 0.0) * dir1
        lift2 = res2.get("comparative_effect", 0.0) * dir2
        
        if lift1 > lift2:
            return c1
        elif lift2 > lift1:
            return c2
            
        # 3. Compare complexity cost (lower is simpler/better)
        cost1 = p1.get("complexity_cost", 1.0)
        cost2 = p2.get("complexity_cost", 1.0)
        
        if cost1 < cost2:
            return c1
        elif cost2 < cost1:
            return c2
            
        # Default tie-breaker: return first
        return c1
