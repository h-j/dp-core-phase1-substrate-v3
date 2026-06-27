# HLD: Market-Grounded Reflective Cognition Substrate

## 1. System Purpose
This substrate is a **cognition laboratory**. Its goal is to study how an AI's internal belief system (theories) adapts, contradicts itself, and evolves when exposed to the non-stationary and adversarial environment of financial markets.

## 2. Core Architecture Layers
*   **Orchestration (Replay Engine):** Manages deterministic time-stepping.
*   **Market Grounding:** Synthesizes raw data into structured "Observations".
*   **Cognition Loop:** The "Thinker" layer (Observation → Abstraction → Theory → Reflection).
*   **Memory & Persistence:** Stores longitudinal state (Regime Memory, Lineage, RDBMS).

## 3. The Daily Replay Loop (Data Flow)

### Phase 1: Ingestion & Synthesis
1. **ReplayEngine** loads CSV data.
2. **MarketObservationSynthesizer** converts OHLCV into `MarketObservation` (semantics vs raw data).
3. **HorizonCognitionEngine** generates Daily/Weekly/Monthly structural views.

### Phase 2: Context Retrieval
1. **RegimeMemoryStore** retrieves similar historical days (signatures).
2. **TheoryLineageEngine** fetches active cognitive threads.

### Phase 3: The Cognition Loop
1. **AbstractionFlow:** Summarizes market events.
2. **TheoryGenerationFlow:** Generates/Mutates beliefs based on history.
3. **ContradictionDetector:** Flags conflicts between "Belief" and "Reality".
4. **ReflectionFlow:** Evaluates the theory vs outcome; updates self-awareness.

### Phase 4: Assessment & Inference
1. **EpistemicScoringEngine:** Evaluates "Theory Usefulness".
2. **ConfidenceEvolutionEngine:** Updates confidence states (Empirical, Coherence, Pressure).
3. **TransitionPressureEngine:** Detects breakout risks and stability.
4. **PredictionProbeGenerator:** Issues a directional "Probe" with calibrated confidence.

### Phase 5: Execution & Persistence
1. **DecisionPolicyEngine:** Filters probes through risk/conviction policies.
2. **CapitalSimulator:** Tracks simulated PnL (Observer-only).
3. **Repositories:** Persist state to PostgreSQL.

## 4. Key Cognitive Semantics

| Component | Role |
| :--- | :--- |
| **Lineage** | Tracks the evolution of a theory from its root to its mutations. |
| **Contradiction** | The primary driver of "cognitive stress" and theory retirement. |
| **Regime Signature** | A multi-dimensional hash of market state used for memory recall. |
| **Calibration** | The process of ensuring internal confidence matches external accuracy. |

## 5. Major Component Mapping

*   **Orchestrator:** `market/replay/replay_engine.py`
*   **Observation:** `market/replay/market_observation_synthesizer.py`
*   **Theory Engine:** `flows/theory_flow/` & `memory/replay/epistemic_scoring.py`
*   **Confidence:** `cognition/confidence/confidence_evolution_engine.py`
*   **Decisioning:** `market/replay/decision_policy.py`
*   **Analysis:** `market/replay/replay_analysis.py`

## 6. How to Verify Changes
1. **Unit Tests:** `poetry run pytest` (Logic checks).
2. **Short Replay:** Run a 3-day replay on RELIANCE to check for flow breaks.
3. **Long Replay:** Run a 30-day replay to verify "Theory Retirement" and "Confidence Calibration" metrics in the summary.

---
*Document Version: 1.1*
*Grounding Doctrine: Understanding > Prediction*

## 7. World-Class System Improvements & Concerns

### Architectural Risks
*   **Execution Monolith:** The `ReplayExecutor.execute` loop is over-extended. Logic for metrics, persistence, and cognition should be separated into event listeners or pipeline stages to prevent side-effect leakage.
*   **Silent Failures:** Widespread use of `except: pass` in the orchestrator can mask cognitive regression. 
*   **Data Integrity:** Current list serialization in repositories (newline-delimited) is brittle against multi-line LLM outputs.

### Priority Improvements
*   **1. Configuration-Driven Cognition:** Extract all hardcoded multipliers and thresholds (e.g., in `TransitionPressureEngine`) into a centralized YAML configuration. This facilitates reproducible "Personality" tuning.
*   **2. Observability 2.0:** Replace print statements with a structured event-bus. This allows real-time dashboards to hook into the replay without modifying the core loop.
*   **3. Parallel Replay Execution:** Implement a worker-pool for `ReplayExecutor` to allow simultaneous replays across multiple assets (e.g., replaying the entire NIFTY 50 universe) while maintaining per-asset determinism.
*   **4. Strict Type Definitions:** Replace `object` type hints with `Protocols` (PEP 544) to ensure that observations and theories adhere to required interfaces at runtime.
*   **5. Epistemic Unit Testing:** Create a test suite that asserts cognitive behavior (e.g., "Given a contradiction score of 0.8, ensure theory retirement is triggered within 2 steps").

### Scalability Targets
| Milestone | Target |
| :--- | :--- |
| **Performance** | 100-day replay (full cognition) in < 120 seconds. |
| **Reliability** | Zero "silent passes"; 100% of internal errors logged to the DB. |
| **Extensibility** | Adding a new "Grounding Domain" (e.g., Crypto) requires < 3 file changes. |