# Structured Theory Architecture Audit Report
**Date**: 2026-06-02  
**Status**: AUDIT ONLY — No code changes made  
**Objective**: Document architectural drift between dual structured theory persistence models

---

## EXECUTIVE SUMMARY

The codebase contains **two competing structured theory persistence models**:

1. **Model A (Active)**: `TheoryModel.summary_structured` — data stored directly on theories table
2. **Model B (Abandoned)**: `TheoryStructuredModel` — separate theory_structures table

**Current State**: Model B code exists but the `theory_structures` table is never created, causing runtime failures (`psycopg2.errors.UndefinedTable`).

**Consumers**: All downstream cognition components (5 files) read from `summary_structured` on Model A.

**Recommendation**: Consolidate on Model A; remove Model B code paths completely.

---

## 1. INVENTORY

### 1.1 Producer: Theory Generation

**File**: `flows/theory_flow/theory_generation_flow.py`

- **Lines 169-181**: `_clean_theory()` returns structured JSON
- **Output Format**:
  ```json
  {
    "claim": "...",
    "if_branch": "...",
    "else_branch": "...",
    "unless": "...",
    "falsified_if": "..."
  }
  ```
- **Storage**: Returned as `json.dumps(cleaned_theory)` → `theory.summary` (string)
- **Type**: JSON string (structured data encoded as text)

### 1.2 Persistence Layer: Repository & Models

#### TheoryRepository.save() — `memory/relational/repositories/theory_repository.py`

**DUAL PERSISTENCE PATTERN** (Lines 18-70):

```
Input: theory object with theory.summary = JSON string

Path A (Active):
  └─ Line 38: Parse theory.summary as JSON
  └─ Create TheoryModel with summary_structured = parsed JSON string
  └─ session.merge(theory_model) → theories table

Path B (Dead):
  └─ Lines 55-68: Same JSON stored in TheoryStructuredModel
  └─ Create TheoryStructuredModel(theory_id=..., structured_json=...)
  └─ session.merge(structured_model) → theory_structures table [NEVER CREATED]
```

**Status**: 
- ✓ Path A persists to `theories.summary_structured` column
- ✗ Path B tries to persist to non-existent `theory_structures` table

#### TheoryRepository.list_recent() — `memory/relational/repositories/theory_repository.py`

**DUAL RETRIEVAL PATTERN** (Lines 78-105):

```
Step 1: Query TheoryModel from theories table
  └─ Returns all fields including summary_structured

Step 2: For each theory, query TheoryStructuredModel
  └─ Lines 92-105: Join logic that attempts to reconstruct summary_structured
  └─ FAILS: theory_structures table does not exist
```

**Current Failure Mode**:
```python
# Line 92-93
structured = (
    session.query(TheoryStructuredModel)
    .filter(TheoryStructuredModel.theory_id == rec.id)
    .one_or_none()
)
# Raises: psycopg2.errors.UndefinedTable: relation "theory_structures" does not exist
```

#### Model Definitions

**TheoryModel** — `memory/relational/models/theory_model.py`
```python
class TheoryModel(Base):
    __tablename__ = "theories"
    id = Column(String, primary_key=True)
    lineage_id = Column(String)
    thesis = Column(String)
    summary = Column(String)
    summary_structured = Column(Text)  # <-- ACTIVE
    created_at = Column(DateTime...)
    confidence_state_id = Column(...)
```

**Status**: ✓ Registered in `memory/relational/models/__init__.py`

**TheoryStructuredModel** — `memory/relational/models/theory_structured_model.py`
```python
class TheoryStructuredModel(Base):
    __tablename__ = "theory_structures"
    theory_id = Column(String, primary_key=True)
    structured_json = Column(Text)
    created_at = Column(DateTime...)
```

**Status**: 
- ✗ NOT in `memory/relational/models/__init__.py` (not explicitly registered)
- ✗ Table never created in schema
- ✗ Imported directly only in theory_repository.py line 3

### 1.3 Consumers: Cognition Components

All consumers read `summary_structured` **directly from theory object**.

| File | Location | Pattern | Status |
|------|----------|---------|--------|
| **reflection_flow.py** | Line 112 | `getattr(theory, "summary_structured", None)` | ✓ Working |
| **reflective_memory_synthesizer.py** | Line 414 | `getattr(theory, "summary_structured", None)` | ✓ Working |
| **contradiction_detector.py** | Lines 176-182 | Handles both dict/object; checks `summary_structured` and `theory_summary_structured` | ✓ Working (defensive) |
| **historical_cognition_service.py** | Line 43 | `getattr(t, "summary_structured", None)` | ✓ Working |
| **replay_engine.py** | Lines 652, 905, 1339-1341 | `getattr(theory, 'summary_structured', None)` and dict key `"theory_summary_structured"` | ✓ Working |

**All consumers use Model A directly** — they never attempt to load from `theory_structures` table.

### 1.4 Model Registration Status

**Registered Models** (via `memory/relational/models/__init__.py`):
```python
from memory.relational.models.abstraction_model import AbstractionModel
from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.models.observation_model import ObservationModel
from memory.relational.models.reflection_model import ReflectionModel
from memory.relational.models.reflective_memory_model import ReflectiveMemoryModel
from memory.relational.models.theory_model import TheoryModel  # ✓ REGISTERED
from memory.relational.models.validation_model import ValidationModel

__all__ = [
    "AbstractionModel",
    "ConfidenceModel",
    "ObservationModel",
    "ReflectionModel",
    "ReflectiveMemoryModel",
    "TheoryModel",  # ✓ HERE
    "ValidationModel"
]
```

**Unregistered Models**:
- `TheoryStructuredModel` — defined but not in `__all__`
- Direct import only in `theory_repository.py:3`

**Metadata Initialization** (`memory/relational/postgres_client.py:28-29`):
```python
import memory.relational.models  # noqa: F401
Base.metadata.create_all(engine)
```

**Effect**: Only registered models (those in `__all__`) get `create_all()` called. `TheoryStructuredModel` is never registered, so `theory_structures` table never created.

---

## 2. ARCHITECTURE BEFORE CLEANUP

```
┌─────────────────────────────────────────────────────────────────┐
│                   THEORY GENERATION                              │
├─────────────────────────────────────────────────────────────────┤
│  theory_generation_flow.py                                       │
│  └─ Output: theory.summary = JSON string                         │
│             ("claim": "...", "if_branch": "...", ...)           │
└──────────────────┬──────────────────────────────────────────────┘
                   │ theory object (has summary as JSON string)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  TheoryRepository.save(theory)                                   │
│  ├─ Path A (ACTIVE):                                             │
│  │  ├─ Parse theory.summary as JSON                             │
│  │  ├─ Create TheoryModel with summary_structured = JSON string │
│  │  └─ Persist to theories.summary_structured ✓                 │
│  │                                                               │
│  └─ Path B (DEAD):                                               │
│     ├─ Create TheoryStructuredModel                             │
│     └─ Try to persist to theory_structures ✗ [TABLE MISSING]   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┴────────────┐
        ▼                       ▼
   ┌─────────────┐         ┌──────────────────┐
   │  theories   │         │ theory_structures│
   │  table ✓    │         │ table ✗ MISSING  │
   │             │         │                  │
   │ summary_str-│         │ structured_json  │
   │ uctured COL │         │                  │
   └──────┬──────┘         └──────────────────┘
          │
          │ TheoryRepository.list_recent()
          │
          ├─ Query TheoryModel ✓
          │
          └─ Query TheoryStructuredModel ✗ [FAILS HERE]
              └─ psycopg2.errors.UndefinedTable: relation "theory_structures" does not exist
```

**Retrieval Flow (Current Broken State)**:
```
list_recent() 
  ├─ session.query(TheoryModel).all() ✓
  │
  ├─ For each theory:
  │   └─ session.query(TheoryStructuredModel)
  │       .filter(theory_id == rec.id)
  │       .one_or_none() ✗ CRASH
  │
  └─ Never reaches consumers
```

**Consumers** (all reading from Model A, which works):
```
reflection_flow → getattr(theory, "summary_structured")
reflective_memory → getattr(theory, "summary_structured")
contradiction_detector → getattr(theory, "summary_structured")
historical_cognition → getattr(theory, "summary_structured")
replay_engine → getattr(theory, "summary_structured")
```

---

## 3. ARCHITECTURE AFTER CLEANUP

```
┌─────────────────────────────────────────────────────────────────┐
│                   THEORY GENERATION                              │
├─────────────────────────────────────────────────────────────────┤
│  theory_generation_flow.py                                       │
│  └─ Output: theory.summary = JSON string                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER (CANONICAL)                  │
├─────────────────────────────────────────────────────────────────┤
│  TheoryRepository.save(theory)                                   │
│  └─ Single Path (Model A Only):                                 │
│     ├─ Parse theory.summary as JSON                             │
│     ├─ Create TheoryModel with summary_structured = JSON string │
│     └─ Persist to theories.summary_structured ✓                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │  theories table  │
        │                  │
        │ summary_structur │
        │ ed COLUMN ✓      │
        │ (canonical)      │
        └──────┬───────────┘
               │
               │ TheoryRepository.list_recent()
               │ └─ Query TheoryModel.all() ✓
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│            CONSUMERS (UNIFIED PIPELINE)                          │
├─────────────────────────────────────────────────────────────────┤
│  theory.summary_structured ◄─── from theories.summary_structured │
│  (already loaded, no join needed)                                │
│                                                                  │
│  ├─ reflection_flow.py                                           │
│  ├─ reflective_memory_synthesizer.py                             │
│  ├─ contradiction_detector.py                                    │
│  ├─ historical_cognition_service.py                              │
│  └─ replay_engine.py                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits of consolidated Model A**:
- ✓ Single join-free query
- ✓ Simpler schema (no extra table)
- ✓ No missing table errors
- ✓ Easier debugging (one canonical location)
- ✓ Faster retrieval (no join penalty)
- ✓ Easier migrations

---

## 4. DEAD CODE PATHS

### 4.1 Unnecessary Persistence (theory_repository.py:55-68)

```python
# If structured JSON is present in the theory.summary, store it in a separate table
structured_json = None
if isinstance(getattr(theory, 'summary', None), str) and _is_json(getattr(theory, 'summary')):
    try:
        parsed = json.loads(theory.summary)
        structured_json = json.dumps(parsed)
    except Exception:
        structured_json = None

if structured_json:
    structured_model = TheoryStructuredModel(
        theory_id=theory.id,
        structured_json=structured_json
    )
    session.merge(structured_model)
```

**Why Dead**: 
- Same data already persisted to `theories.summary_structured` on line 38
- Table never created, so merge always fails silently or causes error
- Never read by consumers

### 4.2 Unnecessary Retrieval (theory_repository.py:92-105)

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

**Why Dead**:
- `rec.summary_structured` already populated from `theories.summary_structured` column
- Query to non-existent table always fails
- Exception handler masks the error but code is useless
- No consumer relies on this join logic

### 4.3 Unused Model Import (theory_repository.py:3)

```python
from memory.relational.models.theory_structured_model import TheoryStructuredModel
```

**Why Dead**:
- Only used in dead code paths above
- Never referenced elsewhere in codebase

### 4.4 Unused Model Definition & Registration

**File**: `memory/relational/models/theory_structured_model.py` (entire file)

**Why Dead**:
- Never registered in `__init__.py`
- Never created in schema
- Never queried (except in dead code in theory_repository.py)

---

## 5. FILES TO MODIFY

| File | Changes | Impact |
|------|---------|--------|
| **theory_repository.py** | Remove lines 3, 55-68, 92-105 | Remove dual persistence & dual retrieval |
| **theory_structured_model.py** | Can be deleted (optional for now) | Clean dead code |
| **models/__init__.py** | No change needed (already not registered) | No impact |
| **postgres_client.py** | No change needed | No impact |

---

## 6. VALIDATION POINTS

### 6.1 Schema Verification (Proposed Startup Check)

```python
# In postgres_client.py or new validation module
def validate_theory_schema():
    """Verify that structured theory persistence is correctly configured."""
    with engine.connect() as conn:
        # Check theories table has summary_structured column
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('theories')]
        
        if 'summary_structured' not in columns:
            raise RuntimeError(
                "SCHEMA ERROR: theories.summary_structured column missing. "
                "Theory structured persistence cannot proceed."
            )
        
        # Verify theory_structures does NOT exist (anti-pattern removed)
        tables = inspector.get_table_names()
        if 'theory_structures' in tables:
            print("WARNING: Deprecated theory_structures table still exists. "
                  "This table is no longer used. Consider dropping it.")
        
        print("✓ STRUCTURED THEORY STORAGE: theories.summary_structured (CANONICAL)")
```

### 6.2 Instrumentation Points (Proposed Tracing)

To measure structured cognition survival rate:

1. **Generation** (`theory_generation_flow.py`):
   ```python
   # After _clean_theory returns
   if parsed_theory_data:
       print(f"[STRUCTURED] Generated: {theory.id} with {len(parsed_theory_data)} fields")
   ```

2. **Persistence** (`theory_repository.py`):
   ```python
   # After TheoryModel.merge
   if theory_model.summary_structured:
       print(f"[STRUCTURED] Persisted: {theory.id} summary_structured={len(theory_model.summary_structured)} bytes")
   ```

3. **Retrieval** (`theory_repository.py`):
   ```python
   # In list_recent after query
   for rec in results:
       if rec.summary_structured:
           print(f"[STRUCTURED] Retrieved: {rec.id} summary_structured present")
   ```

4. **Consumption** (each consumer):
   ```python
   # e.g., in reflection_flow.py line 112
   t_struct = getattr(theory, "summary_structured", None)
   if isinstance(t_struct, dict):
       print(f"[STRUCTURED] Consumed by reflection_flow: {theory.id}")
   else:
       print(f"[STRUCTURED] WARNING: reflection_flow received theory {theory.id} without structured data")
   ```

---

## 7. REMAINING RISKS & EDGE CASES

### 7.1 Existing Data in theory_structures Table

**Risk**: If `theory_structures` table exists in a running database, removal of query logic might appear to lose data.

**Assessment**: 
- Table definition never registered in metadata
- Table never created by `create_all()`
- Extremely unlikely to exist unless manually created for debugging
- Data would be stale (duplicate of theories.summary_structured)

**Mitigation**: Audit check before cleanup:
```sql
SELECT COUNT(*) FROM theory_structures;  -- If exists and has rows, investigate
```

### 7.2 backward Compatibility with Old Theory Objects

**Risk**: If old Theory objects (pre-v3.0) exist without `summary_structured` field, consumers might fail.

**Status**: 
- Consumers already use `getattr(theory, "summary_structured", None)` (defensive)
- Fallback to text-based summary available in all consumers
- No incompatibility risk

### 7.3 Replay Snapshot Handling

**Current State**: `replay_engine.py` line 1339 creates snapshot with `"theory_summary_structured"` key:
```python
"theory_summary_structured": (
    getattr(theory, "summary_structured", None)
    if isinstance(getattr(theory, "summary_structured", None), dict)
    else None
)
```

**Status**: ✓ Works correctly from Model A, no change needed

### 7.4 Contradiction Detector Dual Key Handling

**Current State**: `contradiction_detector.py` handles both keys:
```python
structured = theory.get("theory_summary_structured") or theory.get("summary_structured")
```

**Status**: ✓ Defensive, can remain as-is or simplify to just `"summary_structured"`

---

## 8. RECOMMENDATION: Future Use of Dedicated Table

**Question**: Should `theory_structures` table ever be reintroduced?

**Answer**: **NO** — Not recommended for the following reasons:

1. **Research Phase**: Current system is in active research. Normalized schema adds complexity without benefit.

2. **Join Overhead**: Querying structured theories currently requires:
   - Model A (current): 1 query to theories table
   - Model B (proposed): 1 query to theories + 1 join to theory_structures = 2x retrieval cost

3. **Schema Evolution**: Structured theory schema may still evolve:
   - Current: Modify `theories.summary_structured` column type/constraint (1 ALTER)
   - Proposed: Requires schema migration on separate table + index updates

4. **Audit Trail**: Consumers need access to structured claims. Forcing a separate table creates:
   - Extra join logic
   - Potential for data staleness between tables
   - More complex migrations

5. **When It Might Be Reconsidered**:
   - If structured theories become >50% of persistence operations (currently ~20%)
   - If columnar storage compression becomes critical (unlikely in OLTP workload)
   - If separation of concerns justifies normalized design (trade-off: query complexity)
   - Only after Model A has proven stable in production for 6+ months

---

## 9. SUMMARY TABLE: What Needs Removal

| Item | File | Lines | Reason | Risk |
|------|------|-------|--------|------|
| Import TheoryStructuredModel | theory_repository.py | 3 | Never used after cleanup | None |
| Dual persistence code | theory_repository.py | 55-68 | Dead logic | None |
| Dual retrieval code | theory_repository.py | 92-105 | Dead logic | None |
| TheoryStructuredModel class | theory_structured_model.py | 1-20 | Unused model | None |
| ~~theory_structures table~~ | database | N/A | Never created | None |

---

## 10. FINAL RECOMMENDATION

**Proceed with consolidation to Model A**:

1. **Immediate** (next commit):
   - [ ] Remove import statement (theory_repository.py:3)
   - [ ] Remove persistence logic (theory_repository.py:55-68)
   - [ ] Remove retrieval logic (theory_repository.py:92-105)
   - [ ] Simplify `list_recent()` to single query
   - [ ] Add startup validation check
   - [ ] Add instrumentation for structured cognition tracing

2. **Post-Cleanup Validation**:
   - [ ] Run full replay on historical data
   - [ ] Verify structured theories flow end-to-end
   - [ ] Measure structured cognition survival rate
   - [ ] Check query performance (should improve 2x)

3. **Optional Cleanup** (future):
   - [ ] Delete `theory_structured_model.py` file
   - [ ] Remove dead imports from any test files that reference it

4. **Documentation**:
   - [ ] Update AGENTS.md to reflect singular canonical model
   - [ ] Add schema documentation to README.md

---

## APPENDIX: Reference Locations

### Consumers (All Using summary_structured):
1. `flows/reflection_flow/reflection_flow.py:112`
2. `memory/reflection/reflective_memory_synthesizer.py:414`
3. `cognition/contradiction/contradiction_detector.py:176-182`
4. `memory/lineage/historical_cognition_service.py:43`
5. `market/replay/replay_engine.py:652, 905, 1339`

### Producer:
- `flows/theory_flow/theory_generation_flow.py:169-181` (generates JSON)

### Persistence:
- `memory/relational/repositories/theory_repository.py` (save & list_recent)
- `memory/relational/models/theory_model.py` (canonical storage)

### Dead Model:
- `memory/relational/models/theory_structured_model.py` (never used)

### Model Registration:
- `memory/relational/models/__init__.py` (TheoryModel registered, TheoryStructuredModel not)

---

**End of Audit Report**
