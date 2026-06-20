from market.schemas.market_outcome import MarketOutcome


# Seeded market outcomes for validation testing
# Linked to observations that were previously created in the system

SAMPLE_NIFTY_OUTCOMES = [
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-01",
        outcome_summary=(
            "NIFTY continued higher despite weak breadth, creating divergence. "
            "Large caps drove the move while mid-caps lagged."
        ),
        realized_trend="up with continuation",
        realized_volatility="elevated",
        realized_breadth="weak with divergence",
        realized_liquidity="concentrated in large caps",
        outcome_contradictions=[
            "price strength vs weak breadth",
            "new highs with narrow participation",
        ],
        outcome_confidence=0.6,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-02",
        outcome_summary=(
            "Momentum persistence weakened as volatility expanded. "
            "Recovery from intraday lows lacked conviction."
        ),
        realized_trend="mixed with reversals",
        realized_volatility="expanded significantly",
        realized_breadth="mixed participation",
        realized_liquidity="uneven flow",
        outcome_contradictions=[
            "momentum persistence vs volatility expansion",
            "recovery without conviction",
        ],
        outcome_confidence=0.5,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-03",
        outcome_summary=(
            "Liquidity concentrated in NIFTY 50 despite declining broader market. "
            "Sectoral rotation evident with IT weakness."
        ),
        realized_trend="selective strength",
        realized_volatility="contained",
        realized_breadth="weak in mid and small caps",
        realized_liquidity="concentrated in index heavyweights",
        outcome_contradictions=[
            "liquidity concentration vs participation weakness",
            "index strength vs broad market weakness",
        ],
        outcome_confidence=0.65,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-04",
        outcome_summary=(
            "Trend reversal from expected continuation. "
            "Breakout failed after initial strength, closing lower."
        ),
        realized_trend="reversal from highs",
        realized_volatility="high with doji patterns",
        realized_breadth="declined through session",
        realized_liquidity="strong but directional",
        outcome_contradictions=["breakout failed", "intraday reversal from trend"],
        outcome_confidence=0.45,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-05",
        outcome_summary=(
            "Breadth improvement supported price strength. "
            "Advance-decline ratio turned positive with broad participation."
        ),
        realized_trend="higher with breadth support",
        realized_volatility="stable",
        realized_breadth="broad improvement",
        realized_liquidity="ample across sectors",
        outcome_contradictions=[],
        outcome_confidence=0.85,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-06",
        outcome_summary=(
            "Volatility expanded despite positive close. "
            "Range expanded intraday with uncertainty lingering into close."
        ),
        realized_trend="higher but choppy",
        realized_volatility="expanded with wide range",
        realized_breadth="neutral",
        realized_liquidity="fragmented",
        outcome_contradictions=[
            "volatility expansion with positive close",
            "range expansion indicating uncertainty",
        ],
        outcome_confidence=0.5,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-07",
        outcome_summary=(
            "Weakness in liquidity foundations despite index support. "
            "Mid-cap weakness persisted through session."
        ),
        realized_trend="lower overall",
        realized_volatility="moderate",
        realized_breadth="weak with leadership in large caps only",
        realized_liquidity="weak in mid-cap segment",
        outcome_contradictions=[
            "NIFTY support vs mid-cap weakness",
            "liquidity fragmentation",
        ],
        outcome_confidence=0.55,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-08",
        outcome_summary=(
            "Liquidity-led momentum continuation as expected. "
            "Strong liquidity foundations supported sustained move higher."
        ),
        realized_trend="strong continuation",
        realized_volatility="compressed",
        realized_breadth="broad and improving",
        realized_liquidity="strong ample flow",
        outcome_contradictions=[],
        outcome_confidence=0.8,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-09",
        outcome_summary=(
            "Regime shift from directional to range-bound. "
            "Market oscillated within range instead of trending."
        ),
        realized_trend="range-bound consolidation",
        realized_volatility="compressed",
        realized_breadth="neutral meandering",
        realized_liquidity="steady but no directional push",
        outcome_contradictions=[
            "regime shift from trend to range",
            "assumption failure",
        ],
        outcome_confidence=0.6,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-10",
        outcome_summary=(
            "Selective strength continued with narrow breadth. "
            "Bank index carried momentum while others lagged severely."
        ),
        realized_trend="selective higher",
        realized_volatility="elevated in non-bank segments",
        realized_breadth="extremely narrow",
        realized_liquidity="concentrated in banking stocks",
        outcome_contradictions=[
            "price strength vs very weak breadth",
            "sector concentration risk",
        ],
        outcome_confidence=0.5,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-11",
        outcome_summary=(
            "Theoretical breadth weakness contradicted by strong volume. "
            "Participation stronger than expected on downside move."
        ),
        realized_trend="lower with strong participation",
        realized_volatility="moderate",
        realized_breadth="strong on decline",
        realized_liquidity="ample and broad",
        outcome_contradictions=[],
        outcome_confidence=0.75,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-12",
        outcome_summary=(
            "Recovery lacked sustainability. Bounces failed to extend. "
            "Selling pressure resumed after brief relief."
        ),
        realized_trend="lower with failed recovery",
        realized_volatility="elevated with whipsaws",
        realized_breadth="weak sellers dominating",
        realized_liquidity="uneven execution",
        outcome_contradictions=["bounce failure", "lack of conviction"],
        outcome_confidence=0.4,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-13",
        outcome_summary=(
            "Consensus trend theory outperformed in quiet market. "
            "Directional move supported by stable liquidity."
        ),
        realized_trend="directional continuation",
        realized_volatility="quiet and stable",
        realized_breadth="steady improvement",
        realized_liquidity="reliable flow",
        outcome_contradictions=[],
        outcome_confidence=0.82,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-14",
        outcome_summary=(
            "Assumption of macro sentiment deteriorated. "
            "External risks emerged, confidence shaken."
        ),
        realized_trend="down sharply",
        realized_volatility="spiked higher",
        realized_breadth="universal weakness",
        realized_liquidity="stress evident in execution",
        outcome_contradictions=["macro assumption failure", "external shock impact"],
        outcome_confidence=0.35,
    ),
    MarketOutcome(
        market_name="NIFTY",
        related_observation_id="obs-15",
        outcome_summary=(
            "Adaptive learning: weakness under volatile regimes confirmed again. "
            "Liquidity-led theories weakened as predicted under volatility spikes."
        ),
        realized_trend="lower under pressure",
        realized_volatility="highly elevated",
        realized_breadth="weak across board",
        realized_liquidity="fragmented severely",
        outcome_contradictions=[
            "liquidity led theories fail in vol spike",
            "regime sensitivity confirmed",
        ],
        outcome_confidence=0.45,
    ),
]
