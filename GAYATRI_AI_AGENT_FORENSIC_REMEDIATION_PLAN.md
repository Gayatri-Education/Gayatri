# Gayatri — AI Agent Forensic Remediation & Production Hardening Plan

**Repository:** `Gayatri-Education/Gayatri`
**Canonical branch declared by project:** `master`
**Audit basis:** `GAYATRI_DEEP_FORENSIC_AUDIT_REPORT_2026-10-02.md`
**Execution mode:** local AI coding agent + GitHub + local runtime
**Objective:** repair every confirmed defect without breaking previously working behavior, and do not advance to the next phase until the current phase has been independently verified.

---

## 0. READ THIS FIRST — NON-NEGOTIABLE AGENT RULES

You are not being asked to “make tests pass.” You are being asked to make the **actual system correct**.

The repository contains tests that currently validate behavior that the newer product contract forbids. Therefore:

> **Never treat an existing green test as proof that the behavior is correct.**

A feature is complete only when all of the following are true:

1. Code path is implemented.
2. Correct production dependency is actually used.
3. Positive behavior works.
4. Negative/security behavior works.
5. Failure behavior is explicit and safe.
6. Persistence behavior is correct after restart.
7. Cross-student and cross-course isolation is proven.
8. No legacy/fallback path bypasses the invariant.
9. Existing legitimate behavior still works.
10. Tests have been reviewed for correctness against the current contract.
11. GitHub CI passes from a clean environment.
12. The phase evidence is recorded in this document and committed.

### Forbidden completion language

Do not write:

- “probably fixed”
- “should work”
- “tests pass so done”
- “mock proves integration”
- “endpoint exists so feature works”
- “fallback is harmless”
- “legacy code is unused” without proving reachability
- “production ready” without runtime evidence

Use only:

- `IMPLEMENTED`
- `TESTED`
- `RUNTIME_VERIFIED`
- `SECURITY_VERIFIED`
- `REGRESSION_VERIFIED`
- `BLOCKED`

A phase is `COMPLETE` only when all required gates pass.

---

# 1. Current Forensic Baseline

The forensic audit found the repository is **not currently production-verifiable**.

## Confirmed critical defects

| ID | Area | Severity | Core defect |
|---|---|---:|---|
| F-001 | Authentication | P0 | Protected APIs can operate without authentication |
| F-002 | Identity | P0 | Caller-supplied `student_id` is not bound to authenticated identity |
| F-003 | Tutor lifecycle | P1 | Tutor can create users/sessions/enrollments automatically |
| F-004 | Defaults | P1 | Chemistry/default identities still exist in current paths |
| F-005 | RAG | P0 | Missing RAG can fall back to hardcoded Chemistry answer |
| F-006 | RAG | P0 | Core retriever can undo metadata filtering |
| F-007 | RAG API | P0 | RAG query/chunk paths lack adequate authorization |
| F-008 | RAG versioning | P1 | Version-pinned retrieval can accept unversioned content |
| F-009 | RAG relevance | P1 | Concept-scoped retrieval includes generic/empty concept chunks |
| F-010 | Context | P1 | Context failures are swallowed and tutor continues |
| F-011 | Adaptive learning | P0 | Mastery increases from valid AI response instead of learner evidence |
| F-012 | Misconceptions | P1 | Misconceptions are not consistently course-scoped |
| F-013 | AI gateway | P0 | Provider failure can silently become mock success |
| F-014 | Transactions | P0 | “Atomic” learning commit is not truly atomic |
| F-015 | SLR | P1 | SLR contains Chemistry/default fabricated fallback state |
| F-016 | Sync | P1 | Sync manager uses in-memory deduplication and weak binding |
| F-017 | Assessment | P1 | Assessment service auto-provisions users/courses |
| F-018 | Assessment | P1 | Subjective grading is heuristic keyword/length scoring with fixed confidence |
| F-019 | Production gate | P0 | Readiness checks prove object existence more than real runtime behavior |
| F-020 | CI/release | P0 | Claimed verified state conflicts with actual CI and branch state |
| F-021 | Branching | P1 | `main` and declared canonical `master` diverged |
| F-022 | Test contract | P0 | Tests encode behavior that the current contract forbids |
| F-023 | Context | P1 | Missing learner/course context can be synthesized instead of rejected |
| F-024 | RAG | P1 | Legacy fallback scans unscoped JSON knowledge files |
| F-025 | Database | P1 | Production architecture is SQLite-centric despite PostgreSQL claims |

These findings are the starting point. Do not close them merely by changing tests.

---

# 2. Master Remediation Strategy

The repair must proceed in dependency order.

```text
PHASE 0  Baseline + branch + CI truth
   ↓
PHASE 1  Authentication + identity binding
   ↓
PHASE 2  Course/enrollment/version/context resolution
   ↓
PHASE 3  RAG authorization + strict retrieval + fallback removal
   ↓
PHASE 4  AI gateway + explicit failure semantics
   ↓
PHASE 5  Transactional learning state + SLR correctness
   ↓
PHASE 6  Evidence-based adaptive learning
   ↓
PHASE 7  Assessment correctness + learner evidence
   ↓
PHASE 8  Sync/offline/device/idempotency
   ↓
PHASE 9  Analytics + portals + privacy isolation
   ↓
PHASE 10 Legacy/dead-end removal + route/reachability audit
   ↓
PHASE 11 Production runtime / deployment / database validation
   ↓
PHASE 12 Full forensic regression + release certification
```

Do **not** reorder these casually. Later phases depend on earlier invariants.

---

# 3. Global Progress Tracker

Copy this section into the repository as the working status table and update it after every phase.

| Phase | Status | Code | Tests | Runtime | Security | Regression | Commit | Evidence |
|---|---|---|---|---|---|---|---|---|
| 0 Baseline/Truth | NOT_STARTED | ☐ | ☐ | ☐ | N/A | ☐ | ☐ | ☐ |
| 1 Auth/Identity | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 Context/Enrollment | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 RAG | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 AI Gateway | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 State/SLR/Transactions | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 Adaptive Learning | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 Assessment | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 Sync/Offline | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 Analytics/Portals | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 Legacy/Dead Ends | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 11 Production Runtime | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 12 Final Certification | NOT_STARTED | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

### Status definitions

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `IMPLEMENTED`
- `TESTED`
- `RUNTIME_VERIFIED`
- `COMPLETE`

Never use `COMPLETE` without evidence.

---

# 4. Universal Change Protocol

Every phase must follow this exact loop.

## Step A — Inspect before modifying

```bash
git status --short
git branch --show-current
git log --oneline -10
python --version
python -m pip list
```

Then inspect:

- imports
- call graph
- route registration
- dependencies
- persistence layer
- tests
- environment configuration
- legacy aliases
- feature flags
- fallback paths

Do not edit until the agent can explain the current execution path.

## Step B — Create a phase branch

```bash
git checkout master
git pull --ff-only
git checkout -b fix/phase-XX-short-name
```

Never develop directly on `master`.

## Step C — Capture baseline

Before changes:

```bash
python -m compileall .
pytest -q
```

If baseline fails, record the exact failure. Do not hide it.

Also run the narrowest relevant tests.

## Step D — Fix implementation, not symptoms

If a test fails because it encodes the old behavior:

1. inspect the governing contract;
2. decide the intended behavior;
3. update the test to represent the correct contract;
4. add a regression test for the old bug;
5. implement the fix.

Never weaken production code merely to satisfy a stale test.

## Step E — Add adversarial tests

Every positive test must have a negative counterpart.

Example:

```text
student A can read own course
student A cannot read student B's course
student A cannot spoof student B's ID
unauthenticated request is rejected
expired token is rejected
wrong organization is rejected
wrong class is rejected
wrong version is rejected
missing context fails explicitly
provider failure fails explicitly
restart preserves state
replay does not duplicate state
```

## Step F — Run focused tests

```bash
pytest -q tests/<relevant tests>
```

## Step G — Run integration tests

```bash
pytest -q
```

## Step H — Test actual runtime

Do not rely only on `TestClient`.

Start the real application using the same entrypoint used in deployment, then exercise HTTP requests through the real server.

## Step I — Inspect the diff

```bash
git diff --check
git diff --stat
git diff
```

Check for:

- accidental deletion
- new fallback
- hardcoded IDs
- debug code
- credentials
- disabled auth
- broad `except`
- test-only behavior leaking into production

## Step J — Commit only after evidence

Commit format:

```text
fix(phase-XX): <specific invariant repaired>
```

Push branch.

## Step K — Update this plan

Record:

- changed files
- tests added
- tests run
- runtime evidence
- security evidence
- known limitations
- commit SHA
- next phase

Only then move forward.

---

# 5. PHASE 0 — Establish Ground Truth

## Objective

Stop repository state/documentation/CI contradictions before changing application logic.

## Required inspection

Inspect:

- `PROJECT_STATE.yaml`
- `PROGRESS_TRACKER.yaml`
- `CURRENT_REPO_AUDIT.md`
- `GAYATRI_V2_PLATFORM_RECONCILIATION_PRODUCTION_MASTER_PLAN.md`
- `.github/workflows/*`
- `pyproject.toml`
- `requirements*.txt`
- Docker/deployment files
- Git branches
- GitHub Actions

## Required work

### 0.1 Resolve canonical branch policy

Choose one explicit policy:

- `master` canonical, `main` mirror; or
- `main` canonical and update all documentation.

Do not leave two divergent sources of truth.

If `master` remains canonical, determine whether the five commits on `main` are valid work that must be merged or obsolete work that must be removed.

Never force-reset a branch before inspecting its commits.

### 0.2 Make CI reproducible

Create a clean environment and install dependencies from the repository's declared dependency source.

The current audit observed collection failures including missing `jwt`, `fastapi`, and `psutil`.

Determine whether:

- dependencies are missing;
- wrong package names are used;
- optional dependencies are incorrectly imported at module import time;
- CI uses the wrong Python version;
- local environment is hiding dependency errors.

### 0.3 Separate verification claims

Replace vague state claims such as:

`PRODUCTION_RELEASE_READY`

with explicit fields:

```yaml
implemented: false
tested: false
runtime_verified: false
security_verified: false
regression_verified: false
production_ready: false
```

### 0.4 Add repository verification manifest

Create:

`docs/verification/VERIFICATION_STATE.yaml`

It must contain per-phase:

- status
- commit
- test command
- test result
- runtime result
- security result
- evidence path
- reviewer/agent timestamp

## Exit gate

- clean dependency installation works;
- CI reaches tests;
- branch policy is documented;
- no false production-ready claim remains;
- baseline failures are recorded.

---

# 6. PHASE 1 — Authentication and Identity Binding

## Objective

Make every protected operation require a real authenticated principal and bind identity to the authenticated user.

## Primary files to inspect

- `central_platform/auth/dependencies.py`
- `central_platform/auth/tokens.py`
- `central_platform/security/*`
- `central_platform/api/routes/*`
- `central_platform/tutor/*`
- `central_platform/rag/*`
- `central_platform/learning/*`
- `central_platform/sync/*`

## Required invariants

### I1 — Protected route means authenticated

Create/use a strict dependency such as:

```python
get_current_user()
```

not optional.

Public routes must be explicitly documented as public.

### I2 — Identity is server-derived

For student operations:

```text
authenticated_user.id == student_id
```

Do not trust `student_id` supplied by the client.

For teacher/admin operations, verify:

```text
principal.organization_id
principal.role
resource.organization_id
```

### I3 — Never authenticate by request body

Do not use:

- body `student_id`
- query `student_id`
- path `student_id`

as proof of identity.

They can be resource selectors only after the principal is authenticated and authorized.

### I4 — Remove demo authentication from production routes

Search for:

```text
demo_token
demo_user
demo_student
default user
anonymous
optional auth
```

If a demo mode is required, isolate it behind an explicit development-only flag and make production fail closed.

### I5 — JWT secret must come from environment/secret manager

No hardcoded production signing secret.

Reject startup when production secret is absent.

### I6 — Token revocation must persist

If revocation exists only in memory, replace it with a durable mechanism appropriate to deployment.

## Tests to add

- unauthenticated tutor → `401`
- malformed token → `401`
- expired token → `401`
- valid student → own resources only
- student A requesting student B → `403`
- teacher from org A requesting org B → `403`
- admin from org A requesting org B → `403`
- forged body `student_id` → rejected
- forged query `student_id` → rejected
- token role mismatch → rejected
- token organization mismatch → rejected
- production startup without JWT secret → fails safely

## Runtime verification

Use actual HTTP server, not only `TestClient`.

Capture request/response evidence without logging secrets.

## Exit gate

No protected route may be reachable without a valid principal.

---

# 7. PHASE 2 — Course, Enrollment, Version, Class and Context Resolution

## Objective

Eliminate invented context and make tutor requests depend on real platform state.

## Primary files

- `central_platform/tutor/orchestrator.py`
- `central_platform/api/routes/tutor.py`
- `central_platform/courses/service.py`
- `central_platform/curriculum/*`
- `central_platform/learning/state.py`
- `central_platform/slr/service.py`
- `central_platform/ai/context_builder.py`

## Required behavior

A tutor turn must resolve:

```text
principal
→ student
→ organization
→ course
→ active enrollment
→ pinned/published course version
→ class/cohort where required
→ curriculum
→ concept
→ learner state
→ teacher instructions
→ authorized RAG scope
→ tool policy
→ AI provider
→ telemetry
```

If any required value cannot be resolved:

```text
DO NOT GUESS
DO NOT CREATE
DO NOT FALL BACK TO CHEMISTRY
RETURN EXPLICIT ERROR/CONTEXT_REQUIRED
```

## Remove from normal tutor execution

- automatic student creation
- automatic enrollment
- invented course
- invented course version
- invented session owner
- default Chemistry concept
- default organization
- default SLR

Provisioning belongs in explicit account/enrollment APIs.

## Session rules

A tutor turn may create a session only if:

- the authenticated student owns it;
- the course is authorized;
- the course version is resolved;
- session creation is an allowed lifecycle operation.

Otherwise reject.

## ContextBuilder rules

Do not silently swallow:

```python
except Exception:
    logger.warning(...)
    continue
```

For required context layers:

```text
success → continue
expected absence → explicit empty state
required failure → CONTEXT_REQUIRED / CONTEXT_ERROR
```

Do not turn infrastructure failure into “valid context with fewer fields.”

## Tests

- nonexistent course
- unpublished version
- missing enrollment
- inactive enrollment
- wrong organization
- wrong class
- missing curriculum
- ambiguous version
- missing concept
- missing learner state
- teacher instruction lookup failure
- context DB failure

Every failure must be explicit and safe.

---

# 8. PHASE 3 — RAG Authorization, Retrieval and Grounding

## Objective

Make RAG authoritative, course/version/class/student scoped, fail-closed, and impossible to bypass through legacy paths.

## Primary files

- `central_platform/rag/service.py`
- `central_platform/rag/security.py`
- `central_platform/api/routes/rag.py`
- `core/rag/retriever.py`
- `core/rag/store.py`
- `core/rag/seeder.py`
- `central_platform/ai/context_builder.py`

## Critical repair 3.1 — Remove hardcoded Chemistry fallback

Delete/disable this behavior from production execution:

```text
chunk-thermo-01
ncert_chem_11_ch6
Delta U = q + w
Thermodynamics
```

A missing RAG result must produce:

```json
{
  "status": "RAG_UNAVAILABLE",
  "count": 0,
  "results": [],
  "data_context": ""
}
```

or an explicit `CONTEXT_REQUIRED` response if the tutor contract requires grounding.

### Never do

```text
RAG_EMPTY → global Chemistry JSON → fabricated success
```

## Critical repair 3.2 — Remove retrieve-anyway fallback

In `core/rag/retriever.py`, this pattern is forbidden:

```python
if not filtered_candidates:
    filtered_candidates = vector_candidates
```

Correct behavior:

```text
metadata mismatch → zero results
```

## Critical repair 3.3 — Authorization before retrieval

The query pipeline must be:

```text
authenticate
→ authorize course
→ resolve version
→ resolve class
→ resolve student-targeting
→ build allowed filter
→ retrieve only allowed chunks
→ rerank
→ return evidence
```

Never:

```text
retrieve everything
→ filter afterward
```

## Critical repair 3.4 — Exact version semantics

If request specifies `course_version_id`:

```text
chunk.version == requested.version
```

No null-version escape.

If version cannot be determined:

```text
RAG_UNAVAILABLE / CONTEXT_REQUIRED
```

## Critical repair 3.5 — Exact concept semantics

If concept scope is requested, generic/unclassified chunks must not silently become equivalent to concept-specific chunks.

Use explicit policy:

- exact concept
- explicitly declared allowed general material
- otherwise reject/empty

Do not treat empty concept as universally matching.

## Critical repair 3.6 — RAG API authorization

Require authenticated principal for:

- query
- source listing where private data may appear
- chunk inspection
- source metadata
- ingestion
- publish
- validate

Apply role and organization rules.

## Critical repair 3.7 — Legacy JSON RAG

Inventory all:

```text
data/rag/*.json
data/rag/ncert_*.json
core/rag/*
central_platform/rag/*
```

Decide one authoritative path.

If legacy data remains for migration:

- mark read-only;
- require explicit migration flag;
- never use automatically from production tutor path;
- remove from default imports.

## RAG adversarial tests

### Positive

- enrolled student retrieves own course textbook
- correct version retrieved
- correct class note retrieved
- targeted remedial content retrieved by target student
- approved/published content retrieved

### Negative

- unauthenticated query → 401
- other organization → denied
- non-enrolled private course → denied
- wrong class → empty
- wrong version → empty
- wrong student-targeted asset → empty
- unpublished asset → empty
- empty index → RAG_UNAVAILABLE
- provider/RAG DB error → explicit error
- query injection → sanitized
- document prompt injection → data-only framing
- legacy Chemistry fallback impossible

---

# 9. PHASE 4 — AI Gateway and Model Failure Semantics

## Objective

A model response must mean an actual configured model provider succeeded.

## Primary files

- `central_platform/ai/gateway.py`
- provider adapters
- model routing
- settings/config
- tutor orchestrator

## Critical defect

The gateway can fall back to `mock_engine` after real provider failure.

This is unacceptable for production.

## Required provider states

```text
MODEL_SUCCESS
MODEL_UNAVAILABLE
MODEL_TIMEOUT
MODEL_RATE_LIMITED
MODEL_CONFIGURATION_ERROR
MODEL_INVALID_RESPONSE
```

Do not convert failure into success.

## Mock provider policy

Mocks may exist only in tests.

Production runtime must fail startup or request execution if the selected provider is unavailable, depending on product requirements.

The response must include machine-readable provenance:

```json
{
  "provider": "openai|anthropic|gemini|local|...",
  "model": "...",
  "mock": false
}
```

Never expose secrets.

## Tests

- real provider success
- provider timeout
- provider 500
- invalid response
- rate limit
- missing credentials
- mock accidentally configured in production
- provider rotation behavior
- fallback provider if explicitly configured
- all providers unavailable

If all providers fail:

```text
Tutor must not fabricate a successful AI turn.
```

---

# 10. PHASE 5 — Transactional Learning State and Authoritative SLR

## Objective

Make learning-state mutation truly atomic and make SLR reflect actual evidence.

## Primary files

- `central_platform/learning/commit_pipeline.py`
- `central_platform/learning/state.py`
- `central_platform/slr/service.py`
- `central_platform/events/store.py`
- `central_platform/db.py`

## Critical defect

The current “atomic” pipeline performs multiple DB operations that can commit independently.

A failure after write 1 can leave write 1 persisted even though the API reports failure.

## Required transaction model

All related mutations must occur inside one DB transaction:

```text
BEGIN
  learning event
  mastery state
  misconception state
  SLR update
  recommendation state
  telemetry
COMMIT
```

Any failure:

```text
ROLLBACK ALL
```

## Required idempotency

Every externally submitted learning event must have a durable unique identifier.

Database-level uniqueness is required.

Do not rely only on Python sets.

## SLR rules

Remove fabricated defaults such as:

- Chemistry course
- Chemistry concept
- fake 50% mastery
- fake 85% retention
- synthetic enrollment

If there is no learning evidence:

```text
mastery = unknown / insufficient evidence
```

not a fabricated numeric baseline.

## Course scoping

Misconceptions, mastery, recommendations, events and assessments must be scoped correctly to:

```text
student + organization + course + course_version + concept
```

as applicable.

## Failure injection tests

Write a DB fault injector that fails after each persistence step.

Verify:

```text
failure at step 1 → zero writes
failure at step 2 → zero writes
...
failure at final step → zero writes
```

Then verify successful transaction commits all records.

---

# 11. PHASE 6 — Evidence-Based Adaptive Learning

## Objective

Replace fake adaptive behavior with real learner-evidence-driven progression.

## Primary files

- `central_platform/learning/mastery.py`
- `central_platform/learning/state.py`
- `central_platform/learning/graph.py`
- `central_platform/assessment/adaptive.py`
- `central_platform/tutor/orchestrator.py`
- `central_platform/analytics/service.py`

## Critical defect

Current tutor flow can increase mastery because the **AI response passed validation**.

That is not evidence of student learning.

## Correct evidence flow

```text
student asks
→ tutor explains
→ tutor asks student
→ student answers
→ answer evaluated
→ evidence event recorded
→ mastery engine updates
→ misconception engine updates
→ next action selected
```

A tutor response alone must not increase mastery.

## Mastery evidence must distinguish

- explanation consumed
- hint requested
- question attempted
- question correct
- question incorrect
- partial answer
- misconception detected
- remediation completed
- assessment evidence
- spaced review success/failure

## Adaptive decision rules

At minimum:

```text
low mastery → review/remediation
repeated error → targeted remediation
high mastery + verified correct evidence → advance/practice
prerequisite not satisfied → prerequisite review
high hint dependence → reduce difficulty/support
recent success → controlled difficulty increase
```

No random or fixed `+0.05` progression.

## Multi-turn requirement

The adaptive engine must consume previous turns and actual learner responses.

Test sequence:

1. student demonstrates weakness;
2. engine records weakness;
3. tutor changes strategy;
4. student improves;
5. engine records improvement;
6. next content becomes appropriately harder;
7. restart session;
8. state remains correct.

## Adversarial tests

- same correct answer repeated
- same wrong answer repeated
- hint then correct
- hint then wrong
- partial answer
- irrelevant answer
- student changes concept
- course A evidence must not affect course B
- restart preserves state
- replay event does not duplicate evidence
- model output validation must not alter mastery

---

# 12. PHASE 7 — Assessment Correctness

## Objective

Make assessment results reliable enough to become learning evidence.

## Primary files

- `central_platform/assessment/service.py`
- `central_platform/assessment/grading.py`
- `central_platform/assessment/adaptive.py`
- question bank models
- assessment routes

## Remove synthetic provisioning

`AssessmentService._ensure_entities()` must not silently create:

- organization
- student
- course

for normal production assessment execution.

Require real existing entities.

## Deterministic grading

Verify:

- MCQ letter/content equivalence
- True/False
- numerical tolerance
- units
- sign handling
- scientific notation
- exact matches
- malformed answers

### Numerical edge cases

Test:

```text
0
-0
1e-3
1E3
NaN
Infinity
units only
multiple numbers in explanation
correct value with wrong unit
wrong value with correct unit
```

Do not accept the first number found in a free-form response unless that is explicitly the item policy.

## Subjective grading

Current implementation uses keyword ratios, answer length and heuristic rubric scoring.

Do not label this as genuine AI grading.

Choose one explicit policy:

1. deterministic rubric engine with documented limitations; or
2. actual AI grader with structured schema, evidence, calibration and confidence validation.

If AI grading is used:

- confidence must be derived, not hardcoded;
- model/provider must be recorded;
- invalid grader output must fail safely;
- teacher review must be possible;
- grading must not invent evidence.

## Assessment-to-learning integration

Only finalized, authorized assessment results should affect mastery.

Draft/in-progress attempts must not become mastery evidence.

---

# 13. PHASE 8 — Offline Sync, Device Binding and Idempotency

## Objective

Make offline learning synchronization durable and secure.

## Primary files

- `central_platform/sync/manager.py`
- `central_platform/sync/service.py`
- sync routes
- event store

## Critical defects

Current `SyncManager` keeps:

```python
_processed_event_ids = set()
_local_queue = []
_device_bindings = {}
```

These disappear on process restart.

## Required architecture

Persist:

- device registration
- device owner
- event ID
- sequence number
- received timestamp
- processing status
- retry count
- server acknowledgement

## Device security

A device must not be automatically rebound to a different student because the incoming event says so.

Correct:

```text
device already bound to student A
incoming event claims student B
→ reject
```

Initial device binding must require authenticated authorization.

## Idempotency

Database uniqueness:

```text
UNIQUE(event_id)
```

or equivalent durable idempotency key.

## Ordering

If sequence numbers are used:

- detect gaps;
- reject or quarantine out-of-order events according to policy;
- support replay safely.

## Restart test

1. queue event;
2. kill process;
3. restart;
4. event still exists;
5. process once;
6. replay same event;
7. no duplicate learning evidence.

---

# 14. PHASE 9 — Analytics, Portals and Privacy

## Objective

Ensure dashboards display evidence, not fabricated or cross-user data.

## Primary files

- `central_platform/analytics/service.py`
- portal controllers
- privacy rules
- student/teacher/parent routes

## Student analytics

Verify every metric has a source:

| Metric | Required source |
|---|---|
| Mastery | mastery evidence/SLR |
| Accuracy | question/assessment events |
| Retention | dated mastery/review evidence |
| Sessions | persisted sessions |
| Learning velocity | persisted learning evidence |
| Weak concepts | scoped mastery/misconceptions |
| Review compliance | scheduled/completed review events |

No fabricated fallback numbers.

## Teacher analytics

Must be scoped to:

```text
teacher authorization
→ organization
→ assigned class/course/cohort
```

A teacher must not be able to query arbitrary student IDs.

## Parent analytics

Explicitly define which data is visible.

Never expose:

- private teacher notes
- hidden safety information
- unrelated student data
- private chat data unless policy explicitly permits it

## Cross-tenant test matrix

For every portal endpoint:

```text
org A principal → org A resource = allowed
org A principal → org B resource = denied
student A → student B = denied
teacher A → unrelated class = denied
parent A → unrelated student = denied
```

---

# 15. PHASE 10 — Legacy, Dead Ends and False-Green Paths

## Objective

Remove code that can bypass the corrected architecture.

## Search patterns

Run searches for:

```bash
git grep -n "legacy"
git grep -n "fallback"
git grep -n "mock"
git grep -n "demo"
git grep -n "optional"
git grep -n "crs-chem-101"
git grep -n "chem_thermo_first_law"
git grep -n "org-default"
git grep -n "v1.0"
git grep -n "except Exception"
git grep -n "pass$"
git grep -n "return None"
git grep -n "TODO"
```

Also inspect Python imports with static analysis.

## Route reachability audit

For every route:

1. locate definition;
2. locate registration;
3. locate caller/frontend client;
4. identify auth dependency;
5. identify service called;
6. identify persistence writes;
7. identify fallback paths;
8. identify error handling.

Create:

`docs/verification/ROUTE_REACHABILITY_MATRIX.md`

Columns:

```text
route
method
auth
role
resource scope
service
DB writes
external calls
fallback
error contract
runtime verified
```

## Legacy server

Inspect `central_platform/api/server.py` and any alternative application entrypoint.

There must be exactly one production application entrypoint or explicitly documented alternatives.

If an old entrypoint can bypass current middleware/auth/context rules:

- remove it;
- or make it delegate to the canonical app;
- add a regression test preventing divergence.

---

# 16. PHASE 11 — Production Runtime and Database Validation

## Objective

Prove the application works outside the test harness.

## Database

The audit found SQLite-centric implementation despite PostgreSQL production claims.

Determine the official production database.

If PostgreSQL is required:

- use a production-compatible DB abstraction;
- validate migrations on PostgreSQL;
- test transactions on PostgreSQL;
- test constraints/indexes;
- test concurrency;
- remove SQLite-only assumptions from production path.

SQLite may remain for local tests if clearly isolated.

## Runtime deployment test

Use the same command/configuration as deployment.

Test:

```text
startup
health
login
course resolution
enrollment
RAG ingestion
RAG retrieval
tutor turn
student answer
mastery update
assessment
analytics
logout/revocation
restart
```

## Failure tests

Kill or break:

- database
- RAG service
- model provider
- network
- external API
- filesystem

Verify the system returns explicit safe failures.

It must not:

- fabricate success;
- return Chemistry fallback;
- lose identity boundaries;
- silently omit required context.

---

# 17. PHASE 12 — Final Forensic Certification

## Objective

Perform a second independent audit after fixes.

Do not simply rerun the phase tests.

## Test layers

### Layer 1 — Static

- imports
- unreachable code
- route registration
- hardcoded secrets
- default identities
- Chemistry fallback
- mock provider
- broad exception handlers
- duplicate implementations
- deprecated aliases

### Layer 2 — Unit

Every core algorithm.

### Layer 3 — Integration

Database + services + auth + RAG + AI.

### Layer 4 — HTTP

Actual server requests.

### Layer 5 — Security

Cross-user, cross-org, cross-course, cross-class, cross-version.

### Layer 6 — Failure injection

Provider failure, DB failure, RAG failure, timeout, malformed model output.

### Layer 7 — Restart

Kill process and verify persisted state.

### Layer 8 — Concurrency

Two simultaneous submissions of the same event/turn.

### Layer 9 — Regression

All previously legitimate functionality.

---

# 18. Required Tutor End-to-End Verification Matrix

The local AI agent MUST execute this matrix after all tutor/RAG/context fixes.

| Scenario | Expected |
|---|---|
| authenticated enrolled student asks valid course question | success |
| unauthenticated tutor request | 401 |
| student A spoofs student B | 403 |
| student asks private un-enrolled course | 403 |
| student asks wrong organization course | 403 |
| inactive enrollment | 403 |
| unpublished version | explicit unavailable/error |
| no course | context error |
| no curriculum | context error |
| no concept | context error unless explicitly general tutoring policy allows it |
| RAG has matching authorized evidence | RAG_OK |
| RAG has no match | RAG_UNAVAILABLE / explicit no-evidence state |
| RAG database fails | RAG_ERROR / context failure |
| wrong class RAG | zero results |
| wrong version RAG | zero results |
| targeted remediation wrong student | zero results |
| provider succeeds | actual provider response |
| provider fails | model unavailable/error |
| provider returns invalid output | validation failure |
| student answers correctly | learning evidence recorded |
| student answers incorrectly | learning evidence recorded |
| model response merely validates | NO mastery increase by itself |
| duplicate turn | no duplicate learning evidence |
| duplicate event after restart | no duplicate learning evidence |
| session restart | history/state preserved |

---

# 19. Required RAG Verification Matrix

Create automated tests for every row.

| Test | Must pass |
|---|---|
| course A cannot retrieve course B | yes |
| org A cannot retrieve org B | yes |
| class A cannot retrieve class B | yes |
| student A cannot retrieve student-targeted B | yes |
| version 1 cannot retrieve version 2 | yes |
| versioned request cannot retrieve unversioned content | yes |
| unpublished source unavailable | yes |
| unauthorized query rejected | yes |
| no results never trigger Chemistry fallback | yes |
| metadata filter never falls back to unfiltered vector results | yes |
| concept-scoped request respects concept policy | yes |
| document prompt injection is treated as data | yes |
| query prompt injection is sanitized | yes |
| citation maps to actual source/chunk | yes |
| provider receives only authorized RAG context | yes |

---

# 20. Required Adaptive Learning Verification Matrix

The agent must prove behavior using **sequential learner evidence**, not static mocks.

## Test A — Wrong answer

```text
initial mastery = M
student answers incorrectly
→ event recorded
→ mastery should not increase
→ misconception may increase if detected
→ next action should reflect weakness
```

## Test B — Correct answer

```text
student answers correctly
→ answer evidence recorded
→ mastery may increase according to mastery engine
→ next action can become harder if prerequisites satisfied
```

## Test C — Model-only response

```text
AI generates excellent explanation
student has not answered
→ mastery must remain unchanged
```

## Test D — Repeated misconception

```text
same misconception repeated
→ frequency increases
→ intervention/remediation becomes eligible
```

## Test E — Recovery

```text
student performs remediation correctly
→ misconception recovery evidence recorded
→ mastery updates appropriately
```

## Test F — Course isolation

```text
student struggles in Chemistry
student starts Physics
→ Physics context must not inherit Chemistry misconception/mastery
```

---

# 21. Required “Looks Working but Isn't” Checks

The agent must explicitly test these false-green classes.

## A. Endpoint exists but is not protected

Check HTTP status without token.

## B. Endpoint returns 200 but response is fallback

Inspect:

- provider
- model
- RAG source
- fallback flags
- telemetry

## C. RAG returns evidence but wrong evidence

Use deliberately conflicting documents across courses/versions.

## D. Mastery changes without learner evidence

Compare mastery before/after an explanation-only turn.

## E. Context is incomplete but response succeeds

Break one context dependency and verify explicit failure.

## F. Transaction reports failure but partial state remains

Inject DB failure after every write.

## G. Duplicate request returns success but duplicates learning state

Replay exact request twice and inspect DB/event count.

## H. Restart loses state

Restart process between queue/commit/replay.

## I. Tests pass because mocks hide broken integration

Replace mocks with real local provider/database where feasible.

## J. Production validator says healthy while real runtime is broken

Run real deployment smoke test independently.

---

# 22. Test Suite Rules

## Never delete a failing test without classification

Every failing test must be categorized:

```text
REAL BUG
STALE TEST
WRONG CONTRACT
ENVIRONMENT FAILURE
TEST INFRASTRUCTURE FAILURE
UNIMPLEMENTED FEATURE
```

Then act accordingly.

## Tests that encode forbidden behavior must be rewritten

Known examples include tests that expect:

- public-course auto-enrollment;
- unauthenticated tutor REST calls;
- synthetic user creation.

Those are not valid production tests under the current contract.

## Add regression IDs

Each fixed defect should have a test named with the forensic finding ID where practical:

```text
test_F001_protected_route_requires_auth()
test_F002_student_identity_bound_to_principal()
test_F005_rag_never_falls_back_to_chemistry()
test_F006_metadata_filter_never_falls_back_to_unfiltered()
test_F011_model_response_does_not_increase_mastery()
test_F013_provider_failure_not_reported_as_success()
test_F014_learning_commit_rolls_back_all_writes()
```

---

# 23. Progress File Requirements

After every phase, update:

`docs/verification/REMEDIATION_PROGRESS.yaml`

Example:

```yaml
project: Gayatri
last_updated: "2026-10-02T00:00:00Z"
canonical_branch: master
release_status: BLOCKED
phases:
  phase_01_auth_identity:
    status: COMPLETE
    commit: "abc1234"
    implementation_verified: true
    tests_passed: true
    runtime_verified: true
    security_verified: true
    regression_verified: true
    evidence:
      - docs/verification/evidence/phase-01-auth.md
    known_limitations: []
  phase_02_context:
    status: IN_PROGRESS
    commit: null
    implementation_verified: false
    tests_passed: false
    runtime_verified: false
    security_verified: false
    regression_verified: false
    evidence: []
    known_limitations: []
```

Never mark a boolean `true` without recorded evidence.

---

# 24. Phase Evidence Files

Create one evidence file per phase:

```text
docs/verification/evidence/
  phase-00-baseline.md
  phase-01-auth-identity.md
  phase-02-context.md
  phase-03-rag.md
  phase-04-ai-gateway.md
  phase-05-state-slr.md
  phase-06-adaptive.md
  phase-07-assessment.md
  phase-08-sync.md
  phase-09-analytics-portals.md
  phase-10-legacy.md
  phase-11-production.md
  phase-12-certification.md
```

Each evidence file must contain:

```markdown
# Phase XX Evidence

## Objective

## Starting commit

## Files changed

## Defects addressed

## Tests added

## Tests executed

## Test output

## Runtime verification

## Security verification

## Regression verification

## Failure-injection results

## Known limitations

## Ending commit

## Next phase
```

---

# 25. Git Commit Discipline

Use small, reviewable commits.

Recommended sequence:

```text
fix(phase-00): establish repository verification truth
fix(phase-01): enforce authenticated identity boundaries
fix(phase-02): make tutor context authoritative
fix(phase-03): enforce scoped fail-closed RAG
fix(phase-04): remove silent model fallback
fix(phase-05): make learning commit transactional
fix(phase-06): make mastery evidence-driven
fix(phase-07): harden assessment evidence
fix(phase-08): persist sync idempotency
fix(phase-09): scope analytics and portals
fix(phase-10): remove legacy bypass paths
fix(phase-11): verify production runtime
verify(phase-12): certify forensic regression
```

Do not mix unrelated refactors into a bug-fix commit.

---

# 26. “Do Not Break Previous Working Code” Protocol

This is mandatory for every change.

## Before modifying a shared service

Record:

- public method signatures;
- response schemas;
- route paths;
- error codes;
- DB schema dependencies;
- callers;
- test coverage.

## Prefer additive changes

When possible:

1. add strict new behavior;
2. migrate callers;
3. add regression tests;
4. remove old behavior only after all callers are migrated.

## Never silently change

- database IDs;
- public API response fields;
- event IDs;
- course/version semantics;
- token claims;
- persisted state schema.

If a breaking change is necessary, create a migration and compatibility strategy.

## Database changes

Every schema change must include:

- migration;
- forward test;
- existing-data test;
- rollback/recovery plan where applicable;
- restart test.

## API changes

Every API change must include:

- old behavior analysis;
- new contract;
- positive test;
- negative test;
- authorization test;
- backward compatibility assessment.

---

# 27. Local AI Agent Operating Prompt

Use the following as the system/task instruction for the local coding agent.

```text
You are the principal engineer responsible for repairing the Gayatri repository.

Repository: Gayatri-Education/Gayatri
Canonical branch: master unless repository verification proves otherwise.

Your mission is NOT to make tests green. Your mission is to make the actual product correct and production-safe while preserving legitimate existing functionality.

You must execute the remediation plan in GAYATRI_AI_AGENT_FORENSIC_REMEDIATION_PLAN.md phase by phase.

NON-NEGOTIABLE RULES:

1. Read the forensic audit before modifying code.
2. Read the governing product/development documents in the repository.
3. Inspect actual runtime call paths. Never assume an implementation is active because a file exists.
4. Never assume a test result proves correctness.
5. Treat tests that encode forbidden behavior as stale/incorrect tests and update them to the current contract.
6. Never weaken production behavior merely to make a test pass.
7. Never introduce a fallback that hides a failure.
8. Never use Chemistry/default values to repair missing generic context.
9. Never auto-create users, enrollments, courses or versions during normal tutor execution.
10. Never trust caller-supplied student identity over authenticated identity.
11. Never allow protected APIs to proceed without authentication.
12. Never retrieve RAG content before authorization.
13. Never fall back from filtered RAG to unfiltered RAG.
14. Never convert model-provider failure into successful mock output in production.
15. Never update mastery because an AI response merely passed validation.
16. Learning state must be derived from learner evidence.
17. Learning-state mutations must be transactionally atomic.
18. Idempotency must survive process restart.
19. Cross-student, cross-course, cross-org, cross-class and cross-version isolation must be tested.
20. Every phase must include adversarial negative tests.
21. Every phase must be runtime verified where the component is runtime dependent.
22. Every phase must preserve previously valid functionality.
23. Do not mark a phase complete without evidence.
24. Do not claim production readiness while any P0/P1 defect remains unresolved.

WORKFLOW FOR EACH PHASE:

A. Inspect git status and branch.
B. Read the phase section completely.
C. Inspect all named files and their callers.
D. Build a call graph for the affected behavior.
E. Run baseline tests.
F. Implement the smallest safe architectural fix.
G. Add/update regression tests.
H. Run focused tests.
I. Run complete test suite.
J. Start actual application and perform HTTP/runtime verification.
K. Perform adversarial/failure-injection tests.
L. Inspect git diff for regressions and accidental fallback behavior.
M. Update progress YAML and phase evidence.
N. Commit the phase.
O. Push branch.
P. Only then proceed to the next phase.

WHEN A TEST FAILS:

Do not immediately change production code.
Classify the failure as:
- real bug
- stale test
- wrong contract
- environment failure
- infrastructure failure
- unimplemented feature

Then fix the root cause.

WHEN A FEATURE RETURNS 200:

Do not assume success.
Inspect:
- authenticated principal
- authorization decision
- course/version/class scope
- RAG status
- RAG source IDs
- provider/model identity
- fallback flags
- persisted events
- mastery changes
- telemetry

WHEN RAG RETURNS RESULTS:

Verify that every returned chunk is authorized for the exact student/course/version/class context.
Create conflicting documents if necessary to prove isolation.

WHEN MASTERY CHANGES:

Trace the exact event/evidence that caused the update.
If the only cause is “AI response valid,” the implementation is wrong.

WHEN A TRANSACTION FAILS:

Verify database state after failure.
A failed operation must leave no partial learning-state writes.

WHEN YOU FIND DEAD CODE:

Do not delete blindly.
First determine whether it is imported, routed, dynamically loaded, or used by deployment.
Then either remove it safely or make it delegate to the canonical implementation.

AT THE END OF EACH PHASE:

Report:
- files changed
- defects fixed
- tests added
- tests executed
- runtime checks
- security checks
- regression checks
- known limitations
- commit SHA
- remaining findings
- next phase

Never say “all fixed” unless the entire phase gate is proven.
```

---

# 28. Final Release Gate

The system may be called production-ready only if **all** conditions below are true.

## Security

- [ ] No protected route is anonymously accessible.
- [ ] Student identity is server-bound.
- [ ] Organization boundaries are enforced.
- [ ] Course/class/version boundaries are enforced.
- [ ] JWT secrets are not hardcoded.
- [ ] Revocation is durable.
- [ ] RAG data is authorized before retrieval.
- [ ] Private chunks cannot leak through API or legacy path.

## Tutor

- [ ] No automatic student creation.
- [ ] No automatic enrollment during tutor turn.
- [ ] No invented course/version.
- [ ] Context is authoritative.
- [ ] Context failure is explicit.
- [ ] Provider failure is explicit.
- [ ] Multi-turn state persists.
- [ ] Duplicate turns are idempotent.

## RAG

- [ ] No hardcoded Chemistry fallback.
- [ ] No global fallback from scoped query.
- [ ] Exact version isolation.
- [ ] Exact class isolation.
- [ ] Student-targeted isolation.
- [ ] Organization isolation.
- [ ] Source authorization.
- [ ] Provenance/citation is real.

## Adaptive learning

- [ ] Mastery comes from learner evidence.
- [ ] Model output alone cannot increase mastery.
- [ ] Misconceptions are scoped.
- [ ] Recommendations are evidence-derived.
- [ ] Adaptive difficulty responds to actual performance.
- [ ] Restart preserves state.

## Persistence

- [ ] Learning commit is transactionally atomic.
- [ ] Event IDs are durable/idempotent.
- [ ] Sync survives restart.
- [ ] Database production target is verified.
- [ ] Migrations are tested.

## Assessment

- [ ] Deterministic grading is verified.
- [ ] Numerical edge cases are verified.
- [ ] Subjective grading policy is explicit.
- [ ] No fabricated AI confidence.
- [ ] Assessment evidence feeds learning state only after finalization.

## Analytics

- [ ] No fabricated metrics.
- [ ] Student analytics are student-scoped.
- [ ] Teacher analytics are class/course scoped.
- [ ] Parent privacy rules are enforced.
- [ ] Cross-tenant isolation is verified.

## Production

- [ ] Clean environment install succeeds.
- [ ] GitHub CI passes.
- [ ] Actual HTTP runtime passes smoke tests.
- [ ] External provider failure is tested.
- [ ] Database failure is tested.
- [ ] RAG failure is tested.
- [ ] Restart is tested.
- [ ] Concurrency is tested.
- [ ] No unresolved P0/P1 defects.
- [ ] Branch/release truth is consistent.
- [ ] Verification state is backed by evidence.

---

# 29. Final Instruction to the Local AI Agent

Do not optimize for speed of completion.

Optimize for **correctness, traceability, isolation, failure safety, and regression resistance**.

If a phase reveals a deeper architectural issue, stop and repair the dependency rather than layering another workaround on top.

If the repository contradicts this plan, inspect the actual code and governing product contract, document the contradiction, and resolve it deliberately.

If you cannot prove something works, mark it `BLOCKED` rather than `VERIFIED`.

The end goal is not a repository with many passing tests.

The end goal is a system where:

```text
identity is real
context is real
RAG is authorized
model output is real
learning evidence is real
mastery is evidence-driven
state is atomic
sync is durable
analytics are derived
failures are explicit
legacy paths cannot bypass controls
and previous valid functionality remains intact.
```

**Do not proceed to the next phase until the current phase is independently proven.**
