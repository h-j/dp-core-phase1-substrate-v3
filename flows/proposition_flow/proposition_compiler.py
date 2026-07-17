from typing import Optional, Tuple

import pandas as pd

from cognition.schemas.proposition.canonical_semantic_proposition import \
    CanonicalSemanticProposition
from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.theory.theory import Theory
from flows.proposition_flow.parameter_grounder import ParameterGrounder
from flows.proposition_flow.semantic_compiler import SemanticCompiler
from interfaces.ollama_client import OllamaClient


class MarketPropositionCompiler:
    """
    Coordinating Proposition Compiler (Phase 1.7)
    Bifurcated into SemanticCompiler (LLM stage) and ParameterGrounder (Code-based statistical stage).
    """

    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient(temperature=0.0, seed=42)
        self.semantic_compiler = SemanticCompiler(client=self.client)
        self.parameter_grounder = ParameterGrounder()

    def compile_theory(
        self, theory: Theory, step: int, history_df: Optional[pd.DataFrame] = None
    ) -> Tuple[CanonicalSemanticProposition, CompiledProposition]:
        """
        Runs two-stage compilation:
        1. Semantic Compiler translates raw Theory -> CanonicalSemanticProposition
        2. Parameter Grounder calculates deterministic variables -> CompiledProposition
        """
        # Stage 1: Semantic Compile (LLM-driven concept extraction)
        canonical_prop = self.semantic_compiler.compile(theory)

        # Stage 2: Parameter Grounding (Deterministic threshold grounding)
        compiled_prop = self.parameter_grounder.ground(canonical_prop, history_df, step)

        return canonical_prop, compiled_prop
