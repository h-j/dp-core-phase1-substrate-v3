# Planned Infrastructure — Activation Pathways

This document describes stub infrastructure modules in DP-Core Phase 1B
that are retained for future integration but not yet activated.

> [!NOTE]
> These stubs make no external calls and have no runtime cost.
> Do not activate without an explicit milestone decision.

## Stub Modules (Phase 8 — 2026-07-20)

### `memory/market/parquet_store.py` — ParquetStore
**Status:** STUB — `save()` returns `{"status": "saved"}` without writing files.

**Planned purpose:** Efficient columnar storage of market replay snapshots
for fast retrospective analytics. Currently, snapshots are stored as JSON
under `data/replay_snapshots/`.

**Activation conditions:**
- Milestone decision to add replay analytics beyond current JSON snapshots.
- `pyarrow` added as dependency.
- `ParquetStore` integrated into `ReplayExecutor` snapshot write path.

---

### `memory/vector/vector_store.py` — VectorStore
**Status:** STUB — `store()` returns `{"status": "stored"}` without writing.

**Planned purpose:** Embedding-based similarity search for theory retrieval.

**Activation conditions:**
- Explicit decision to add embedding-based memory retrieval.
- `AGENTS.md` constraint: *"No embeddings/vector DBs unless explicitly requested."*
- This module must never be activated without overriding the `AGENTS.md` doctrine.

---

### `memory/vector/embedding_provider.py` — EmbeddingProvider
**Status:** STUB — `embed()` returns `[0.0]`.

**Planned purpose:** Provide embeddings for `VectorStore`.

**Activation conditions:** Same as `VectorStore` above.

---

### `memory/vector/semantic_memory_store.py` — SemanticMemoryStore
**Status:** STUB — `search()` returns `[]`.

**Planned purpose:** Semantic search over theory corpus.

**Activation conditions:** Same as `VectorStore` above.
