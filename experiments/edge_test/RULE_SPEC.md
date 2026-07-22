# MECHANICAL RULE SPECIFICATION (PSEUDOCODE)

**Status**: SPECIFICATION SPEC  
**Target Document**: `experiments/edge_test/RULE_SPEC.md`  
**Purpose**: Formal unambiguous pseudocode for the Edge Test mechanical trading rule defined in `PREREGISTRATION.md`.

---

## 1. PRE-REGISTERED CONSTANTS

```python
# Universe and Allocation Parameters
UNIVERSE_INSTRUMENTS = [
    "NIFTY_FUT_PROXY",
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
]  # <OWNER DECIDES: Final universe selection>

# Signal Generation Thresholds
RELIABILITY_BAND_ESTABLISHED_MIN = 0.75  # Min reliability score for established theories
SIGNAL_WEIGHTED_SUM_THRESHOLD = 0.25     # Min |weighted sum| threshold to take position
POSITION_NOTIONAL_FRACTION = 1.0        # Fixed 100% notional, single unit (no compounding)

# Transaction Cost Parameters (India Market Conservative Model)
COST_BROKERAGE_PER_SIDE_BPS = 3.0       # 0.03% per side
COST_STT_SELL_SIDE_BPS = 2.5            # 0.025% on sell side (Futures proxy rate)
COST_EXCHANGE_PER_SIDE_BPS = 0.3        # 0.003% per side
COST_GST_RATE = 0.18                    # 18% GST on brokerage + exchange fee
COST_STAMP_DUTY_BUY_BPS = 0.2           # 0.002% stamp duty on buy side
COST_SLIPPAGE_PER_SIDE_BPS = 5.0        # 0.05% slippage per side (liquidity impact)

# Computed Costs in Bps
COST_BUY_SIDE_BPS = (
    COST_BROKERAGE_PER_SIDE_BPS
    + COST_EXCHANGE_PER_SIDE_BPS
    + (COST_BROKERAGE_PER_SIDE_BPS + COST_EXCHANGE_PER_SIDE_BPS) * COST_GST_RATE
    + COST_STAMP_DUTY_BUY_BPS
    + COST_SLIPPAGE_PER_SIDE_BPS
)  # 3.0 + 0.3 + 0.594 + 0.2 + 5.0 = 9.094 bps

COST_SELL_SIDE_BPS = (
    COST_BROKERAGE_PER_SIDE_BPS
    + COST_STT_SELL_SIDE_BPS
    + COST_EXCHANGE_PER_SIDE_BPS
    + (COST_BROKERAGE_PER_SIDE_BPS + COST_EXCHANGE_PER_SIDE_BPS) * COST_GST_RATE
    + COST_SLIPPAGE_PER_SIDE_BPS
)  # 3.0 + 2.5 + 0.3 + 0.594 + 5.0 = 11.394 bps

ALL_IN_ROUND_TRIP_COST_BPS = COST_BUY_SIDE_BPS + COST_SELL_SIDE_BPS  # 20.488 bps (~20.5 bps)
```

---

## 2. FORMAL ALGORITHM PSEUDOCODE

```python
def generate_daily_signal_for_instrument(instrument_id: str, day_t: int, theory_base: List[Theory]) -> int:
    """
    Computes position signal for day t+1 based strictly on EOD day t theories.
    Returns: +1 (Long), -1 (Short), or 0 (Flat).
    """
    established_theories = []
    
    # Step 1: Collect established theories whose scope & activation predicates fire for day t
    for theory in theory_base:
        if theory.reliability_score > RELIABILITY_BAND_ESTABLISHED_MIN:
            if theory.scope_predicate.evaluates_true(instrument_id, day_t):
                if theory.activation_predicate.evaluates_true(instrument_id, day_t):
                    established_theories.append(theory)
    
    # Step 2: If no established theory fires, position is FLAT
    if len(established_theories) == 0:
        return 0
    
    # Step 3: Compute reliability-weighted sum of directional commitments
    weighted_sum = 0.0
    for theory in established_theories:
        reliability = theory.reliability_score
        directional_commitment = theory.fallback_payload.directional_commitment  # -1 or +1
        weighted_sum += reliability * directional_commitment
    
    # Step 4: Apply minimum threshold filter
    if abs(weighted_sum) < SIGNAL_WEIGHTED_SUM_THRESHOLD:
        return 0  # Flat if signal below threshold
    
    # Step 5: Return sign of weighted sum (+1 or -1)
    if weighted_sum > 0:
        return +1
    else:
        return -1


def execute_mechanical_rule(
    instrument_id: str,
    day_t: int,
    signal_t: int,
    open_price_t_plus_1: float,
    close_price_t_plus_1: float,
    current_position: int
) -> Tuple[float, float, int]:
    """
    Executes position rebalance at Next-Day Open (day t+1 Open).
    Computes daily return including explicit trading costs.
    """
    target_position = signal_t  # +1, -1, or 0
    trade_executed = (target_position != current_position)
    
    cost_penalty_bps = 0.0
    if trade_executed:
        if current_position == 0:
            # Entering new position (1 side fee)
            cost_penalty_bps = COST_BUY_SIDE_BPS if target_position == +1 else COST_SELL_SIDE_BPS
        elif target_position == 0:
            # Exiting position to flat (1 side fee)
            cost_penalty_bps = COST_SELL_SIDE_BPS if current_position == +1 else COST_BUY_SIDE_BPS
        else:
            # Reversing position from +1 to -1 or -1 to +1 (2 sides fee = full round-trip)
            cost_penalty_bps = ALL_IN_ROUND_TRIP_COST_BPS
            
    cost_penalty_decimal = cost_penalty_bps / 10000.0
    
    # Gross daily price return from Open_t+1 to Close_t+1
    raw_price_return = (close_price_t_plus_1 - open_price_t_plus_1) / open_price_t_plus_1
    
    # Directional position return minus cost penalty
    daily_gross_return = target_position * raw_price_return
    daily_net_return = daily_gross_return - cost_penalty_decimal
    
    new_position = target_position
    return daily_net_return, daily_gross_return, new_position
```

---

## 3. RULE DATA ACCESS CONSTRAINTS

```text
ALLOWED READ INPUTS:
- Theory.reliability_score (float)
- Theory.scope_predicate (evaluable boolean function)
- Theory.activation_predicate (evaluable boolean function)
- Theory.fallback_payload.directional_commitment (int in {-1, +1})

PROHIBITED INPUTS (STRICTLY FORBIDDEN):
- Raw OHLCV price series during signal evaluation (prices read ONLY for Open_t+1 execution fill & return calculation)
- Technical indicators (RSI, Moving Averages, MACD) beyond predicate evaluation
- Historical PnL or trade outcome feedback
```
