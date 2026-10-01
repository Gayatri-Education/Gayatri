# Agent Development Rules & Code Invariants — Gayatri Platform

**Document:** `docs/AGENT_DEVELOPMENT_RULES.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** ACTIVE & MANDATORY  

---

## 1. Core Operating Principles for AI Agents

1. **Phase-by-Phase Discipline:**
   - Execute strictly **one phase at a time** in the exact sequential order defined in `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`.
   - Before executing any phase: create `docs/reports/PHASE_<NN>_PLAN.md`, present the plan, and solicit user approval.
   - Do NOT skip to later phases or declare success based on partial implementation.

2. **Honest & Reproducible Evidence:**
   - A passing test is evidence ONLY for what it specifically asserted.
   - Never report "production ready" merely because a test suite passed.
   - Every phase requires empirical test execution, failure/negative testing, and machine-readable reports (`PHASE_<NN>_TEST_RESULTS.json`).

3. **Anti-False-Green Testing Standards:**
   - NEVER weaken assertions to make failing tests pass.
   - NEVER skip failing tests with `@pytest.mark.skip` or `xfail` without explicit justification.
   - NEVER swallow exceptions in production code or tests (`try...except Exception: pass` is prohibited).

---

## 2. Non-Negotiable Architectural Invariants

### Invariant 1: Course Independence & Subject Neutrality
- Generic core modules under `core/`, `central_platform/`, and `app/` MUST NOT contain hardcoded subject keywords (`chemistry`, `thermodynamics`, `hess`, `ncert`, `chemical`, `crs-chem-101`).
- All subject-specific tools, misconception catalogs, and curriculum models belong in domain adapters (e.g. `adapters/chemistry/`).
- The generic platform MUST boot, initialize courses, and tutor non-chemistry subjects even if `adapters/chemistry/` is absent.

### Invariant 2: Zero Legacy Imports
- Active production code MUST NOT import from `legacy.*`.
- All AI inference and context construction must route through the canonical `AI Gateway` (`central_platform.ai`).
- When all callers are eradicated, `legacy/` will be permanently deleted.

### Invariant 3: Zero Hardcoded Fake Rosters in Production
- Production runtime and bridge code MUST NOT seed fake students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`, `local_user_1`, `local_student_1`).
- Empty databases or unassigned rosters MUST render clear, honest empty states.
- Demo fixtures belong strictly in `tests/fixtures/` or an explicit `--demo` launcher mode.

### Invariant 4: Deterministic Schema Evolution
- Schema changes MUST occur strictly through numbered SQL scripts in `migrations/` accompanied by corresponding down scripts.
- Runtime dynamic DDL (`ALTER TABLE` executed on connection setup) is strictly prohibited.

### Invariant 5: Pre-Retrieval Authorization in RAG
- Authorization filters (Organization, Course, Course Version, Class Group, Student Remedial Scope, and Publication Status) MUST be applied before vector/lexical retrieval.
- Unauthorized chunks must never enter the candidate set and cannot be filtered post-hoc in the UI.

### Invariant 6: Immutable Course Content & Pinned Versions
- Published course versions are immutable. Content updates produce a new course version in `DRAFT`.
- Historical student learning sessions remain permanently pinned to the version they utilized.

### Invariant 7: Server-Side Tool Authorization
- Course tools are enabled per course version via `CourseToolPolicy`.
- Tool execution MUST be verified server-side at the AI Gateway. The client UI cannot grant itself capabilities.

---

## 3. Mandatory Phase Checklist

Every phase must satisfy this checklist before marking `PHASE_STATUS = VERIFIED`:

- [ ] Plan written in `docs/reports/PHASE_<NN>_PLAN.md` and approved by user.
- [ ] Code implemented cleanly with focused commits.
- [ ] Unit and integration tests written and passing.
- [ ] Negative and boundary tests written and passing.
- [ ] Real application boundary verified.
- [ ] Bytecode compilation passes with 0 errors (`python -m compileall`).
- [ ] Architecture guard tests pass (`pytest tests/architecture`).
- [ ] `docs/reports/PHASE_<NN>_TEST_REPORT.md` written with exact commands and results.
- [ ] `docs/reports/PHASE_<NN>_TEST_RESULTS.json` generated.
- [ ] `PROJECT_STATE.yaml` updated to match reality.
- [ ] `docs/reports/DEVELOPMENT_LOG.md` appended with chronological entry.
- [ ] `docs/reports/BUG_REGISTER.md` updated with any discoveries or fixes.
- [ ] Git commit created and pushed to remote `origin`.
