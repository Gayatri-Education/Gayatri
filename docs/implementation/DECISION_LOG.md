# V2 Platform Architectural Decision Log (ADR)

Authoritative log of design decisions, architectural choices, and rationale for the Gayatri AI V2 Platform Reconciliation.

---

## ADR-0001: Central PostgreSQL as Single Authoritative Truth
- **Date**: 2026-09-27
- **Status**: ACCEPTED (Master Plan Contract)
- **Context**: Previously, student profiles lived as disconnected local JSON (`student_profile.json`) or ad-hoc SQLite tables in `central_platform.db`.
- **Decision**: Central PostgreSQL becomes the authoritative single source of truth for all users, enrollments, learning events, SLR, assessments, and teacher directives. Local SQLite / JSON files are strictly limited to local client-side caching and offline queueing.
- **Consequences**: Direct DB access from frontend clients is strictly disallowed. All mutations flow through validated `/api/v1/*` platform APIs.

---

## ADR-0002: Preservation of Validated Core Chemistry & Adaptive Intelligence
- **Date**: 2026-09-27
- **Status**: ACCEPTED (Master Plan Contract § 1.3)
- **Context**: The existing BKT (`core/tutor/adaptive.py`), LDG, assessment engine, misconception catalog, and NCERT chemistry RAG pipelines are empirically validated across 411 tests.
- **Decision**: Core learning intelligence will NOT be rewritten or dismantled. Instead, it will be wrapped by the central event pipeline and SLR layer in Phase 07, ensuring complete continuity of pedagogical logic.
- **Consequences**: Existing benchmarks remain frozen and regression suites protect all pedagogical algorithms.

---

## ADR-0003: Strict Zero-Warning and Empirical Gate Policy
- **Date**: 2026-09-27
- **Status**: ACCEPTED (Master Plan Contract § 1.5)
- **Context**: In previous phases, code existing was occasionally confused with complete integration, leading to runtime deadends.
- **Decision**: No phase can be marked `VERIFIED` without: (1) passing all unit and integration tests with zero failures and zero warnings, (2) running end-to-end user boundary verification (`scripts/verify_sync.py`), and (3) tracking all bugs in `DEBUGGING_REGISTER.md`.
- **Consequences**: Highest reliability, guaranteed reproducibility before GitHub pushes.
