# Example Strategic Cognition Outputs for Testing

EXAMPLE_STRATEGIC_OUTPUTS = [
    {
        "posture": "confident",
        "coherence_trajectory": "strengthening",
        "summary": (
            "Recent cognition shows strong theoretical coherence (0.78) "
            "with manageable contradiction pressure (0.15). "
            "Liquidity-led momentum continuation theories are strengthening. "
            "Broad market participation supports theoretical expectations."
        ),
        "contradictions": [],
        "weakening_assumptions": [
            "Regime-specific assumptions show slight deterioration under volatility"
        ],
        "regime": (
            "Stable regime with broad participation. "
            "Theories developed under similar conditions remain valid."
        ),
    },
    {
        "posture": "cautiously_coherent",
        "coherence_trajectory": "stable",
        "summary": (
            "Coherence maintaining at 0.72 despite emerging contradiction pressure (0.28). "
            "Trend continuation theories remain supported. "
            "Breadth weakness creates interpretive tension."
        ),
        "contradictions": [
            "Price strength vs weak breadth (2 occurrences)",
            "Index momentum vs declining participation",
        ],
        "weakening_assumptions": [
            "Broad-based participation assumption weakening (45% failure rate)"
        ],
        "regime": (
            "Transitional regime with selective strength. "
            "Index performance masking underlying dispersion."
        ),
    },
    {
        "posture": "adaptive",
        "coherence_trajectory": "weakening",
        "summary": (
            "Coherence declining from 0.75 to 0.62 (Δ-0.13). "
            "Contradiction pressure rising (0.38). "
            "Market outcomes frequently diverge from liquidity-led theories. "
            "Adaptive interpretation frameworks engaged."
        ),
        "contradictions": [
            "Liquidity concentration vs participation weakness (3 occurrences)",
            "Momentum persistence vs volatility expansion (4 occurrences)",
            "Trend reversal zones (recurring)",
        ],
        "weakening_assumptions": [
            "Liquidity-led momentum (58% failure under vol spike)",
            "Trend persistence (52% failure rate)",
            "Breadth support assumption (51% failure)",
        ],
        "regime": (
            "Volatile, dispersed regime destabilizing momentum theories. "
            "Regime-sensitive confidence weighting required."
        ),
    },
    {
        "posture": "contradicted",
        "coherence_trajectory": "deteriorating",
        "summary": (
            "Coherence collapsed to 0.38 with high contradiction pressure (0.68). "
            "Multiple theories simultaneously failing. "
            "Market structure diverged significantly from theoretical expectations. "
            "High interpretive caution warranted."
        ),
        "contradictions": [
            "Price strength vs weak breadth (dominant pattern)",
            "Liquidity fragmentation despite index moves",
            "Volatility expansion breaking momentum assumptions",
            "Regime shift from trend to range-bound",
        ],
        "weakening_assumptions": [
            "Trend continuation (72% failure rate)",
            "Liquidity support for momentum (68% failure)",
            "Broad participation (75% failure)",
            "Volatility compression (critical failure)",
        ],
        "regime": (
            "Major regime transition. "
            "Previous theoretical framework boundaries exceeded. "
            "New regime requires new interpretive structures."
        ),
    },
    {
        "posture": "uncertain",
        "coherence_trajectory": "volatile",
        "summary": (
            "Coherence oscillating (0.45-0.68) indicating framework instability. "
            "Contradiction pressure fluctuating (0.25-0.55). "
            "Theory survival highly regime-dependent. "
            "Adaptive cognition in flux."
        ),
        "contradictions": [
            "Regime sensitivity creating interpretation ambiguity",
            "Theory success/failure ratio highly time-dependent",
        ],
        "weakening_assumptions": [
            "Regime-invariant theory assumptions (highest uncertainty)"
        ],
        "regime": (
            "Uncertain regime classification. "
            "Multiple theoretical frameworks partially applicable. "
            "Requires continuous re-evaluation."
        ),
    },
    {
        "posture": "confident",
        "coherence_trajectory": "strengthening",
        "summary": (
            "Market outcomes strongly validating breadth-led theories. "
            "Coherence rising from 0.68 to 0.81 (Δ+0.13). "
            "Contradiction pressure declining (0.12). "
            "Broad participation supporting price continuation."
        ),
        "contradictions": [],
        "weakening_assumptions": [],
        "regime": (
            "Broad participation regime. "
            "All-sector market strength. "
            "Theories well-grounded in current market structure."
        ),
    },
    {
        "posture": "adaptive",
        "coherence_trajectory": "weakening",
        "summary": (
            "Liquidity-led momentum theories show region-specific weakness. "
            "Coherence at 0.65 with moderate pressure (0.32). "
            "Performance diverging in selected sectors. "
            "Regime-conditional confidence adaptation ongoing."
        ),
        "contradictions": [
            "Liquidity concentration in large caps (2 occurrences)",
            "Mid-cap weakness despite index strength",
        ],
        "weakening_assumptions": [
            "Index-wide liquidity assumptions (sector-specific failure)",
            "Uniform participation assumption (40% failure rate)",
        ],
        "regime": (
            "Selective leadership regime. "
            "Large cap-led moves. "
            "Mid-cap theories require separate regime treatment."
        ),
    },
    {
        "posture": "cautiously_coherent",
        "coherence_trajectory": "stable",
        "summary": (
            "Theory validation mixed with emerging contradictions. "
            "Coherence stable at 0.58 with rising pressure (0.35). "
            "Contradictions accumulating but not yet dominant. "
            "Framework integrity maintained with caution."
        ),
        "contradictions": [
            "Volatility expansion (2 recent occurrences)",
            "Divergence widening (recurring pattern)",
        ],
        "weakening_assumptions": [
            "Volatility compression assumption (emerging weakness)"
        ],
        "regime": (
            "Transitional volatility regime. "
            "Calm period ending. "
            "Increased adaptability required going forward."
        ),
    },
    {
        "posture": "contradicted",
        "coherence_trajectory": "deteriorating",
        "summary": (
            "Volatility spike broke momentum theories. "
            "Coherence collapsed (0.32) with extreme pressure (0.76). "
            "Theory failures cascading. "
            "Fundamental regime change indicated."
        ),
        "contradictions": [
            "Momentum persistence (dominant failure)",
            "Liquidity support failed",
            "Price strength without breadth (critical zone)",
            "Trend reversal zone active",
        ],
        "weakening_assumptions": [
            "All momentum-based theories (>80% failure)",
            "Liquidity support (critical failure)",
            "Trend continuation (universal failure)",
        ],
        "regime": (
            "Volatility shock regime. "
            "Previous frameworks invalidated. "
            "Emergency regime adaptation required."
        ),
    },
    {
        "posture": "adaptive",
        "coherence_trajectory": "weakening",
        "summary": (
            "Recovery theories show mixed results. "
            "Coherence moderate at 0.51 with pressure (0.42). "
            "Breadth divergence restricting strength validation. "
            "Regime instability requiring adaptive frameworks."
        ),
        "contradictions": [
            "Price recovery vs weak breadth support",
            "Liquidity recovery without participation recovery",
        ],
        "weakening_assumptions": [
            "V-shaped recovery assumption (53% failure)",
            "Symmetrical market structure assumption",
        ],
        "regime": (
            "Recovery uncertainty regime. "
            "Asymmetric market healing. "
            "Divergent sector strength patterns."
        ),
    },
    {
        "posture": "confident",
        "coherence_trajectory": "strengthening",
        "summary": (
            "Validation momentum building across theories. "
            "Coherence rising to 0.79 with pressure declining (0.18). "
            "Consistency of theory support increasing. "
            "Market structure aligning with framework."
        ),
        "contradictions": [],
        "weakening_assumptions": [],
        "regime": (
            "Confirmed trend regime. "
            "Market validation across multiple theory dimensions. "
            "Framework integrity high."
        ),
    },
    {
        "posture": "uncertain",
        "coherence_trajectory": "volatile",
        "summary": (
            "Regime classification ambiguous. "
            "Coherence oscillating (0.48-0.65). "
            "Different theories succeeding in different sub-periods. "
            "Framework requirements changing rapidly."
        ),
        "contradictions": ["Temporal inconsistency in validation patterns"],
        "weakening_assumptions": ["Regime-invariant theory structure"],
        "regime": (
            "Multi-regime period. "
            "Daily/hourly switches between behavioral patterns. "
            "Highest interpretive uncertainty."
        ),
    },
    {
        "posture": "cautiously_coherent",
        "coherence_trajectory": "stable",
        "summary": (
            "Fragile coherence maintained at 0.62 with pressure (0.28). "
            "Multiple contradictions present but contained. "
            "Theory framework holding but stressed. "
            "Continued observation required."
        ),
        "contradictions": [
            "Price strength vs weak participation (2 occurrences)",
            "Liquidity concentration patterns",
        ],
        "weakening_assumptions": [
            "Broad market assumptions (partial failure)",
            "Uniform sector behavior (56% failure rate)",
        ],
        "regime": (
            "Stressed but stable regime. "
            "Market structure testing framework boundaries. "
            "Near potential regime transition."
        ),
    },
    {
        "posture": "adaptive",
        "coherence_trajectory": "improving",
        "summary": (
            "Adaptive frameworks proving effective. "
            "Coherence recovering from 0.52 to 0.68 (Δ+0.16). "
            "Pressure declining as regime adaptations applied. "
            "Regime-conditional theory success improving."
        ),
        "contradictions": ["Residual liquidity concentration (declining frequency)"],
        "weakening_assumptions": ["Regime-invariant assumptions (being phased out)"],
        "regime": (
            "Stabilizing mixed regime. "
            "Regime-conditional framework showing effectiveness. "
            "Adaptive interpretation paying dividends."
        ),
    },
    {
        "posture": "contradicted",
        "coherence_trajectory": "collapsed",
        "summary": (
            "Complete theoretical framework failure. "
            "Coherence at critical low (0.22) with maximum pressure (0.89). "
            "Market behavior decoupled from all theory domains. "
            "Emergency cognition reset required."
        ),
        "contradictions": [
            "All theory dimensions simultaneously contradicted",
            "Price direction unpredictable",
            "Liquidity fragmented",
            "Volatility extreme",
            "Breadth collapsed",
        ],
        "weakening_assumptions": ["ALL active theories showing universal failure"],
        "regime": (
            "Shock/dislocation regime. "
            "Market structure fundamentally altered. "
            "Existing theory bases obsolete. "
            "Requires market regime re-evaluation from first principles."
        ),
    },
]
