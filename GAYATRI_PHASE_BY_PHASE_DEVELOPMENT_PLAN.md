# GAYATRI — PHASE-BY-PHASE COURSE-INDEPENDENT PLATFORM DEVELOPMENT PLAN

**File:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Purpose:** This document is the execution contract for the local AI development agent.

---

# 1. HOW THE AGENT MUST USE THIS DOCUMENT

The agent MUST execute exactly **one phase at a time**.

The agent MUST NOT read this as permission to jump directly to the final architecture.

For every phase:

```text
READ PHASE
    ↓
DISCOVER CURRENT IMPLEMENTATION
    ↓
PLAN EXACT CHANGES
    ↓
RECORD PLAN LOCALLY
    ↓
UPDATE GITHUB
    ↓
IMPLEMENT
    ↓
TEST
    ↓
FAILURE TEST
    ↓
REAL RUNTIME VERIFY
    ↓
WRITE ACTUAL REPORT
    ↓
UPDATE LOCAL PROGRESS
    ↓
UPDATE GITHUB
    ↓
PHASE GATE
```

Only a phase marked:

```text
VERIFIED
```

may be followed by the next phase.

`IMPLEMENTED` is not the same as `VERIFIED`.

`TESTS PASSED` is not the same as `E2E VERIFIED`.

`E2E VERIFIED` is not the same as `PRODUCTION READY`.

---

# 2. FINAL PRODUCT VISION

Gayatri is a **course-independent AI tutoring platform**.

It must allow an organization/school/coaching institute to:

```text
create/select course
      ↓
make course PUBLIC or PRIVATE
      ↓
upload course content
      ↓
teacher submits content
      ↓
admin reviews
      ↓
admin approves/publishes
      ↓
students enroll
      ↓
students can belong to multiple courses
      ↓
Gayatri tutors using the selected course/version
      ↓
course-scoped RAG
      ↓
course-scoped learning state
      ↓
teacher/class/student instructions
      ↓
course-specific tools
      ↓
online and offline operation
      ↓
safe synchronization
      ↓
real analytics
```

No generic source-code change should be required to support a new subject/course.

Chemistry is an adapter/course package.

---

# 3. LOCKED PRODUCT DECISIONS

| Area | Decision |
|---|---|
| Course visibility | PUBLIC or PRIVATE |
| Public course | Other organizations can discover/select it |
| Private course | Restricted to owning organization |
| Student enrollment | Student can join multiple courses |
| Content updates | Versioned publish model |
| Upload | Teacher |
| Approval/publish | Admin |
| Textbook/course content | All eligible students in course |
| Teacher extra notes | Class-scoped |
| Remedial worksheet | Selected-student scoped |
| Teacher instructions | Supported, scope-aware |
| Course tools | Enabled per course |
| Architecture | Online + Offline |
| Generic tutor | Course/topic independent |
| Chemistry | Adapter only |

---

# 4. ABSOLUTE ENGINEERING RULES

## Rule 1 — Never trust a test label

A test called `e2e` is not automatically E2E.

Only call a test E2E when it crosses the actual system boundary.

## Rule 2 — Never use fake production data

No production runtime seeding of fake:

```text
students
teachers
courses
mastery
assignments
instructions
analytics
```

Demo data belongs in explicit test fixtures/demo mode.

## Rule 3 — Never hide exceptions

No broad exception handling that turns:

```text
ERROR
```

into:

```text
SUCCESS
```

## Rule 4 — Never add magic identity

Do not silently use:

```text
student_id = session_id
course = chemistry
default student
default school
default course
```

when the identity should be explicitly resolved.

## Rule 5 — Never put authorization only in the UI

Authorization must exist in service/domain/repository boundaries.

## Rule 6 — Never globally retrieve RAG then filter later

RAG authorization must be enforced before retrieval results are returned.

## Rule 7 — Never modify published course content in place

Create a new course version.

## Rule 8 — Never let generic code become Chemistry-specific

Chemistry belongs in its adapter.

## Rule 9 — Never retain legacy indefinitely

Compatibility code is temporary and must have a removal condition.

## Rule 10 — Never declare a phase complete without evidence

Every phase needs:

- implementation evidence
- tests
- negative tests
- runtime evidence
- failure evidence
- local progress update
- GitHub update
- report artifact

---

# 5. ARCHITECTURE TO CONVERGE TOWARD

```text
                         GAYATRI PLATFORM
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
             ONLINE                         OFFLINE
                 │                             │
             API/Auth                    Local Services
                 │                             │
            PostgreSQL                       SQLite
                 │                             │
       Object / RAG storage              Local course store
                 │                             │
            AI Gateway                    AI Gateway
                 │                             │
                 └──────────────┬──────────────┘
                                │
                         GENERIC TUTOR CORE
                                │
         ┌──────────────┬───────┼────────┬──────────────┐
         │              │       │        │              │
      Course         Curriculum Learning Assessment Instructions
      Engine           Engine     Engine    Engine       Engine
         │              │       │        │              │
         └──────────────┴───────┴────────┴──────────────┘
                                │
                         Tool / Adapter Layer
                                │
             ┌──────────────────┼────────────────────┐
             │                  │                    │
          Chemistry           Math             Programming
             │
       optional adapter
```

---

# 6. DATA CONTEXT RULE

Every tutor request must resolve:

```text
WHO?
  student

WHERE?
  organization

WHICH ENROLLMENT?
  enrollment

WHICH COURSE?
  course

WHICH VERSION?
  course_version

WHICH CLASS?
  class

WHAT CAN STUDENT SEE?
  content access policy

WHAT INSTRUCTIONS APPLY?
  instruction resolver

WHAT IS STUDENT STATE?
  course-scoped learning state

WHAT KNOWLEDGE IS ALLOWED?
  authorized RAG

WHAT TOOLS ARE ALLOWED?
  course tool policy

WHICH AI PROVIDER/MODEL?
  model registry

WHAT HAPPENED?
  append-only event/telemetry
```

If a required value is ambiguous, the operation must fail clearly rather than guessing.

---

# 7. CONTENT VISIBILITY MODEL

Content has both:

```text
CONTENT TYPE
```

and:

```text
VISIBILITY SCOPE
```

Example:

```text
TEXTBOOK + COURSE
TEACHER_NOTE + CLASS
REMEDIAL + STUDENT
```

Content publication is separate from visibility.

Unpublished content is never student-visible.

---

# 8. TEACHER INSTRUCTION MODEL

Scopes:

```text
ORGANIZATION
COURSE
CLASS
STUDENT
SESSION
```

Recommended precedence:

```text
platform safety/security
        ↓
organization
        ↓
course
        ↓
class
        ↓
student
        ↓
session
```

Instructions must be:

- authenticated
- authorized
- persisted
- validated
- auditable
- time-bounded
- revocable

They are directives, not knowledge.

---

# 9. STUDENT LEARNING IDENTITY

Learning is scoped to:

```text
student
+
course
+
course_version
+
concept
```

A student can therefore have:

```text
Physics → Newton's Laws → mastery X
Chemistry → Newton's Laws → mastery Y
History → "Force" concept → mastery Z
```

without contamination.

---

# 10. LOCAL PROGRESS TRACKING

The agent MUST create and maintain:

```text
PROJECT_STATE.yaml
```

Minimum fields:

```yaml
project:
  name:
  repository:
  canonical_branch:
  current_commit:

phase:
  number:
  name:
  status:

requirements:
  course_independent:
  public_private_courses:
  versioned_content:
  approval_publish:
  multiple_courses_per_student:
  scoped_instructions:
  scoped_rag:
  course_tools:
  online:
  offline:
  sync:

quality:
  unit_tests:
  integration_tests:
  e2e_tests:
  failure_tests:
  security_tests:
  architecture_guards:
  migration_tests:
  clean_install:
  release_validation:

bugs:
  p0:
  p1:
  p2:
  p3:

github:
  issue:
  last_comment:
  last_commit:
  last_push:
  remote_sync:

last_verified:
  timestamp:
  commit:
  report:
```

The agent must update this after every meaningful phase checkpoint.

Never update it optimistically.

---

# 11. REQUIRED LOCAL REPORTS

Create:

```text
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

Each phase creates:

```text
docs/reports/PHASE_<NN>_PLAN.md
docs/reports/PHASE_<NN>_TEST_REPORT.md
docs/reports/PHASE_<NN>_TEST_RESULTS.json
```

For relevant phases also create:

```text
PHASE_<NN>_E2E_REPORT.md
PHASE_<NN>_SECURITY_REPORT.md
PHASE_<NN>_MIGRATION_REPORT.md
PHASE_<NN>_FAILURE_INJECTION_REPORT.md
```

Do not manufacture reports for tests that were not run.


# 12.0 PHASE 0 — Forensic Baseline & Branch Reconciliation

## Objective

Freeze the true starting state before changing architecture. Establish which branch is authoritative, what actually runs, what is dead/legacy, what is hardcoded Chemistry/demo behavior, what configuration conflicts exist, and what the real baseline test results are.

## What to inspect before coding

Repository:
- git status --short --branch
- git remote -v
- git branch -a
- git log --oneline --decorate --graph --all -80
- git fetch --all --prune

Current repository evidence already observed:
- main and master diverged.
- master has newer platform phases.
- Current project documentation contains contradictory test counts and status claims.
- master currently contains platform modules but generic execution is still coupled to older Chemistry-centric paths.

Inspect:
- README.md
- PROGRESS_TRACKER.yaml
- docs/PROJECT_STATE.md
- docs/ARCHITECTURE.md
- docs/DATA_MODEL.md
- docs/TESTING_STRATEGY.md
- docs/DEPLOYMENT.md
- CURRENT_REPO_AUDIT.md
- app/**
- core/**
- central_platform/**
- adapters/ if present
- legacy/**
- migrations/**
- scripts/**
- tests/**
- model_manifest.json
- pyproject.toml
- requirements*.txt

## Files/modules likely affected

Do not modify application architecture yet.

Create:
- docs/reports/PHASE_00_FORENSICS.md
- docs/reports/PHASE_00_FILE_INVENTORY.csv
- docs/reports/PHASE_00_RUNTIME_GRAPH.md
- docs/reports/PHASE_00_TEST_BASELINE.md
- docs/reports/PHASE_00_CONFIG_AUDIT.md
- docs/reports/PHASE_00_SCHEMA_AUDIT.md
- docs/reports/PHASE_00_CHEMISTRY_COUPLING.md
- docs/reports/PHASE_00_LEGACY_REACHABILITY.md
- PROJECT_STATE.yaml
- docs/reports/DEVELOPMENT_LOG.md
- docs/reports/BUG_REGISTER.md
- docs/reports/REQUIREMENTS_TRACEABILITY.md

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

1. Capture both branch tips and create a backup reference/tag without rewriting history.
2. Determine canonical working branch from evidence; do not assume master.
3. Build file inventory with classification:
   ACTIVE / TEST_ONLY / LEGACY / DUPLICATE / OBSOLETE / UNKNOWN.
4. Trace runtime from app.main to UI/bridge/orchestrator/inference/providers.
5. Trace online/platform path separately.
6. Trace DB initialization and migrations.
7. Trace RAG write and read paths.
8. Trace test boundaries.
9. Search for hardcoded Chemistry/demo identifiers.
10. Search for all legacy imports.
11. Search for duplicate model definitions.
12. Search migrations for duplicate table definitions.
13. Run baseline tests using the exact repository-supported commands.
14. Run compile/static checks.
15. Record failures exactly; do not fix them in this phase unless required just to obtain a valid baseline.
16. Update the local state and GitHub tracking with the evidence.

## Mandatory testing

Required:
- python --version
- python -m pytest -q
- pytest -q, if supported, to compare behavior
- python -m compileall app core central_platform tests scripts
- ruff check .
- dependency/version inspection
- import smoke test
- startup smoke test
- architecture searches for Chemistry/legacy/demo references

A test is not E2E unless it crosses actual runtime boundaries.

## Required evidence/reporting

All phase-0 reports above plus exact command output. Record:
commit SHA
branch
environment
test counts
lint counts
compile result
known blockers
GitHub branch state

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

Create/update the phase GitHub issue.
Post:
- baseline SHA
- branch comparison
- confirmed defects
- exact test counts
- exact failed commands
- intended Phase 1 scope.

Push the documentation commit(s) after verification. Do not claim repository reconciliation until the branch decision is evidenced.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when:
- canonical branch decision documented
- baseline is reproducible
- known architectural defects are enumerated
- no hidden assumption remains about current state
- PROJECT_STATE.yaml is initialized
- BUG_REGISTER is initialized
- GitHub update actually exists

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.1 PHASE 1 — Architecture Contract & Repository Guardrails

## Objective

Create the authoritative target architecture and automated guardrails before feature refactoring. Stop future agents from reintroducing Chemistry coupling, legacy imports, demo seeds, configuration duplication, or false-green testing.

## What to inspect before coding

Inspect:
- current architecture docs
- pyproject.toml
- CI workflow(s)
- all production imports
- all test configuration
- model configuration
- environment configuration
- release scripts
- existing architecture/security/test docs

## Files/modules likely affected

Create/update:
- docs/ARCHITECTURE_TARGET.md
- docs/DATA_MODEL_TARGET.md
- docs/SECURITY_MODEL_TARGET.md
- docs/TESTING_STRATEGY_TARGET.md
- docs/AGENT_DEVELOPMENT_RULES.md
- tests/architecture/**
- CI workflow(s)
- PROJECT_STATE.yaml

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

1. Define canonical layers:
   presentation → application → domain → repositories/infrastructure.
2. Define generic tutor boundary.
3. Define Course/CourseVersion/CourseOffering boundaries.
4. Define online/offline adapters using shared domain services.
5. Define security boundaries and authorization points.
6. Define error contracts.
7. Define observability contracts.
8. Add architecture tests:
   - generic core cannot import Chemistry adapter
   - production code cannot import legacy
   - demo fixture identifiers cannot appear in production runtime
   - model config must have one source of truth
   - required migrations have unique names and no duplicate DDL tables
9. Add a test-report generator or standardized report command.
10. Make CI fail on architecture violations.

## Mandatory testing

Run:
- architecture guard tests
- compile
- lint
- current regression suite
- import graph/grep checks
- config validation

Add negative tests proving the guards fail on deliberate temporary fixtures where practical.

## Required evidence/reporting

Target architecture docs, guard tests, CI output, report JSON, and project-state update.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub:
- update the architecture issue
- commit target docs + guards separately from application changes
- push
- comment exact CI results

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when the repository has machine-enforceable guardrails and one authoritative architecture document. No application feature work should proceed without these guards.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.2 PHASE 2 — Canonical Course, Version & Offering Domain

## Objective

Introduce the core abstraction that makes every subsequent feature course-independent. Public/private courses become platform entities; school selection becomes a separate offering relationship; versions become immutable published snapshots.

## What to inspect before coding

Inspect:
- central_platform/models/schema.py
- central_platform/db.py
- migrations/**
- central_platform/portals/**
- tests for Course/Curriculum/Enrollment
- any course-related UI or bridge code

## Files/modules likely affected

Likely affected:
- central_platform/models/schema.py
- central_platform/db.py
- migrations/ new migration(s)
- central_platform/services/ or application layer
- tests/unit/course/*
- tests/integration/course/*
- docs/DATA_MODEL_TARGET.md

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Implement domain objects and persistence for:
- Course
- CourseVersion
- CourseOffering / OrganizationCourse
- CourseVisibility PUBLIC/PRIVATE
- CourseStatus
- VersionStatus
- course policy/tool policy placeholders

Rules:
- PUBLIC means discoverable/selectable by other organizations.
- PRIVATE means owner organization only.
- Public metadata can be discoverable; private content cannot.
- A course version is immutable after publish.
- An organization selects/pins a course version through its offering.
- Students may enroll in many courses.

Do not put UI logic in repositories or database functions.
Do not make `organization_id` the intrinsic identity of a public Course.

## Mandatory testing

Test:
- create public course
- create private course
- public discovery
- private cross-org denial
- multiple organization offerings
- version state machine
- published version immutability
- enrollment into multiple courses
- duplicate enrollment protection
- tenant isolation
- migration fresh install
- migration from previous DB
- migration idempotency

## Required evidence/reporting

PHASE_02 implementation report, migration report, test report, JSON evidence, DB schema evidence, traceability updates.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

Open/update course-domain GitHub issue. Include schema diagram and migration evidence. Push logical commits.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only with real persisted data tests and migration tests. No default Chemistry course may be created automatically.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.3 PHASE 3 — Generic Curriculum & Versioned Learning Graph

## Objective

Replace Chemistry-specific curriculum logic with a data-driven course curriculum. The same engine must accept Physics, History, Programming, or arbitrary school-created course structures without source-code changes.

## What to inspect before coding

Inspect:
- core/curriculum/models.py
- core/curriculum/resolver.py
- core/curriculum/loader.py
- core/knowledge_graph.py
- central_platform/learning/graph.py
- curriculum data files
- curriculum validator tests

## Files/modules likely affected

Refactor:
- core/curriculum/models.py
- core/curriculum/loader.py
- core/curriculum/resolver.py
- core/knowledge_graph.py
- central_platform/learning/graph.py
- migrations if needed
- tests for curriculum/graph

Move Chemistry-specific logic into adapter territory, not generic resolver.

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Implement generic:
CourseVersion → Curriculum → Subject → Module → Topic → Concept → Prerequisite.

Concept resolution should use:
- explicit concept ID
- active course curriculum
- aliases/metadata
- course-scoped semantic/keyword resolver
- safe unknown result

Do not use a global Chemistry keyword map.

Support optional concepts when arbitrary courses do not have a full taxonomy.
Validate DAGs for cycles/orphans.
Keep stable concept identifiers independent from display names.

## Mandatory testing

Test with four fixture courses:
- Chemistry
- Physics
- History
- Programming

Prove:
- all load using same generic engine
- no Chemistry code path is required
- prerequisites are course/version scoped
- cycle detection works
- missing prerequisite detection works
- concept IDs do not collide across courses

## Required evidence/reporting

Generic curriculum report, graph report, fixture manifests, test evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with genericity evidence. Include the four-course test matrix in the issue comment.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when generic curriculum works with Chemistry adapter disabled.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.4 PHASE 4 — Course-Scoped Student Learning State & Sessions

## Objective

Make every learning state, session, event, mastery record, misconception, review queue, and progress query course-aware and version-aware where required.

## What to inspect before coding

Inspect:
- central_platform/learning/state.py
- central_platform/models/schema.py
- core/tutor/state.py
- core/learning/**
- core/tutor/lifecycle.py
- progress services
- sessions and event persistence

## Files/modules likely affected

Refactor affected learning/state/session/event modules.
Key data identity:
student + course + course_version + concept.
Use enrollment to authorize course membership.

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

1. Build authoritative CourseLearningContext.
2. Require course context in learning services.
3. Associate sessions with course/version.
4. Associate learning events with org/course/version/student.
5. Keep event IDs idempotent.
6. Compute mastery only from course-scoped evidence.
7. Keep misconceptions course-aware.
8. Ensure progress analytics accept course context.
9. Remove fallbacks like student_id=session_id where they create hidden identity.
10. Reject missing/ambiguous course context.

## Mandatory testing

Cross-course contamination matrix:
- same student, same concept name, two courses
- course A attempt changes only A
- course B attempt changes only B
- version history preserved
- unauthorized student cannot query another student's state
- duplicate event does not double-count
- restart restores exact state

## Required evidence/reporting

State migration report, event schema report, test report, restart/recovery evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with exact cross-course isolation results.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only with explicit course-scoped persistence and negative isolation tests.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.5 PHASE 5 — Knowledge Asset Ingestion & Publication Pipeline

## Objective

Create a controlled content pipeline where teachers upload content, the system processes it, and only administrators can approve/publish it.

## What to inspect before coding

Inspect:
- existing core/rag/**
- upload handlers
- file security
- course data directories
- storage helpers
- deployment docs
- any existing upload/UI code

## Files/modules likely affected

Create/refactor:
- knowledge asset models
- upload service
- parser registry
- sanitization/normalization
- content processing state machine
- storage abstraction
- migration(s)
- tests

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Required states:
DRAFT → PROCESSING → READY_FOR_REVIEW → APPROVED → PUBLISHED → ARCHIVED
Failure → FAILED.

Content types:
TEXTBOOK, REFERENCE, TEACHER_NOTE, WORKSHEET, REMEDIAL, ASSESSMENT_SOURCE, SOLUTION_GUIDE, OTHER.

Processing:
upload → checksum → type/size validation → persistent source → parse → clean → chunk → metadata → index staging → validation.

A failed operation cannot become READY by accident.
A retry must be idempotent where feasible.

## Mandatory testing

Test PDF/DOCX/TXT/Markdown if supported.
Test malformed, empty, duplicate, oversized, unsupported, corrupted, partial processing and failed indexing cases.
Prove publication permissions and student visibility rules.

## Required evidence/reporting

Ingestion lifecycle report, sample sanitized metadata, failure matrix, test JSON.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub issue update with file-type matrix and state transition evidence.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when no unpublished content is retrievable by student workflows.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.6 PHASE 6 — Scoped RAG & Knowledge Authorization

## Objective

Make retrieval course/version/class/student scoped. RAG becomes an authorization-aware service, not a global search index.

## What to inspect before coding

Inspect:
- core/rag/store.py
- core/rag/retriever.py
- core/rag/schema.py
- central_platform DB RAG tables
- any embeddings/vector index implementation

## Files/modules likely affected

Refactor RAG to carry:
organization_id
course_id
course_version_id
subject_id/module_id/topic_id/concept_id
visibility_scope
class_id
student_id
publication_status
source_id/version/checksum

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Implement:
1. authorization filter before retrieval results leave the service.
2. course/version filter.
3. class scope.
4. student scope.
5. publication status filter.
6. source authority/provenance.
7. no fallback from restricted search to global search.
8. retrieval diagnostics that expose status but not private content.
9. deterministic empty/failed states.
10. reindex/version isolation.

## Mandatory testing

Required tests:
- course textbook visible to enrolled students
- private course invisible to other org
- class notes visible only to class
- remedial visible only to selected students
- draft/unpublished invisible
- old version not mixed with new version
- unauthorized query returns DENY/empty according to contract, never leaked chunks
- RAG failure is explicit

## Required evidence/reporting

RAG access-control report, retrieval traces, source/version checksum evidence, test JSON.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with access-control matrix and negative test results.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when authorization is enforced inside retrieval/service boundaries, not UI.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.7 PHASE 7 — Teacher Instruction Hierarchy

## Objective

Implement teacher instructions as persisted, authorized, time-bounded directives that can target course, class, student, or session without compromising system safety policy.

## What to inspect before coding

Inspect:
- central_platform/teacher/instruction.py
- central_platform/models/schema.py
- instruction services
- context builder
- teacher portal
- tests for instruction/security

## Files/modules likely affected

Refactor/create:
- TeacherInstruction entity
- instruction repository/service
- instruction resolver
- audit events
- API boundary
- context integration
- tests

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Scopes:
ORGANIZATION
COURSE
CLASS
STUDENT
SESSION

Resolution:
platform safety/security policy
→ organization
→ course
→ class
→ student
→ session

Fields:
id, org, course, version, class, student, scope, priority, content, creator, validity dates, status, safety status, audit.

Instruction content is not the same as knowledge content.
Never inject raw teacher text directly into system prompt.

## Mandatory testing

Test:
- authorized teacher can create
- unauthorized teacher denied
- expired/revoked excluded
- class instruction reaches only class students
- student instruction reaches only selected student
- conflicting instructions follow deterministic precedence
- prompt injection in teacher instruction is rejected
- platform policy cannot be overridden

## Required evidence/reporting

Instruction resolver report, policy test matrix, audit evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with exact scope tests.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when instruction resolution is deterministic and security-policy protected.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.8 PHASE 8 — Course Tool Capability & Adapter Registry

## Objective

Allow courses to enable tools without coupling the tutor core to specific subjects.

## What to inspect before coding

Inspect:
- core/tutor/chemistry_tools.py
- central_platform AI/tool modules
- provider capability handling
- assessment/evaluator code

## Files/modules likely affected

Create:
- tool registry
- tool capability model
- course tool policy
- adapter interfaces
- Chemistry tool adapter
- optional Math/Programming test adapters

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Tool execution must require:
course policy allows tool
user role permits tool
operation is within scope
input validated
output typed
resource limits enforced

Example:
Chemistry equation balancer.
Math symbolic calculator.
Programming sandbox.
Custom course can use no tools.

## Mandatory testing

Test enabled/disabled tool behavior, unauthorized tool calls, resource limits, malformed arguments, disabled Chemistry adapter, and cross-course tool-policy isolation.

## Required evidence/reporting

Tool registry report and test evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with adapter/capability matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when generic tutor does not import individual tool implementations directly.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.9 PHASE 9 — Model Registry & AI Gateway Unification

## Objective

Replace conflicting model settings and eliminate legacy inference dependency. AI provider/model configuration gets one authoritative source.

## What to inspect before coding

Inspect:
- model_manifest.json
- core/config.py
- core/inference/service.py
- core/providers/*
- legacy/agents/*
- model fetch/download scripts
- release scripts

## Files/modules likely affected

Refactor:
- model registry/manifest loader
- AI Gateway
- provider interfaces
- local provider
- cloud providers
- configuration
- model validation
- tests

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Manifest must define:
model_id
provider
artifact path
format
quantization
prompt template
context window
streaming
JSON/tool capabilities
resource profile

Inference flow:
Tutor → AI Gateway → provider → model.

No production caller may import legacy.

Do not silently switch provider/model.
Fallbacks must be policy-controlled and observable.

## Mandatory testing

Test:
- manifest consistency
- missing model
- wrong model
- corrupt model
- provider timeout
- provider invalid response
- local-only policy
- local-first fallback
- provider selection
- streaming
- cancellation
- legacy import guard
- prompt template consistency

## Required evidence/reporting

Model/config reconciliation report, provider matrix, failure injection report, test JSON.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with legacy search result and provider tests.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when the active runtime path is fully legacy-free and model configuration has one source of truth.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.10 PHASE 10 — Generic Tutor Orchestrator

## Objective

Build the central tutoring flow around course context rather than Chemistry mode.

## What to inspect before coding

Inspect:
- core/orchestrator.py
- central_platform/ai/context_builder.py
- central_platform/ai/query_understanding.py
- response planner/validator
- tutor lifecycle
- session management
- bridge callers

## Files/modules likely affected

Refactor:
- core/orchestrator.py or replace with application tutor service
- context builder
- response planner
- response validator
- lifecycle integration
- API/local adapters

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Required flow:
identity validation
→ enrollment validation
→ course/version resolution
→ class resolution
→ learning state
→ instruction resolution
→ course policy
→ tool policy
→ RAG retrieval
→ conversation context
→ pedagogy planner
→ AI Gateway
→ response validator
→ learning evidence
→ state commit
→ audit/telemetry

No `if chemistry`, `mode=chemistry_tutor`, or Chemistry keyword branches in generic orchestration.

## Mandatory testing

Real integration tests must execute the whole service flow.
Test:
- valid course
- invalid course
- unauthorized enrollment
- empty curriculum
- RAG empty
- model unavailable
- invalid model output
- state rollback when response validation fails
- streaming interruption
- duplicate turn
- restart/resume

## Required evidence/reporting

Tutor architecture trace, turn lifecycle traces, actual request/response samples with sensitive data redacted, test JSON.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with actual request-path evidence.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when one generic tutor pipeline runs multiple course types without Chemistry-specific branching.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.11 PHASE 11 — Generic Assessment & Evaluation

## Objective

Make assessments course-independent while preserving deterministic evaluators where domain adapters provide them.

## What to inspect before coding

Inspect:
- central_platform/models/schema.py assessment models
- core/assessment/**
- core/tutor/evaluator.py
- chemistry evaluator/tools
- assessment tests

## Files/modules likely affected

Refactor:
- generic assessment service
- evaluator registry
- generic evaluator
- numeric evaluator
- rubric evaluator
- adapter evaluator hooks
- anti-answer-leakage service
- tests

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Supported item types should be capability-driven, not Chemistry-driven.
Evaluation result:
CORRECT / PARTIALLY_CORRECT / INCORRECT / UNCERTAIN.

The model may produce evidence but does not directly set mastery.

## Mandatory testing

Test all generic types supported.
Test uncertain answers.
Test malformed answers.
Test unit mismatch where applicable.
Test anti-leakage.
Test assessment state by course/version.
Test teacher review.
Test remediation recommendations without cross-course contamination.

## Required evidence/reporting

Assessment report + answer evaluation evidence + failure matrix.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with exact evaluator coverage.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when no keyword-only fallback can produce false correctness.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.12 PHASE 12 — Real Online API Boundary

## Objective

Introduce an actual online service boundary so portals do not bypass domain services and so E2E tests can exercise the real application path.

## What to inspect before coding

Inspect:
- central_platform/api/**
- any FastAPI/Flask modules
- auth/RBAC
- db/repository layer
- deployment validator
- existing UI callers

## Files/modules likely affected

Implement route/service separation for:
- auth
- organizations
- course catalog
- course selection
- enrollments
- classes
- content
- review
- publication
- instructions
- assignments
- assessments
- tutor
- progress
- sync
- health

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Routes validate input and auth, call application services, and return typed responses.
Business rules do not live in route functions.
Error responses use stable codes.
Health endpoint reports actual subsystem state.

## Mandatory testing

Run real server.
Test real HTTP requests.
Test auth.
Test RBAC.
Test course CRUD.
Test content lifecycle.
Test tutor.
Test unauthorized access.
Test error mapping.
Test health with intentionally broken subsystem if feasible.

## Required evidence/reporting

API contract document, OpenAPI snapshot if available, real HTTP test report, server startup/shutdown evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with server command, endpoint list, and exact test counts.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when real HTTP boundary is exercised in integration tests.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.13 PHASE 13 — Offline Local Runtime

## Objective

Make the same course-independent system operate locally without network dependence for cached courses and local models.

## What to inspect before coding

Inspect:
- app/main.py
- app/bridge/**
- local DB/storage
- local RAG
- model loader
- settings
- session store
- current setup.bat/launch scripts

## Files/modules likely affected

Refactor local runtime to use the same application/domain services as online mode.
Add:
- local repository adapter
- local course store/cache
- local RAG store
- local model provider
- local session persistence
- offline capability detection

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Startup must:
- detect missing dependencies explicitly
- detect missing course cache
- detect missing model
- show honest degraded state
- never seed fake demo data

Local state must survive restart.

## Mandatory testing

Test from clean environment:
- first offline launch
- cached course
- uncached course
- local tutor
- restart
- interrupted turn
- read-only DB
- missing model
- corrupted cache

## Required evidence/reporting

Offline report with actual timings, files used, state before/after restart, failure results.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with offline matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when offline mode completes real learning flow without network.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.14 PHASE 14 — Sync & Conflict Resolution

## Objective

Synchronize offline learning events and metadata safely and idempotently.

## What to inspect before coding

Inspect:
- event model
- DB repositories
- local DB
- API
- any sync code
- timestamps/version fields
- recovery manager

## Files/modules likely affected

Implement:
- sync_outbox
- operation IDs
- event IDs
- retries
- acknowledgement
- deduplication
- conflict policies
- sync status UI/API

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Learning events append-only where possible.
Same event sent twice must not create two logical events.
Course content does not merge ad hoc; it uses course versions.
Mastery should derive from authoritative event history where practical.

## Mandatory testing

Test:
- normal sync
- duplicate sync
- partial sync
- timeout
- server rejection
- retry
- client crash
- server restart
- simultaneous devices
- version mismatch
- out-of-order events

## Required evidence/reporting

Sync report with event IDs, operation IDs, before/after state snapshots and server acknowledgements.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with duplicate-event proof and conflict matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when repeated sync is idempotent and no learning data disappears.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.15 PHASE 15 — Admin Course & Content Workflow UI

## Objective

Connect the admin workflows to real services: public/private course handling, course selection, approval and publication.

## What to inspect before coding

Inspect:
- app/ui/**
- central_platform/portals/**
- bridge facade
- shared design system
- existing course-related UI assets

## Files/modules likely affected

Build UI only against service contracts:
- course catalog
- create private course
- select public course
- view versions
- review queue
- approve/publish
- archive
- audit trail

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

No hardcoded course names, student names, mastery numbers, or demo data.
UI must handle empty/loading/error/forbidden/stale states.

## Mandatory testing

Real UI tests must:
- create course
- upload content
- review
- publish
- view published version
- attempt forbidden action
- confirm UI reflects real DB state after reload

## Required evidence/reporting

UI evidence screenshots/videos where supported, DOM assertions, API correlation IDs, test report.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with real workflow evidence.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when UI state is sourced from the actual backend/local service.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.16 PHASE 16 — Teacher Workflow UI

## Objective

Implement real teacher operations for classes, notes, remedial content, instructions and assignments.

## What to inspect before coding

Inspect teacher portal, bridge, instruction service, assignment/assessment services, class/enrollment services.

## Files/modules likely affected

Implement:
- course/class selection
- textbook/content upload
- class note upload
- student selection
- remedial content upload
- instruction composer
- assignment creation
- review of student progress

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Every action:
UI → service → authorization → persistence → observable result.

Do not let a teacher select arbitrary students outside authorized class/course scope.

## Mandatory testing

Real UI tests:
- class notes visible to correct class only
- remedial visible to selected students
- instruction reaches correct context
- unauthorized student/class denied
- reload preserves state

## Required evidence/reporting

Teacher workflow evidence and test report.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with exact class/student scope matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only with real data and negative authorization tests.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.17 PHASE 17 — Student Multi-Course Workflow UI

## Objective

Allow students to see and switch between multiple courses without state contamination.

## What to inspect before coding

Inspect student portal, course dashboard, session management, progress payloads, bridge/API contracts.

## Files/modules likely affected

Implement:
- My Courses
- course selector
- active course context
- module/topic/concept navigation
- assignments
- course knowledge
- tutor launch
- progress per course
- offline indicators

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Active course must be explicit in every tutor/session call.
Student cannot switch course while a turn is generating unless the session cancellation/transition path is safe.

## Mandatory testing

Real UI tests with one student enrolled in at least three courses.
Verify:
- correct course data
- correct course mastery
- correct RAG
- course switch
- session isolation
- assignment isolation

## Required evidence/reporting

Student workflow test report and state snapshots.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with multi-course evidence.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when one student can use multiple courses concurrently without state bleed.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.18 PHASE 18 — Teacher Instruction + RAG Integration

## Objective

Combine the two most important content/context sources so that the tutor receives exactly the authorized knowledge and applicable instructions.

## What to inspect before coding

Inspect:
- context builder
- instruction resolver
- RAG retriever
- course context
- portal actions

## Files/modules likely affected

Implement deterministic context assembly:
platform policy
course policy
teacher instructions
learner state
authorized RAG
conversation
student query
tool capabilities

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Keep evidence separate from directives.
Attach provenance to retrieved content.
Track which instruction IDs and source IDs contributed to each turn.
Do not log private content unnecessarily.

## Mandatory testing

Test:
- course textbook + class note + student remedial
- broad + narrow instruction
- expired instruction
- unauthorized content
- no content
- no instructions
- mixed scopes
- version update

## Required evidence/reporting

Context trace report with redacted provenance and exact IDs.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with context-layer verification.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when the tutor context is explainable, scoped and reproducible.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.19 PHASE 19 — Chemistry Adapter Extraction & Disablement Test

## Objective

Convert existing Chemistry behavior into a first-class adapter and prove the generic platform does not depend on it.

## What to inspect before coding

Inspect all Chemistry references found in Phase 0 and all modified modules from Phases 3–18.

## Files/modules likely affected

Move/retain under explicit Chemistry adapter:
- chemistry evaluator
- equation balancer
- chemistry misconceptions
- chemistry curriculum manifest
- Chemistry-specific prompt/pedagogy extensions if truly necessary

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Generic core cannot import Chemistry adapter implementation.
Course configuration selects adapter capabilities.
Run platform with adapter disabled.

## Mandatory testing

Tests:
- all generic platform operations with Chemistry adapter disabled
- Chemistry course with adapter enabled
- Chemistry-specific tools
- cross-course isolation
- generic course does not load Chemistry modules

## Required evidence/reporting

Adapter migration report, import-guard evidence, four-course regression results.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with list of moved/deleted modules and zero generic Chemistry imports.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when disabling Chemistry does not break generic platform functionality.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.20 PHASE 20 — Legacy Removal & Dead-Code Cleanup

## Objective

Remove old architecture after reachability proof rather than preserving indefinite compatibility shims.

## What to inspect before coding

Inspect:
- legacy/**
- old tutor contexts
- old mode systems
- old JSON state stores
- duplicate providers
- obsolete docs
- duplicate utilities

## Files/modules likely affected

Before deletion:
- build production import graph
- build test reference graph
- classify each candidate
- identify replacement
- migrate remaining callers
Then delete only proven-unused code.

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Delete:
- legacy runtime dependencies
- obsolete compatibility shims
- stale scratch files
- duplicate trackers
- obsolete Chemistry-generic bridges
- dead configuration

Do not delete test fixtures or historical evidence needed for reproducibility without replacing the evidence path.

## Mandatory testing

Tests:
- architecture import guard
- full regression
- clean import
- startup
- E2E
- packaging
- source scan for deleted references

## Required evidence/reporting

Cleanup manifest, deletion report, dependency graph after cleanup, full regression report.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub issue/PR must enumerate every deletion and proof of no active callers.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when legacy runtime reachability is zero and all replacements are verified.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.21 PHASE 21 — Database & Migration Hardening

## Objective

Reconcile all schema definitions, verify SQLite and supported PostgreSQL behavior, and eliminate silent migration failures.

## What to inspect before coding

Inspect:
- all migrations
- central_platform/db.py
- repository methods
- migration runner
- DDL tests
- deployment validator

## Files/modules likely affected

Fix:
- duplicate table definitions
- missing foreign keys
- missing indexes
- inconsistent field names
- incompatible dataclass/schema types
- migration ordering
- backend-specific SQL if actually unsupported

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Create a schema manifest and migration compatibility matrix.
Every table has one authoritative creation source.
Migrations have immutable identity/checksum.

## Mandatory testing

Test:
- empty DB
- migrate all
- migrate twice
- upgrade from previous release
- data preservation
- foreign-key violations
- uniqueness
- concurrent access where relevant
- PostgreSQL only if actual environment available; otherwise mark unverified

## Required evidence/reporting

Database hardening report with SQL/schema checks and actual results.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with migration matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when every claimed backend capability has actual evidence.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.22 PHASE 22 — Security, Privacy & Isolation Audit

## Objective

Perform independent security verification across identity, RAG, courses, classes, students, instructions, uploads, model prompts, logs and sync.

## What to inspect before coding

Inspect:
- RBAC/auth
- security modules
- upload handling
- instruction validation
- RAG access control
- audit logs
- parent privacy
- sync
- API routes
- bridge methods

## Files/modules likely affected

Fix all confirmed security defects.
Do not treat existing security tests as proof without exercising the real boundary.

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Run attack-style tests:
- cross-tenant access
- IDOR
- privilege escalation
- prompt injection
- malicious course content
- malicious teacher instruction
- path traversal
- unsafe upload
- secret leakage
- log PII leakage
- RAG data leakage
- sync replay

## Mandatory testing

Require negative tests with actual denied responses.
Record evidence, not generic PASS labels.

## Required evidence/reporting

Security audit report, vulnerability register, remediation evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

Open/maintain GitHub issues for every security defect; close only after regression test.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only with zero open release-blocking security findings.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.23 PHASE 23 — Reliability, Failure Injection & Recovery

## Objective

Prove the system fails safely and recovers predictably. This is specifically designed to stop silent-fail bugs from recurring.

## What to inspect before coding

Inspect:
- central_platform/recovery/manager.py
- tutor lifecycle
- provider routing
- DB recovery
- RAG recovery
- sync recovery
- startup validation

## Files/modules likely affected

Refactor recovery paths so all failures have:
classification
observable status
safe user message
technical diagnostic
retryability
rollback/commit decision

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Inject:
missing model
corrupt model
provider timeout
provider malformed response
RAG unavailable
DB unavailable
broken migration
broken upload
interrupted publish
expired instruction
duplicate sync
app crash mid-turn

## Mandatory testing

For each injected failure capture:
trigger
expected
actual
logs/diagnostic
state before
state after
user-visible status
whether data was committed

## Required evidence/reporting

Failure-injection report with per-scenario evidence.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with failure table and fixed bugs.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when failure behavior is explicit and no critical error is converted into a fake success.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.24 PHASE 24 — Real End-to-End Journeys & Browser/Desktop Verification

## Objective

Replace “synthetic E2E” confidence with actual user journeys through the running system.

## What to inspect before coding

Prepare:
- clean DB
- fixture organizations
- public/private courses
- four courses
- teacher/student accounts
- content fixtures
- controlled model/provider

## Files/modules likely affected

Add true E2E tests that cross:
UI → API/local boundary → services → DB → RAG → AI Gateway → state → UI.

Keep lower-level tests too; do not relabel them as E2E.

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Execute mandatory journeys:
A public course selection
B private course isolation
C textbook publication
D class notes
E selected-student remedial
F teacher instructions
G multi-course student
H course version update
I offline restart
J sync
K failure recovery

## Mandatory testing

Capture:
test IDs
browser/app route
request IDs
DB assertions
RAG source IDs
model/provider
final UI state
screenshots/video where supported
timings
failures

## Required evidence/reporting

E2E report is evidence-heavy, not “all green”.
Include per-journey PASS/FAIL with exact checkpoints.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with artifact links and exact journey matrix.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only when all mandatory real journeys execute against the actual application boundary.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.25 PHASE 25 — Performance & Capacity Verification

## Objective

Measure actual system behavior on target hardware/environment instead of using fixed optimistic thresholds.

## What to inspect before coding

Inspect performance profiler, deployment docs, model configuration, DB indexes, RAG indexing, concurrency paths.

## Files/modules likely affected

Instrument:
startup
course selection
RAG retrieval
tutor turn
DB operations
sync
memory
concurrency

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Run with declared environment:
CPU
RAM
OS
Python
model
quantization
course size
content size
student count
concurrency

## Mandatory testing

Report:
p50/p95/p99 where applicable
throughput
memory
CPU
failure rate
cold/warm startup
offline behavior
sync throughput

## Required evidence/reporting

Performance report plus raw measurement JSON.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub update with actual measurements and environment.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only against thresholds that are explicitly justified for the target deployment. Otherwise report measured behavior without inventing PASS.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.26 PHASE 26 — Packaging, Clean Install & Deployment Validation

## Objective

Verify that the released application can be installed and run in a clean environment without developer-machine residue.

## What to inspect before coding

Inspect:
- scripts/package_release.py
- scripts/verify_release.py
- setup.bat
- launch.bat
- requirements*.txt
- pyproject.toml
- deployment docs
- model packaging rules

## Files/modules likely affected

Fix:
- version mismatches
- signature behavior
- missing model metadata
- missing offline assets
- missing migrations
- Python version messaging
- clean-install path

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Clean release procedure:
fresh clone/release artifact
→ fresh environment
→ install
→ initialize DB
→ migrate
→ provision course
→ publish content
→ enroll student
→ run tutor
→ close
→ restart
→ verify state

## Mandatory testing

Test signed and unsigned release behavior according to the actual policy.
Verify all packaged files and hashes.
Verify no missing runtime dependencies.

## Required evidence/reporting

Clean install report, release integrity report, package manifest, startup logs.

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

GitHub release issue/comment includes exact artifact/version/SHA and verification results.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

PASS only if clean installation works independently of developer machine state.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 12.27 PHASE 27 — Documentation, State Reconciliation & Final Release Gate

## Objective

Produce one truthful final state and ensure documentation, tests, GitHub and implementation all agree.

## What to inspect before coding

Inspect all current status/progress/audit/readme docs.
Search for stale numbers, old branch names, old repo URLs, Chemistry-only claims, obsolete phase numbers.

## Files/modules likely affected

Update or archive:
README.md
PROJECT_STATE.yaml
DEVELOPMENT_LOG.md
BUG_REGISTER.md
REQUIREMENTS_TRACEABILITY.md
architecture/data/security/testing docs
release notes

The agent MUST first verify the current file tree and call graph. Do not assume these files still exist or that their implementations match previous versions.

If a listed file does not exist:
- record it as a discovery result,
- locate the actual replacement,
- update the phase report,
- do not create a duplicate file merely to match this document.

## How to code this phase

Generate final state from actual evidence:
- exact commit
- branch
- test counts
- E2E counts
- security findings
- known limitations
- supported online/offline capabilities
- model/provider status
- migration status
- GitHub state

## Mandatory testing

Run final:
- full unit
- full integration
- real E2E
- architecture guards
- security
- failure injection
- migration
- clean install
- release verification


## Required evidence/reporting

Create:
docs/reports/FINAL_PRODUCTION_READINESS_REPORT.md
docs/reports/FINAL_PRODUCTION_READINESS.json
docs/reports/FINAL_TEST_REPORT.md
docs/reports/FINAL_TEST_RESULTS.json

Every test report MUST contain:

```text
commit SHA:
branch:
timestamp:
environment:
python:
OS:
dependencies:
command:
scope:
collected:
passed:
failed:
skipped:
xfailed:
duration:
coverage:
result:
```

For each failure:

```text
test ID:
expected:
actual:
root cause:
fix:
regression test:
verification:
```

For each skipped test:

```text
test:
reason:
impact:
replacement verification:
```

## GitHub work

Final GitHub update:
- all phase issues referenced
- unresolved non-blocking items listed
- release commit
- exact evidence
- no unsupported production-ready claim.

The agent MUST use actual Git/GitHub operations when credentials and tooling are available.

If GitHub remote access is unavailable, write the intended operation to:

```text
docs/reports/GITHUB_SYNC_QUEUE.md
```

and mark:

```text
REMOTE_SYNC = BLOCKED
```

Never claim remote synchronization completed when it did not.

## Phase gate

RELEASE = PASS only if all mandatory gates are green and evidence is present. Otherwise final state must remain PARTIAL/BLOCKED.

Before moving forward, update:

```text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
```

and create the phase test report.

---


# 13. STANDARD PHASE EXECUTION TEMPLATE FOR THE AI AGENT

For every phase after Phase 0, the agent MUST internally execute this sequence.

## Step A — Read state

Read:

```text
PROJECT_STATE.yaml
BUG_REGISTER.md
DEVELOPMENT_LOG.md
REQUIREMENTS_TRACEABILITY.md
previous phase test report
current Git status
current branch
```

## Step B — Verify previous phase

Do not trust the previous agent message.

Run at least:

```text
git status
git rev-parse HEAD
relevant smoke tests
```

Confirm previous phase is actually VERIFIED.

## Step C — Discover

Before editing:

```text
find files
search imports
search callers
search tests
search config
search migrations
search docs
```

## Step D — Write phase plan

Create:

```text
docs/reports/PHASE_<NN>_PLAN.md
```

containing:

```text
objective
current behavior
target behavior
files
dependencies
risks
data changes
API changes
test plan
rollback plan
```

## Step E — Update GitHub

Add the plan to the relevant issue/comment before implementation where practical.

## Step F — Implement incrementally

Use focused commits.

Do not create a giant “fix all” commit.

## Step G — Run tests during development

Use targeted tests first.

Then phase-wide tests.

Then regression.

## Step H — Perform adversarial testing

Ask:

```text
What invalid input can reach this?
What happens if data is missing?
What if it belongs to another tenant?
What if it is unpublished?
What if it is expired?
What if the DB fails?
What if RAG fails?
What if the model fails?
What if the user retries?
What if the process restarts?
What if the request happens twice?
```

## Step I — Perform real-runtime verification

Whenever the phase changes runtime behavior, start the actual app/service and exercise the real path.

## Step J — Record evidence

Generate phase reports with exact numbers.

## Step K — Update local state

Update:

```text
PROJECT_STATE.yaml
DEVELOPMENT_LOG.md
BUG_REGISTER.md
REQUIREMENTS_TRACEABILITY.md
```

## Step L — Update GitHub

Record:

```text
commit
test counts
failures
E2E status
security status
remaining risks
```

## Step M — Gate

Only then mark:

```text
VERIFIED
```

---

# 14. BUG MANAGEMENT PROTOCOL

Every discovered bug must be entered immediately.

Format:

```text
BUG-ID:
Severity:
Subsystem:
First observed:
Commit:
Environment:
Reproduction:
Expected:
Actual:
Root cause:
Impact:
Fix:
Regression test:
Verification:
GitHub issue:
Status:
```

Statuses:

```text
DISCOVERED
CONFIRMED
IN_PROGRESS
FIXED
VERIFIED
CLOSED
```

A bug is not CLOSED until a regression test proves it.

---

# 15. SEVERITY RULES

## P0

Security leak, data corruption, impossible startup, total tutor failure, release-blocking architecture defect.

## P1

Major workflow failure, cross-course contamination, broken publication, broken RAG isolation, broken sync, critical offline failure.

## P2

Meaningful functional defect with workaround.

## P3

Minor defect or documentation/quality issue.

P0/P1 must block release unless explicitly accepted by the project owner.

---

# 16. REAL TESTING RULES

The agent must distinguish:

```text
UNIT
INTEGRATION
SYSTEM
E2E
FAILURE-INJECTION
SECURITY
PERFORMANCE
DEPLOYMENT
```

Never combine these into a single “X tests passed” statement.

A final report should instead say, for example:

```text
Unit:
  collected 412
  passed 410
  failed 2

Integration:
  collected 86
  passed 86

E2E:
  journeys 11
  passed 10
  failed 1

Security:
  scenarios 37
  passed 37

Failure injection:
  scenarios 18
  passed 17
  failed 1
```

Then explain every failure.

---

# 17. TRUE E2E REQUIREMENT

A real E2E test must exercise the real boundary:

```text
user/UI
 ↓
HTTP API or actual local app service boundary
 ↓
authorization
 ↓
application service
 ↓
database
 ↓
RAG
 ↓
AI gateway
 ↓
state/event persistence
 ↓
response
 ↓
user/UI
```

A direct Python service call is NOT E2E.

---

# 18. FOUR-COURSE GENERICITY TEST

Mandatory regression fixture courses:

```text
Chemistry
Physics
History
Programming
```

The exact content can be small.

The goal is architectural proof.

For each course:

```text
create
publish
enroll
open tutor
retrieve knowledge
ask question
record learning
show progress
```

The same generic code path must be used.

---

# 19. CHEMISTRY DISABLEMENT TEST

At least one CI/test execution must prove:

```text
Chemistry adapter disabled
        ↓
platform starts
        ↓
generic course created
        ↓
content published
        ↓
student enrolled
        ↓
RAG works
        ↓
tutor works
        ↓
mastery works
```

If this fails, the platform is still Chemistry-dependent.

---

# 20. MANDATORY AUTHORIZATION MATRIX

| Actor | Resource | Expected |
|---|---|---|
| Org A student | Org A enrolled course | ALLOW |
| Org A student | Org B private course | DENY |
| Org A student | Org A class notes | ALLOW if class member |
| Org A student | Org A other-class notes | DENY |
| Org A student | another student's remedial content | DENY |
| Org A teacher | assigned course/class | ALLOW |
| Org A teacher | Org B course | DENY |
| Org A teacher | publish without permission | DENY |
| Org A admin | own organization course | ALLOW |
| Org A admin | Org B private course | DENY |
| Public catalog | public course metadata | ALLOW |
| Public catalog | private content | DENY |

---

# 21. MANDATORY VERSIONING MATRIX

Test:

```text
V1 DRAFT
V1 READY_FOR_REVIEW
V1 PUBLISHED
V2 DRAFT
V2 READY_FOR_REVIEW
V2 PUBLISHED
V1 historical session
V2 new session
```

Verify:

```text
RAG isolation
curriculum isolation
assessment isolation
student history
course offering behavior
```

---

# 22. MANDATORY OFFLINE MATRIX

```text
offline first launch
offline cached course
offline uncached course
offline local model missing
offline DB read-only
offline session restart
offline interrupted turn
network restored
sync
duplicate sync
partial sync
```

---

# 23. MANDATORY CONTENT MATRIX

```text
PDF
DOCX
TXT
Markdown
empty
corrupt
oversized
unsupported
duplicate
partial upload
failed parsing
failed indexing
draft
published
archived
```

---

# 24. MANDATORY FAILURE MATRIX

```text
model missing
model corrupt
provider timeout
provider malformed output
RAG unavailable
DB unavailable
sync interrupted
duplicate event
invalid upload
expired instruction
revoked instruction
unauthorized course
unauthorized content
stale course version
app crash mid-turn
```

Each must have explicit expected behavior.

---

# 25. NO SILENT FALLBACK POLICY

Acceptable:

```text
RAG unavailable
→ RAG_ERROR
→ explicit degraded state
→ no unauthorized/global retrieval
```

Not acceptable:

```text
RAG unavailable
→ []
→ continue as SUCCESS
```

Acceptable:

```text
model missing
→ MODEL_UNAVAILABLE
→ approved fallback if policy allows
→ telemetry records fallback
```

Not acceptable:

```text
model missing
→ fake response
→ turn marked committed
```

---

# 26. GITHUB TRACKING POLICY

Each phase should have a GitHub issue or a clearly identified parent issue.

Issue body must contain:

```text
Objective
Acceptance criteria
Files/components
Test plan
Known risks
```

Start comment:

```text
PHASE STARTED
branch:
base commit:
scope:
```

Progress comment:

```text
PHASE PROGRESS
completed:
remaining:
bugs found:
tests:
```

Completion comment:

```text
PHASE VERIFIED
commit:
tests:
E2E:
security:
migration:
failure tests:
reports:
remaining risks:
```

Do not close issue until the phase gate is VERIFIED.

---

# 27. GIT SAFETY RULES

Before changes:

```bash
git status --short --branch
git rev-parse HEAD
```

Before commit:

```bash
git diff --check
git diff --stat
git status
```

Before push:

```text
confirm branch
confirm commit
confirm report
confirm no accidental secrets
confirm no unrelated files
```

Never:

```text
force-push
rewrite history
delete another branch
```

without explicit authorization.

---

# 28. CLEANUP RULE

A file is not obsolete because its name looks old.

Before deletion:

```text
search callers
search imports
search tests
search docs
search packaging
search runtime entrypoints
```

Classify:

```text
ACTIVE
TEST_ONLY
HISTORICAL
LEGACY
DUPLICATE
OBSOLETE
UNKNOWN
```

Delete only when evidence supports deletion.

---

# 29. FINAL RELEASE GATE

Release is BLOCKED when any of these remain:

```text
P0 bug
P1 bug
tenant leakage
student leakage
RAG scope violation
unpublished content visible
generic tutor depends on Chemistry
legacy runtime dependency
production demo data
multiple model sources of truth
unknown migration behavior
false E2E claim
mandatory skipped tests
unknown failure
broken offline resume
broken sync idempotency
```

Release PASS requires:

```text
architecture guards pass
unit tests pass
integration tests pass
real E2E pass
security pass
failure injection pass
migration pass
offline pass
sync pass
clean install pass
release verification pass
documentation reconciled
GitHub reconciled
```

---

# 30. FINAL OUTPUTS

The final repository should contain:

```text
PROJECT_STATE.yaml

docs/
  ARCHITECTURE_TARGET.md
  DATA_MODEL_TARGET.md
  SECURITY_MODEL_TARGET.md
  TESTING_STRATEGY_TARGET.md
  AGENT_DEVELOPMENT_RULES.md

docs/reports/
  DEVELOPMENT_LOG.md
  BUG_REGISTER.md
  REQUIREMENTS_TRACEABILITY.md
  PHASE_00_FORENSICS.md
  PHASE_00_FILE_INVENTORY.csv
  PHASE_00_RUNTIME_GRAPH.md
  PHASE_00_TEST_BASELINE.md
  PHASE_01_TEST_REPORT.md
  ...
  PHASE_27_TEST_REPORT.md
  FINAL_PRODUCTION_READINESS_REPORT.md
  FINAL_PRODUCTION_READINESS.json
  FINAL_TEST_REPORT.md
  FINAL_TEST_RESULTS.json
```

---

# 31. FINAL AGENT BEHAVIOR REQUIREMENT

The local AI agent must behave as:

```text
architect
+
developer
+
tester
+
security reviewer
+
database reviewer
+
reliability engineer
+
release engineer
```

For every change it must ask:

```text
What depends on this?
What assumptions does this add?
What breaks if this is missing?
What happens with wrong input?
What happens with wrong tenant?
What happens with wrong course?
What happens with wrong class?
What happens with wrong student?
What happens with wrong version?
What happens offline?
What happens after restart?
What happens on retry?
What happens on duplicate?
What happens when RAG fails?
What happens when model fails?
Can this falsely appear successful?
```

If the answer is unknown, the agent must investigate instead of assuming.

---

# 32. FINAL PRINCIPLE

The platform is not complete because:

```text
the code compiles
```

or:

```text
the tests are green
```

or:

```text
the UI opens
```

It is complete only when:

```text
the real workflow works
+
the wrong workflow is rejected
+
failures are explicit
+
data is isolated
+
state survives restart
+
offline works
+
sync is safe
+
the generic core is actually generic
+
legacy is removed
+
the evidence is reproducible
+
local state matches GitHub
```

**Execute one phase at a time. Verify before advancing. Never hide uncertainty.**
