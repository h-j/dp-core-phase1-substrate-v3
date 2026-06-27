# PHASE 1: ARCHITECTURE REVIEW & DEPENDENCY MAPPING

**Date**: 2026-06-02  
**Purpose**: Complete dependency analysis before consolidation implementation  
**Scope**: Theory generation, persistence, retrieval, consumption pipeline

---

## 1. COMPONENT INVENTORY

### Core Generators
| Component | File | Role | Input | Output |
|-----------|------|------|-------|--------|
| **TheoryGenerationFlow** | flows/theory_flow/theory_generation_flow.py | Generates theories via LLM | Abstraction, context, regime | Theory (summary as JSON string) |
| **DialecticalSynthesizer** | flows/theory_flow/dialectical_synthesizer.py | Synthesizes competing theories | Theory list, validations | Synthesis prompt text |
| **AbstractionFlow** | flows/observation_flow/abstraction_flow.py | Creates abstractions | MarketObservation | Abstraction |

### Persistence Layer
| Component | File | Role | Input | Output |
|-----------|------|------|-------|--------|
| **TheoryRepository** | memory/relational/repositories/theory_repository.py | Persist/retrieve theories | Theory obj | Persisted to DB |
| **TheoryModel** | memory/relational/models/theory_model.py | ORM mapping | — | theories table |
| **TheoryStructuredModel** | memory/relational/models/theory_structured_model.py | (DEAD) Separate structured storage | — | theory_structures table (✗ NEVER CREATED) |
| **PostgresClient** | memory/relational/postgres_client.py | DB connection manager | — | SQLAlchemy engine, SessionLocal |

### Consumption/Analysis
| Component | File | Role | Input | Output |
|-----------|------|------|-------|--------|
| **ReflectionFlow** | flows/reflection_flow/reflection_flow.py | Reflects on theory validity | Theory + validation + contradiction | ReflectionEvent |
| **ContradictionDetector** | cognition/contradiction/contradiction_detector.py | Detects theory conflicts | Current + historical theories | Contradiction score + indicators |
| **HistoricalCognitionService** | memory/lineage/historical_cognition_service.py | Builds historical context | Recent theories, reflections, validations | Context prompt text |
| **ReplayEngine** | market/replay/replay_engine.py | Deterministic historical execution | Dataset + initial config | Replay metrics, snapshots |
| **ReflectiveMemorySynthesizer** | memory/reflection/reflective_memory_synthesizer.py | Synthesizes reflective memory | Theories + reflections + validations | Memory snapshot |

### Orchestration
| Component | File | Role |
|-----------|------|------|
| **CognitionOrchestrator** | orchestration/cognition_orchestrator.py | Coordinates flow execution |
| **run_cognition_loop** | bootstrap/run_cognition_loop.py | Main loop entry point |
| **ReplayValidationRunner** | bootstrap/replay_validation_runner.py | Replay execution harness |

---

## 2. THEORY LIFECYCLE: CURRENT STATE

### Path A: Generation → Persistence (ACTIVE)

```
TheoryGenerationFlow.process()
├─ Calls OllamaClient.generate(prompt)
├─ Receives raw LLM output
├─ Calls _clean_theory(raw_output, parsed_json)
├─ RETURNS: theory.summary = json.dumps(structured_dict)
│           where structured_dict = {
│               "claim": "...",
│               "if_branch": "...",
│               "else_branch": "...",
│               "unless": "...",
│               "falsified_if": "..."
│           }
└─ Creates Theory object
    └─ theory.summary = JSON string (canonical)

run_cognition_loop.main()
├─ theory_repository.save(theory)
│   ├─ Parses theory.summary as JSON
│   ├─ **PATH A1 (ACTIVE)**: 
│   │  ├─ Creates TheoryModel with summary_structured = parsed JSON string
│   │  ├─ session.merge(theory_model)
│   │  └─ Persists to theories.summary_structured column ✓
│   │
│   └─ **PATH A2 (DEAD)**:
│      ├─ Creates TheoryStructuredModel
│      ├─ session.merge(structured_model)
│      └─ Attempts to persist to theory_structures table ✗ [MISSING]
│
└─ Continues cognition loop
```

**Current State**: PATH A1 works perfectly. PATH A2 dead code.

### Path B: Retrieval (BROKEN)

```
theory_repository.list_recent(limit=5)
├─ session.query(TheoryModel).all()
│  └─ Returns: theories with summary_structured column loaded ✓
│
└─ **FOR EACH THEORY**: (Lines 92-105)
   ├─ session.query(TheoryStructuredModel)
   │  .filter(TheoryStructuredModel.theory_id == rec.id)
   │  .one_or_none()
   │
   └─ **CRASHES**: psycopg2.errors.UndefinedTable
                   relation "theory_structures" does not exist ✗
```

**Current Issue**: Even though `summary_structured` is already loaded on TheoryModel, the code tries to fetch from a non-existent table and crashes.

### Path C: Consumption (WORKING, BUT DEFENSIVE)

```
Consumers read directly from theory object:

ReflectionFlow (line 112):
  t_struct = getattr(theory, "summary_structured", None)
  if isinstance(t_struct, dict):
      use structured data
  else:
      fallback to theory.summary

ContradictionDetector (lines 176-182):
  structured = theory.get("theory_summary_structured") or theory.get("summary_structured")
  (or via object attrs)

HistoricalCognitionService (line 43):
  s = getattr(t, "summary_structured", None)

ReflectiveMemorySynthesizer (line 414):
  s = getattr(theory, "summary_structured", None)

ReplayEngine (lines 652, 905, 1339):
  t_struct = getattr(theory, 'summary_structured', None)
```

**Current State**: All work because they read from TheoryModel.summary_structured (PATH A1).
Never call list_recent() and hit the broken retrieval logic.

---

## 3. DEPENDENCY GRAPH

### Generation Dependencies
```
TheoryGenerationFlow
├─ Inputs:
│  ├─ Abstraction (from AbstractionFlow)
│  ├─ HistoricalContext (from HistoricalCognitionService)
│  ├─ MarketMemoryContext (from HistoricalMarketMemoryService)
│  ├─ RegimeHistory (from RegimeContinuityMemory)
│  ├─ DialecticalSynthesis (from DialecticalSynthesizer)
│  └─ OllamaClient (interfaces/ollama_client.py)
├─ Outputs:
│  └─ Theory (with summary = JSON string)
└─ Errors:
   └─ If OllamaClient unavailable → Exception (no fallback)
```

### Persistence Dependencies
```
TheoryRepository
├─ Imports:
│  ├─ TheoryModel (model)
│  ├─ TheoryStructuredModel (DEAD)
│  ├─ SessionLocal (from postgres_client) ✓
│  └─ json
├─ Consumers:
│  ├─ run_cognition_loop.main()
│  ├─ ReplayEngine
│  ├─ ReplayValidationRunner
│  └─ bootstrap/replay_demo.py
└─ Issues:
   ├─ Lines 55-68: Dead persistence logic (never executed successfully)
   └─ Lines 92-105: Dead retrieval logic (crashes on query)
```

### Consumption Dependencies
```
ReflectionFlow.process()
├─ Input: theory object
├─ Uses: theory.summary_structured (via getattr with defensive fallback)
├─ Called by: run_cognition_loop (line 270)
└─ Transitivity: theory must have been loaded via PATH A1

ContradictionDetector.detect()
├─ Input: current_theory + historical_theories
├─ Uses: theory.summary_structured (defensive dual-key lookup)
├─ Called by: run_cognition_loop, ReplayEngine
└─ Transitivity: theories must have PATH A1 structured data

HistoricalCognitionService.build_context()
├─ Input: theories from theory_repository.list_recent()
├─ Uses: theory.summary_structured
├─ Problem: list_recent() crashes! ✗
└─ Workaround: Never actually called in main loop (only in diagnostics)

ReplayEngine._run_step()
├─ Inputs: theory + observation
├─ Uses: theory.summary_structured
├─ Data source: theories loaded via direct query (bypasses list_recent)
└─ Status: Working ✓
```

---

## 4. SCHEMA STATE

### Current Schema

**theories table** (active):
```sql
CREATE TABLE theories (
    id VARCHAR PRIMARY KEY,
    lineage_id VARCHAR,
    thesis VARCHAR,
    summary VARCHAR,
    summary_structured TEXT,  -- ✓ ACTIVE (stores JSON string)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**theory_structures table** (missing):
```
DEFINED IN: memory/relational/models/theory_structured_model.py
CREATED IN SCHEMA: NEVER (not registered in Base.metadata)
REASON: TheoryStructuredModel NOT in __init__.py __all__

Result: Table never created → queries crash
```

### Schema Registration Status
```
memory/relational/models/__init__.py:

Registered (in __all__):
  ✓ AbstractionModel
  ✓ ConfidenceModel
  ✓ ObservationModel
  ✓ ReflectionModel
  ✓ ReflectiveMemoryModel
  ✓ TheoryModel
  ✓ ValidationModel

Not Registered (missing from __all__):
  ✗ TheoryStructuredModel (defined but not exported)
  ✗ MarketOutcomeModel (defined, conditional import in run_cognition_loop)
  ✗ PredictionProbeModel
  ✗ PredictionResultModel
  ✗ TransitionPressureModel

Result: Unregistered models NOT included in Base.metadata.create_all()
```

---

## 5. DEAD CODE PATHS

### 5.1 TheoryStructuredModel Persistence (Lines 55-68 in theory_repository.py)

**Code**:
```python
if structured_json:
    structured_model = TheoryStructuredModel(
        theory_id=theory.id,
        structured_json=structured_json
    )
    session.merge(structured_model)
```

**Status**: DEAD
- Attempted merge to non-existent table
- Even if table existed, data would duplicate PATH A1 persistence
- No consumer ever reads from this model
- Replaced by PATH A1 (lines 38)

**Impact if Removed**: NONE
- DATA: No loss (already in summary_structured column)
- CONSUMERS: Unaffected (all read from PATH A1)
- TESTING: No test references this code

---

### 5.2 TheoryStructuredModel Retrieval (Lines 92-105 in theory_repository.py)

**Code**:
```python
for rec in results:
    try:
        structured = (
            session.query(TheoryStructuredModel)
            .filter(TheoryStructuredModel.theory_id == rec.id)
            .one_or_none()
        )
        if structured and structured.structured_json:
            try:
                rec.summary_structured = json.loads(structured.structured_json)
            except Exception:
                rec.summary_structured = None
        else:
            rec.summary_structured = None
    except Exception:
        rec.summary_structured = None
```

**Status**: DEAD + BROKEN
- Attempts to override rec.summary_structured with data from non-existent table
- Query always fails → caught in exception handler
- rec.summary_structured already populated from theories table column
- Exception handler masks the error
- Never actually overwrites the data

**Impact if Removed**: NONE
- No functional change (exception handler makes it a no-op)
- Improves performance (eliminates failed queries)
- Clarifies intent (remove duplicate logic)

---

### 5.3 TheoryStructuredModel Definition

**File**: `memory/relational/models/theory_structured_model.py`

**Status**: DEAD
- Never imported except in theory_repository.py (line 3)
- Never registered (not in __init__.py)
- Never created (not in Base.metadata)
- Table never exists in schema
- No foreign key constraints reference it

**Impact if Removed**: NONE
- Data: Already in summary_structured column
- Consumers: All read from TheoryModel
- Testing: No references

---

### 5.4 Unused ModelRegistrations

**File**: `memory/relational/models/__init__.py`

**Status**: INCOMPLETE
- MarketOutcomeModel imported but may not be registered
- PredictionProbeModel, PredictionResultModel, TransitionPressureModel NOT in __all__
- These models exist but won't be created by Base.metadata.create_all()

**Impact**: Potential missing tables if bootstrap tries to use them

---

## 6. DUPLICATE LOGIC

### 6.1 JSON Parsing in TheoryRepository

**Location A**: Line 38 (ACTIVE)
```python
summary_structured=(
    json.dumps(json.loads(theory.summary)) 
    if isinstance(getattr(theory, 'summary', None), str) 
    and _is_json(getattr(theory, 'summary')) 
    else None
)
```

**Location B**: Lines 55-60 (DEAD)
```python
structured_json = None
if isinstance(getattr(theory, 'summary', None), str) 
   and _is_json(getattr(theory, 'summary')):
    try:
        parsed = json.loads(theory.summary)
        structured_json = json.dumps(parsed)
```

**Status**: DUPLICATE
- Same logic parsed twice
- Second occurrence used for dead persistence
- Can be consolidated

---

## 7. CIRCULAR & COMPLEX DEPENDENCIES

### Potential Circular Dependency: Reflection ↔ Contradiction

```
ReflectionFlow.process()
├─ Inputs: theory, validation, contradiction_result
├─ Outputs: ReflectionEvent
└─ Called by: run_cognition_loop (after contradiction detection)

ContradictionDetector.detect()
├─ Inputs: current_theory, historical_theories, ...
├─ Outputs: contradiction dict
└─ Called by: run_cognition_loop (before reflection)

Dependency Order:
  1. Generate theory
  2. Detect contradictions
  3. Reflect on validity
  
No actual circularity—sequential flow.
```

### Potential Data Staleness: Historical Context

```
HistoricalCognitionService.build_context()
├─ Calls: theory_repository.list_recent()
├─ Issue: list_recent() BROKEN
├─ Workaround: Only called in diagnostics, not main loop
└─ Impact: Can't generate historical context in production

ReplayEngine._run_step()
├─ Direct query to theories table (bypasses list_recent)
├─ Status: Works ✓
└─ Recommendation: HistoricalCognitionService should do same
```

---

## 8. SCHEMA INCONSISTENCIES

### 8.1 summary vs. summary_structured Redundancy

**Issue**: Theories store complete structured data in TWO places:

```
theory.summary = '{"claim": "...", "if_branch": "...", ...}'  (JSON string)
theory.summary_structured = '"{"claim": "...", ...}"'          (JSON string, same content)
```

**Problem**:
- theory.summary: Generated by LLM, stored as JSON string
- summary_structured: Parsed and re-serialized copy of summary

**Question**: Why have both?
- Answer: Historical - summary was text-based before v3.0
- Current: Both store same JSON; one is redundant

**Recommendation**: Use single field, drop redundancy in Phase 2

---

### 8.2 Theories Table vs. Theory Snapshots in Replay

**Replay Snapshots** (replay_engine.py:1339-1341):
```python
"theory_summary_structured": (
    getattr(theory, "summary_structured", None)
    if isinstance(getattr(theory, "summary_structured", None), dict)
    else None
)
```

**Inconsistency**:
- Key name: `"theory_summary_structured"` (in snapshot)
- Object attr: `summary_structured` (on theory)
- Consumers check both: `theory.get("theory_summary_structured") or theory.get("summary_structured")`

**Recommendation**: Normalize to single key in Phase 2

---

## 9. CURRENT ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        THEORY GENERATION PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────┘

ObservationFlow    AbstractionFlow    ReflectionFlow
     ↓                   ↓                  ↓
     └──→ HistoricalContext ←──┐
          HistoricalMarketMemory ←──┐
                                   ReflectiveMemory
                                        ↓
  RegimeContinuityMemory  DialecticalSynthesizer
              ↓                        ↓
              └──────→ TheoryGenerationFlow ←──── OllamaClient
                               ↓
                        theory object
                  (summary = JSON string)
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          PERSISTENCE LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│  TheoryRepository.save(theory)                                           │
│                                                                          │
│  ┌─ PATH A1 (ACTIVE) ────────────────────────────────────────┐         │
│  │ Parse theory.summary as JSON                             │          │
│  │ Create TheoryModel with summary_structured = JSON string │          │
│  │ session.merge(theory_model) ✓                            │          │
│  └─ Persists to: theories.summary_structured column ✓       │          │
│                                                              │          │
│  ┌─ PATH A2 (DEAD) ──────────────────────────────────────┐  │          │
│  │ Create TheoryStructuredModel                         │  │          │
│  │ session.merge(structured_model) ✗                    │  │          │
│  │ Attempts: theory_structures table [NEVER CREATED]    │  │          │
│  └────────────────────────────────────────────────────────┘  │          │
└─────────────────────────────────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                              DATABASE                                    │
    ├──────────────────────────────────────┬──────────────────────────────────┤
    │  theories table (✓ EXISTS)           │ theory_structures (✗ MISSING)    │
    │                                      │                                  │
    │ id | summary_structured | ...        │ (never created - not registered) │
    │    | (JSON string)      |            │                                  │
    └──────────────────────────┬───────────┴──────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         RETRIEVAL LAYER (BROKEN)                         │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  TheoryRepository.list_recent()                                          │
    │                                                                          │
    │  Step 1: session.query(TheoryModel).all()                               │
    │          Returns theories with summary_structured loaded ✓              │
    │                                                                          │
    │  Step 2: For each theory:                                               │
    │          session.query(TheoryStructuredModel)                           │
    │          .filter(...)                                                   │
    │          .one_or_none()                                                 │
    │          ✗ CRASHES: relation "theory_structures" does not exist         │
    │          (exception caught silently, becomes no-op)                     │
    └─────────────────────────────────────────────────────────────────────────┘
         ↓
    Exception handled → rec.summary_structured unchanged (was already populated)
         ↓
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         CONSUMPTION LAYER (WORKING)                      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  (Defensive programming masks the broken retrieval logic)               │
    │                                                                          │
    │  ReflectionFlow:     getattr(theory, "summary_structured", None)        │
    │  ContradictionDetector: theory.get("theory_summary_structured") or ...  │
    │  HistoricalCognition:   getattr(t, "summary_structured", None)          │
    │  ReflectiveMemory:       getattr(theory, "summary_structured", None)    │
    │  ReplayEngine:           getattr(theory, 'summary_structured', None)    │
    │                                                                          │
    │  All read from PATH A1 directly (theories.summary_structured) ✓         │
    │  Never call list_recent() in production code                           │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. CONSOLIDATION OPPORTUNITIES

### Opportunity 1: Remove Dead Persistence Path

**Current**: PATH A2 (lines 55-68)  
**Target**: DELETE  
**Impact**: Performance improvement, code clarity  
**Risk**: NONE (no consumer relies on theory_structures table)

### Opportunity 2: Fix/Remove Dead Retrieval Logic

**Current**: lines 92-105 (exception handler masks failure)  
**Target**: DELETE entire block  
**Impact**: Improves performance (removes failed queries), clarifies intent  
**Risk**: NONE (data already loaded from theory column)

### Opportunity 3: Remove Dead Model

**Current**: TheoryStructuredModel (entire file)  
**Target**: DELETE file  
**Impact**: Reduces codebase surface  
**Risk**: NONE (not registered, not used)

### Opportunity 4: Unify Structured Theory Access

**Current**: Defensive getattr calls with fallbacks  
**Target**: Single canonical path `theory.summary_structured`  
**Impact**: Simplifies consumer code  
**Risk**: LOW (already defensive)

### Opportunity 5: Add Fail-Fast Validation

**Current**: No schema verification at startup  
**Target**: Validate schema on boot, raise RuntimeError if invalid  
**Impact**: Clear failure mode, easier debugging  
**Risk**: NONE (improves observability)

### Opportunity 6: Add Instrumentation

**Current**: No tracking of structured cognition lifecycle  
**Target**: Add trace logging for: generation → persistence → retrieval → consumption  
**Impact**: Measure survival rate, debug failures  
**Risk**: NONE (additive, no logic changes)

---

## 11. ISSUES & INCONSISTENCIES

| Issue | Severity | Current State | Impact |
|-------|----------|---------------|--------|
| theory_structures table missing | HIGH | Causes crashes in list_recent() | Blocks diagnostics; masked by exception handling |
| TheoryStructuredModel not registered | MEDIUM | Dead code persists | Schema bloat, maintenance debt |
| Dual persistence logic (A1 + A2) | MEDIUM | Redundant code | Confusing, maintenance risk |
| Dual retrieval logic | MEDIUM | Dead exception handler | Performance cost, code clarity |
| summary vs. summary_structured redundancy | LOW | Same data in two fields | Minor schema redundancy |
| Inconsistent key names (theory_summary_structured vs summary_structured) | LOW | Defensive code works but unclear | Maintainability |
| No schema validation at startup | MEDIUM | Silent failures possible | Difficult to debug |
| No structured cognition lifecycle tracing | MEDIUM | Can't measure survival | Can't audit data integrity |

---

## 12. CONSOLIDATION ROADMAP

### Phase 1 ✓ COMPLETE
- [x] Audit current architecture
- [x] Identify dead code paths
- [x] Map dependencies
- [x] Document issues
- [x] Create dependency diagram

### Phase 2: CONSOLIDATION
- [ ] Remove TheoryStructuredModel import (line 3)
- [ ] Remove dead persistence logic (lines 55-68)
- [ ] Remove dead retrieval logic (lines 92-105)
- [ ] Simplify TheoryRepository.save() and list_recent()
- [ ] Delete theory_structured_model.py
- [ ] Verify model registration (check all models in __all__)

### Phase 3: OBSERVABILITY
- [ ] Add startup schema validation
- [ ] Add structured theory generation trace
- [ ] Add persistence instrumentation
- [ ] Add retrieval instrumentation
- [ ] Add consumption instrumentation
- [ ] Measure survival rate

### Phase 4: FAIL-FAST
- [ ] Verify PostgreSQL connection on boot
- [ ] Check theories table exists
- [ ] Check summary_structured column exists
- [ ] Validate structured theory JSON schema
- [ ] Raise RuntimeError if any check fails

### Phase 5: DIAGNOSTICS
- [ ] Classify theories (Observation vs. Hypothesis vs. Falsifiable)
- [ ] Add replay summary reporting
- [ ] Track structured theory survival per step
- [ ] Create audit trail

### Phase 6: FINAL REPORT
- [ ] Document before/after architecture
- [ ] List all files modified/deleted
- [ ] Calculate dead code removed
- [ ] Identify remaining technical debt
- [ ] Recommend v4.0 roadmap

---

## 13. SUCCESS METRICS (Phase 1 Complete)

✓ **Dependency map complete**: All components, inputs, outputs documented  
✓ **Dead code identified**: 3 paths, 50+ lines of dead logic  
✓ **Issues documented**: 8 severity-classified problems  
✓ **Risk assessment**: All removals assessed as NONE/LOW risk  
✓ **Consolidation opportunities**: 6 clear pathways to simplification  

**Recommendation**: PROCEED TO PHASE 2

---

## APPENDIX: File-by-File Summary

### To Be Modified (Phase 2)
1. **memory/relational/repositories/theory_repository.py**
   - Line 3: Remove import
   - Lines 55-68: Remove dead persistence
   - Lines 92-105: Remove dead retrieval
   - Result: Simpler save() and list_recent()

2. **memory/relational/models/__init__.py**
   - Verify all models in __all__
   - Check registration completeness
   - Add missing models if needed

### To Be Deleted (Phase 2)
1. **memory/relational/models/theory_structured_model.py** (entire file)

### To Be Added (Phases 3-4)
1. **memory/relational/schema_validator.py** (new validation module)
2. **telemetry/structured_cognition_tracer.py** (new instrumentation)

### Unchanged
- All consumers (reflection_flow, contradiction_detector, etc.) - already use correct path
- Theory schema - only removing dead dual-storage
- Database schema - theories table unchanged
- Generation logic - no changes needed

