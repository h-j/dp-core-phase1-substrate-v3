import json
import re
from typing import List, Dict, Optional
from cognition.schemas.theory.theory import Theory # Import Theory Pydantic model
from interfaces.ollama_client import OllamaClient

class DialecticalTheorySynthesizer:
    """
    Synthesizes conflicting active theories into a narrow, grounded thesis.
    """
    def __init__(self):
        self.client = OllamaClient()

    def synthesize(
        self,
        observation_text: str, # Assuming TheoryRecord has a 'theory' attribute that holds the Theory object
        active_theories: List[Any],
        contradiction_indicators: List[str],
        regime_subtype: str,
        falsifiability_conditions: List[str]
    ) -> Optional[Dict[str, str]]:
        """
        Performs dialectical synthesis of conflicting theories.
        """
        # Access the underlying Theory object from TheoryRecord
        theory_texts = "\n".join([f"- {t.theory.summary_structured.claim if t.theory.summary_structured else t.theory.summary}" for t in active_theories])
        indicators = "; ".join(contradiction_indicators)
        falsifiability = "\n".join([f"- {c}" for c in falsifiability_conditions])

        prompt = f"""
Observation:
{observation_text}

Active Theories:
{theory_texts}

Detected Contradictions:
{indicators}

Regime Subtype: {regime_subtype}

Primary Falsifiability Conditions:
{falsifiability}

The system has detected a material conflict between these active theories. 
Perform a dialectical synthesis to reconcile them into a narrow, falsifiable claim.

Return exactly a JSON object conforming to this schema:
```json
{{
"shared_premise": "string",
"conflict": "string",
"synthesis": "string",
"falsified_if": "string"
}}
```

JSON Fields:
- `shared_premise`: 1 sentence on agreement.
- `conflict`: 1 sentence on the specific disagreement.
- `synthesis`: 2-4 sentences of reconciled reasoning.
- `falsified_if`: 1 sentence explicit boundary.

Constraints:
- 2-4 sentences for the Synthesis section specifically.
- No generic filler ("it is interesting that", "further confirmation").
- Grounded strictly in the provided observation.
- Avoid causal certainty.
- No markdown.
"""
        self._last_prompt = prompt
        result = self.client.generate(prompt)
        synthesis = self._parse_synthesis(result)
        
        # Phase 3: Synthesis Validation
        if synthesis:
            validation = self._validate_synthesis(synthesis, theory_texts)
            synthesis["validation"] = validation
            if not validation.get("valid", True):
                print(f"[Synthesis Validation Warning] {validation.get('issues')}")
        
        return synthesis

    def _validate_synthesis(self, synthesis: Dict, original_theories: str) -> Dict:
        """Checks synthesis for internal consistency and faithfulness."""
        prompt = f"""
        Original Theories:
        {original_theories}

        Proposed Synthesis:
        {json.dumps(synthesis)}

        Audit this synthesis. Is it coherent? Does it hallucinate mechanisms not present or implied by parents?
        Return JSON: {{"valid": bool, "quality": 0.0-1.0, "issues": []}}
        """
        audit_raw = self.client.generate(prompt)
        try:
            return json.loads(audit_raw.strip().replace('```json', '').replace('```', ''))
        except Exception:
            return {"valid": True, "quality": 0.5, "issues": ["Validation parse failed"]}

    def _parse_synthesis(self, text: str) -> Optional[Dict[str, str]]:
        """Parses the structured JSON output into a dictionary, with retry."""
        parsed_data = None
        # Clean common LLM garbage before parsing
        # Robust JSON extraction: find first { and last }
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        cleaned_text_for_parse = ""
        if json_start != -1 and json_end != -1 and json_end > json_start:
            cleaned_text_for_parse = text[json_start : json_end + 1]
            # Strip markdown if present within the extracted string
            cleaned_text_for_parse = cleaned_text_for_parse.replace('```json', '').replace('```', '').strip()
        else:
            print(f"[Synthesis JSON Parse Error] No valid JSON structure found in raw output: {text[:200]}...")

        for _ in range(2): 
            try:
                parsed_data = json.loads(cleaned_text_for_parse)
                break
            except json.JSONDecodeError:
                print(f"[Synthesis JSON Parse Error] Retrying generation...")
                new_text = self.client.generate(self._last_prompt)
                # Re-extract JSON from the new text
                json_start = new_text.find('{')
                json_end = new_text.rfind('}')
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    cleaned_text_for_parse = new_text[json_start : json_end + 1]
                    cleaned_text_for_parse = cleaned_text_for_parse.replace('```json', '').replace('```', '').strip()
                else:
                    cleaned_text_for_parse = "" # No JSON found in retry
        
        if not parsed_data:
            print(f"[Synthesis JSON Parse Error] Failed after retry, falling back to regex: {text[:100]}...")
            # Fallback to old regex parsing if JSON is invalid after retry
            return self._parse_synthesis_fallback(text)

        # Validate schema
        required_fields = ["shared_premise", "conflict", "synthesis", "falsified_if"]
        if all(field in parsed_data for field in required_fields):
            return {k: v.strip() if isinstance(v, str) else v for k, v in parsed_data.items()}
        else:
            print(f"[Synthesis JSON Schema Error] Invalid schema, falling back to regex: {parsed_data}")
            return self._parse_synthesis_fallback(text)

    def _parse_synthesis_fallback(self, text: str) -> Optional[Dict[str, str]]:
        """Fallback to regex parsing for synthesis if JSON fails."""
        try:
            field = r"(?=\s*(?:Shared premise|Conflict|Synthesis|Falsified if):|\Z)" # Original robust regex
            shared = re.search(r"Shared premise:\s*(.*?)" + field, text, re.I | re.S)
            conflict = re.search(r"Conflict:\s*(.*?)" + field, text, re.I | re.S)
            synthesis = re.search(r"Synthesis:\s*(.*?)" + field, text, re.I | re.S)
            falsified = re.search(r"Falsified if:\s*(.*?)" + field, text, re.I | re.S)

            if shared and conflict and synthesis and falsified:
                return {
                    "shared_premise": shared.group(1).strip(),
                    "conflict": conflict.group(1).strip(),
                    "synthesis": synthesis.group(1).strip(),
                    "falsified_if": falsified.group(1).strip()
                }
            # If regex also fails, try line-based fallback
            lines = [l for l in text.splitlines() if l.strip()]
            if len(lines) >= 4:
                return {
                    "shared_premise": lines[0],
                    "conflict": lines[1],
                        "synthesis": lines[2],
                        "falsified_if": lines[3]
                }
            return None
        except Exception:
            return None

    @staticmethod
    def format_for_reflection(data: Dict[str, str]) -> str:
        """Formats the synthesis dict into a block for ReflectionFlow."""
        if not data:
            return ""
        return (
            f"Shared Premise: {data.get('shared_premise')}\n"
            f"Conflict: {data.get('conflict')}\n"
            f"Synthesis: {data.get('synthesis')}\n"
            f"Boundary: {data.get('falsified_if')}"
        )

    @staticmethod
    def format_for_theory(data: Dict[str, str]) -> str:
        """Formats the synthesis dict into an advisory block for TheoryGenerationFlow."""
        if not data:
            return ""
        return (
            f"Shared premise: {data.get('shared_premise')}\n"
            f"Resolved conflict: {data.get('conflict')}\n"
            f"Synthesis: {data.get('synthesis')}\n"
            f"Boundary retained: {data.get('falsified_if')}" # Use 'falsified_if' field
        )

    _last_prompt: str = "" # Store last prompt for retry