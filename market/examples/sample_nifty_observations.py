from market.schemas.market_observation import MarketObservation

SAMPLE_NIFTY_OBSERVATIONS = [
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY closed higher while market breadth weakened and "
            "volatility expanded."
        ),
        trend_state="closed_higher",
        volatility_state="expanded",
        liquidity_state="concentrated_in_large_caps",
        breadth_state="weakened",
        macro_sentiment="cautiously_positive",
        contradiction_markers=[
            "price_up_breadth_down",
            "volatility_expansion_with_positive_close",
        ],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY extended gains with broad participation and stable " "volatility."
        ),
        trend_state="closed_higher",
        volatility_state="stable",
        liquidity_state="broad_participation",
        breadth_state="strengthened",
        macro_sentiment="positive",
        contradiction_markers=[],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY traded range bound as volatility compressed and liquidity "
            "remained selective."
        ),
        trend_state="range_bound",
        volatility_state="compressed",
        liquidity_state="selective",
        breadth_state="mixed",
        macro_sentiment="neutral",
        contradiction_markers=["index_stable_internal_rotation"],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY fell despite defensive large-cap support as broader "
            "participation deteriorated."
        ),
        trend_state="closed_lower",
        volatility_state="expanded",
        liquidity_state="concentrated_in_defensives",
        breadth_state="weakened",
        macro_sentiment="risk_off",
        contradiction_markers=["defensive_support_breadth_weakness"],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY recovered intraday while volatility stayed elevated and "
            "advance-decline breadth remained weak."
        ),
        trend_state="recovered_intraday",
        volatility_state="high",
        liquidity_state="narrow",
        breadth_state="weakened",
        macro_sentiment="uncertain",
        contradiction_markers=[
            "price_recovery_breadth_weakness",
            "high_volatility_recovery",
        ],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY closed higher with bank and IT leadership but midcap "
            "participation narrowed."
        ),
        trend_state="closed_higher",
        volatility_state="stable",
        liquidity_state="sector_concentrated",
        breadth_state="narrowed",
        macro_sentiment="mixed",
        contradiction_markers=["index_strength_participation_narrowing"],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY declined as volatility expanded and liquidity thinned "
            "across cyclical sectors."
        ),
        trend_state="closed_lower",
        volatility_state="expanded",
        liquidity_state="thin",
        breadth_state="weakened",
        macro_sentiment="negative",
        contradiction_markers=[],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY stabilized near prior highs while breadth improved and "
            "volatility compressed."
        ),
        trend_state="range_bound",
        volatility_state="compressed",
        liquidity_state="broad_participation",
        breadth_state="strengthened",
        macro_sentiment="constructive",
        contradiction_markers=["price_stability_breadth_improvement"],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY made a marginal new high while fewer constituents "
            "participated and volatility lifted."
        ),
        trend_state="closed_higher",
        volatility_state="expanded",
        liquidity_state="concentrated_in_large_caps",
        breadth_state="narrowed",
        macro_sentiment="cautiously_positive",
        contradiction_markers=[
            "new_high_narrow_breadth",
            "volatility_lift_on_strength",
        ],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY reversed lower from resistance as breadth weakened and "
            "risk appetite faded."
        ),
        trend_state="closed_lower",
        volatility_state="expanded",
        liquidity_state="contracted",
        breadth_state="weakened",
        macro_sentiment="risk_off",
        contradiction_markers=[],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY rose modestly while volatility stayed low and liquidity "
            "expanded into broader sectors."
        ),
        trend_state="closed_higher",
        volatility_state="low",
        liquidity_state="expanded",
        breadth_state="strengthened",
        macro_sentiment="positive",
        contradiction_markers=[],
        observation_source="sample_seed",
    ),
    MarketObservation(
        market_name="NIFTY 50",
        observation_text=(
            "NIFTY was flat, but sector rotation intensified and breadth "
            "signals remained mixed."
        ),
        trend_state="range_bound",
        volatility_state="stable",
        liquidity_state="rotational",
        breadth_state="mixed",
        macro_sentiment="uncertain",
        contradiction_markers=["flat_index_active_rotation"],
        observation_source="sample_seed",
    ),
]
