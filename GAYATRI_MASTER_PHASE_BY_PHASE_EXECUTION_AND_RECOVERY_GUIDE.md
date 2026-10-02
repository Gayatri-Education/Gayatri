# GAYATRI --- MASTER PHASE-BY-PHASE EXECUTION & RECOVERY GUIDE

**Repository:** https://github.com/Gayatri-Education/Gayatri\
**Source contract:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`\
**Purpose:** Authoritative execution guide for a local AI coding agent
to complete Phases 0--27, reconcile the current repository, fix
discovered defects, verify every phase, and synchronize truthful
evidence to GitHub.

> **IMPORTANT:** This document extends the existing phase plan. It does
> not replace its product decisions or phase order. It adds stricter
> execution, defect-recovery, evidence, GitHub, and release-control
> requirements based on the current repository audit.

------------------------------------------------------------------------

# 1. NON-NEGOTIABLE EXECUTION CONTRACT

The agent MUST execute exactly one phase at a time.

``` text
READ CURRENT STATE
      ↓
VERIFY PREVIOUS PHASE
      ↓
DISCOVER ACTUAL CODE
      ↓
WRITE PHASE PLAN
      ↓
UPDATE GITHUB BEFORE/AT START
      ↓
IMPLEMENT IN SMALL COMMITS
      ↓
TARGETED TESTS
      ↓
NEGATIVE / FAILURE TESTS
      ↓
REGRESSION TESTS
      ↓
REAL RUNTIME VERIFICATION
      ↓
SECURITY / ISOLATION VERIFICATION
      ↓
WRITE EVIDENCE REPORT
      ↓
UPDATE BUG REGISTER
      ↓
UPDATE REQUIREMENTS TRACEABILITY
      ↓
UPDATE PROJECT_STATE
      ↓
PUSH TO GITHUB
      ↓
VERIFY REMOTE STATE
      ↓
PHASE GATE
      ↓
ONLY IF VERIFIED → NEXT PHASE
```

Never skip a box.

The following states are distinct:

``` text
NOT_STARTED
DISCOVERED
PLANNED
IMPLEMENTED
TESTED
E2E_VERIFIED
SECURITY_VERIFIED
VERIFIED
BLOCKED
```

`IMPLEMENTED` is not `VERIFIED`.

`TESTS PASSED` is not `E2E_VERIFIED`.

`E2E_VERIFIED` is not `PRODUCTION_READY`.

------------------------------------------------------------------------

# 2. CURRENT REPOSITORY RECOVERY RULE

The current repository audit identified issues that must be treated as
open defects even if historical trackers say they are complete.

At minimum, the agent MUST explicitly investigate and close:

1.  Synthetic / demo authentication paths.
2.  Public or privileged demo-token generation.
3.  Optional authentication on sensitive tutor/tool/learning/sync
    routes.
4.  Caller-supplied `student_id` not cryptographically bound to the
    authenticated user.
5.  Tutor-side automatic identity creation.
6.  Tutor-side automatic enrollment as an unintended side effect.
7.  Fail-open/default tool policies.
8.  Hardcoded JWT secret fallback.
9.  In-memory token revocation.
10. Legacy `server.py` imports from active runtime paths.
11. Legacy `SyncManager` compatibility path.
12. Chemistry-specific RAG fallback in generic RAG.
13. Silent exception handling that converts failure into apparently
    valid behavior.
14. Deployment validation that can report readiness without real health
    probes.
15. Deployment validation that treats missing production secrets as
    non-blocking.
16. SQLite-centric database implementation where production PostgreSQL
    is claimed.
17. In-memory tutor deduplication.
18. Magic course/version fallback such as invented `v1.0`.
19. Stale branch/status/test-count documentation.
20. Current GitHub CI status not being conflated with historical local
    test results.

These defects are not optional cleanup. If any P0/P1 item remains open,
the final state MUST remain `BLOCKED` or `PARTIAL`.

------------------------------------------------------------------------

# 3. AUTHORITATIVE PRODUCT TARGET

Gayatri is a course-independent educational platform.

The canonical workflow is:

``` text
Organization
    ↓
Course
    ↓
PUBLIC / PRIVATE
    ↓
Course Version
    ↓
Teacher Content Upload
    ↓
Admin Review
    ↓
Publish
    ↓
Organization Offering
    ↓
Student Enrollment
    ↓
Student Session
    ↓
Course-scoped Tutor
    ↓
Course-scoped RAG
    ↓
Course-scoped Learning State
    ↓
Teacher Instructions
    ↓
Course Tools
    ↓
Learning Events
    ↓
Analytics / SLR
```

Online and offline must use the same domain semantics.

Chemistry must be an adapter/course package, not a generic runtime
assumption.

------------------------------------------------------------------------

# 4. LOCKED ENGINEERING RULES

## 4.1 Never trust a tracker without verifying code

At the beginning of every phase:

``` bash
git status --short --branch
git rev-parse HEAD
git log --oneline --decorate -20
```

Then inspect the actual implementation.

If:

``` text
tracker = DONE
code = incomplete
```

then the tracker is wrong.

Correct the tracker before proceeding.

## 4.2 Never create a fake green test

Do not:

-   delete failing tests;
-   weaken assertions;
-   change benchmark inputs merely to improve scores;
-   mark integration tests as E2E;
-   mock the entire subsystem being tested;
-   skip a failure without documenting why.

## 4.3 No silent failure

Forbidden:

``` python
except Exception:
    pass
```

or any equivalent that causes an error to disappear.

If recovery is intentional:

``` text
catch
→ classify
→ log
→ record telemetry
→ return explicit failure/recovery state
```

## 4.4 No magic identity

Never infer:

``` text
student_id = session_id
student = default student
course = Chemistry
school = demo school
version = v1.0
```

When required context is missing, fail clearly.

## 4.5 Authorization belongs below the UI

A request is not authorized because the frontend hides a button.

Authorization must exist at:

``` text
API
→ application service
→ domain/service boundary
→ repository/data boundary
```

## 4.6 RAG authorization happens before retrieval

Never:

``` text
retrieve everything
→ filter afterward
```

Required:

``` text
resolve authorized course/version/scope
→ build restricted retrieval query
→ retrieve only authorized content
```

## 4.7 Published content is immutable

Do not edit a published course version in place.

Create:

``` text
new version
→ review
→ publish
```

## 4.8 One source of truth

There must be one authoritative source for:

-   model registry;
-   database configuration;
-   course identity;
-   learning identity;
-   authorization;
-   runtime entrypoint;
-   release version;
-   progress state.

------------------------------------------------------------------------

# 5. REQUIRED REPOSITORY CONTROL FILES

The agent MUST maintain:

``` text
PROJECT_STATE.yaml
docs/reports/DEVELOPMENT_LOG.md
docs/reports/BUG_REGISTER.md
docs/reports/REQUIREMENTS_TRACEABILITY.md
docs/reports/GITHUB_SYNC_QUEUE.md
```

Each phase MUST create:

``` text
docs/reports/PHASE_<NN>_PLAN.md
docs/reports/PHASE_<NN>_TEST_REPORT.md
docs/reports/PHASE_<NN>_TEST_RESULTS.json
```

Where applicable:

``` text
docs/reports/PHASE_<NN>_E2E_REPORT.md
docs/reports/PHASE_<NN>_SECURITY_REPORT.md
docs/reports/PHASE_<NN>_MIGRATION_REPORT.md
docs/reports/PHASE_<NN>_FAILURE_INJECTION_REPORT.md
```

Final:

``` text
docs/reports/FINAL_PRODUCTION_READINESS_REPORT.md
docs/reports/FINAL_PRODUCTION_READINESS.json
docs/reports/FINAL_TEST_REPORT.md
docs/reports/FINAL_TEST_RESULTS.json
```

------------------------------------------------------------------------

# 6. PROJECT_STATE.YAML REQUIREMENTS

The state file MUST contain actual evidence.

``` yaml
project:
  name: Gayatri
  repository: Gayatri-Education/Gayatri
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
  scoped_learning_state:
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
  plan_comment:
  implementation_commits:
  verification_comment:
  last_push:
  remote_sync:

last_verified:
  timestamp:
  commit:
  report:
```

Never update a count optimistically.

------------------------------------------------------------------------

# 7. STANDARD PHASE EXECUTION PROTOCOL

Every phase uses this exact protocol.

## STEP A --- Recover

Read:

``` text
PROJECT_STATE.yaml
BUG_REGISTER.md
DEVELOPMENT_LOG.md
REQUIREMENTS_TRACEABILITY.md
previous phase report
```

Then:

``` bash
git status
git rev-parse HEAD
git log --oneline -20
```

## STEP B --- Verify previous phase

The previous phase must have:

``` text
status = VERIFIED
```

and a real report.

If not:

``` text
STOP
→ repair previous phase
→ reverify
→ continue
```

## STEP C --- Discover

Search:

``` text
files
imports
callers
routes
configuration
migrations
tests
fixtures
environment variables
runtime entrypoints
dead code
legacy references
hardcoded domain identifiers
```

## STEP D --- Write the plan

Create:

``` text
docs/reports/PHASE_<NN>_PLAN.md
```

with:

``` text
Objective
Current behavior
Target behavior
Known defects
Files/modules
Dependencies
Database impact
API impact
Security impact
Offline impact
Test plan
Failure plan
Rollback plan
GitHub issue
Acceptance criteria
```

## STEP E --- GitHub pre-implementation update

Open/update the phase issue.

Comment:

``` text
PHASE <NN> START

Base commit:
Branch:
Previous phase verification:
Objective:
Known defects:
Planned files:
Tests:
Security checks:
E2E requirement:
Rollback:
Acceptance gate:
```

Do not claim work is complete.

## STEP F --- Implement incrementally

Prefer commits:

``` text
phase-XX: add domain change
phase-XX: add persistence/migration
phase-XX: add API/runtime integration
phase-XX: add tests
phase-XX: harden failure paths
```

Avoid:

``` text
phase-XX: fix everything
```

## STEP G --- Targeted tests

Run tests nearest to the change.

## STEP H --- Adversarial tests

Always ask:

``` text
What if identity is missing?
What if identity is forged?
What if tenant is wrong?
What if course is wrong?
What if version is unpublished?
What if version is archived?
What if content is missing?
What if RAG fails?
What if model fails?
What if DB fails?
What if network fails?
What if the request is duplicated?
What if the process restarts?
What if two workers execute simultaneously?
What if the client retries?
What if the data belongs to another organization?
What if a teacher instruction is malicious?
What if retrieved text contains instructions?
```

## STEP I --- Real runtime

Start the actual service/application.

Do not substitute:

``` text
direct Python class call
```

for:

``` text
real HTTP/UI/desktop boundary
```

when runtime behavior is being verified.

## STEP J --- Record failures

Every failure becomes a bug entry.

## STEP K --- Update reports

Record exact:

``` text
commit
branch
environment
Python
OS
dependencies
command
scope
collected
passed
failed
skipped
xfailed
duration
coverage
result
```

## STEP L --- Update project state

Only after tests are complete.

## STEP M --- Push

Push the actual commit.

Then independently verify:

``` bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/<branch>
```

The local and remote SHA must match for a completed GitHub
synchronization.

## STEP N --- GitHub verification comment

Comment:

``` text
PHASE <NN> VERIFICATION

Implementation commit(s):
Final commit:
Tests:
E2E:
Security:
Failure injection:
Migration:
Runtime:
Known limitations:
P0:
P1:
Remote SHA:
Gate:
```

## STEP O --- Gate

Only:

``` text
PASS
```

permits the next phase.

------------------------------------------------------------------------

# 8. BUG MANAGEMENT PROTOCOL

Every bug uses:

``` text
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
Blocking phase:
```

Severity:

``` text
P0 = security/data-loss/core-runtime release blocker
P1 = serious correctness/reliability/authorization defect
P2 = important non-blocking defect
P3 = minor/documentation/UX defect
```

Rules:

-   P0 must be closed before any phase can pass.
-   P1 must be closed before production readiness.
-   A P2 may remain only with explicit owner and rationale.
-   P3 may remain only if documented.
-   A bug is not closed because a code change exists.
-   A bug closes only after its regression test passes.

------------------------------------------------------------------------

# 9. REQUIRED GITHUB WORKFLOW

## 9.1 One issue per phase

Use a consistent title:

``` text
Phase NN — <phase name>
```

Labels where available:

``` text
phase
architecture
bug
security
testing
migration
e2e
release
```

## 9.2 Phase start comment

Always include:

``` text
Base SHA
Current branch
Previous phase evidence
Objective
Known bugs
Implementation scope
Acceptance criteria
```

## 9.3 During implementation

Use small commits.

Each commit should have one logical purpose.

## 9.4 Phase completion comment

Must include exact evidence.

Never write:

``` text
Done.
All tests passed.
```

Write:

``` text
Commit:
Environment:
Command:
Collected:
Passed:
Failed:
Skipped:
E2E:
Security:
Failure injection:
Migration:
Runtime:
Known issues:
Gate:
```

## 9.5 GitHub remote failure

If GitHub cannot be updated:

``` text
REMOTE_SYNC = BLOCKED
```

and create:

``` text
docs/reports/GITHUB_SYNC_QUEUE.md
```

with:

``` text
timestamp
phase
intended branch
local SHA
intended push
intended issue update
reason remote update failed
```

Never claim a push occurred if it did not.

------------------------------------------------------------------------

# 10. PHASE 0 --- FORENSIC BASELINE & BRANCH RECONCILIATION

## Objective

Freeze the true repository state before further architecture work.

## Required work

-   Determine canonical branch from actual Git/GitHub evidence.
-   Compare `main`, `master`, and other active branches.
-   Inventory every source file.
-   Classify active/test/legacy/duplicate/obsolete files.
-   Trace runtime entrypoints.
-   Trace API routes.
-   Trace database initialization.
-   Trace RAG.
-   Trace model provider paths.
-   Trace UI/desktop paths.
-   Trace migrations.
-   Trace test boundaries.
-   Find hardcoded Chemistry/demo identifiers.
-   Find legacy imports.
-   Find silent exception handling.
-   Establish baseline tests.

## Mandatory outputs

``` text
PHASE_00_FORENSICS.md
PHASE_00_FILE_INVENTORY.csv
PHASE_00_RUNTIME_GRAPH.md
PHASE_00_TEST_BASELINE.md
PHASE_00_CONFIG_AUDIT.md
PHASE_00_SCHEMA_AUDIT.md
PHASE_00_CHEMISTRY_COUPLING.md
PHASE_00_LEGACY_REACHABILITY.md
```

## Gate

PASS only when:

-   canonical branch is documented;
-   baseline is reproducible;
-   all known P0/P1 defects are registered;
-   current runtime path is known;
-   tracker contradictions are documented.

Do not fix major architecture in Phase 0 unless necessary to establish a
valid baseline.

------------------------------------------------------------------------

# 11. PHASE 1 --- ARCHITECTURE CONTRACT & REPOSITORY GUARDRAILS

## Objective

Create machine-enforced architectural boundaries.

## Required work

Define:

``` text
presentation
application
domain
repositories
infrastructure
adapters
```

Add architecture tests preventing:

-   generic core → Chemistry imports;
-   production code → legacy imports;
-   production runtime → demo seed data;
-   multiple model configuration sources;
-   duplicate migration DDL;
-   unauthorized direct DB manipulation from UI.

Add CI checks.

## Critical remediation

Create guards specifically for the current audit findings:

``` text
no from server import in production runtime
no Chemistry fallback in generic RAG
no demo-token route in production
no hardcoded JWT secret
no optional auth on protected routes
```

## Gate

Architecture violations must make CI fail.

------------------------------------------------------------------------

# 12. PHASE 2 --- CANONICAL COURSE, VERSION & OFFERING DOMAIN

## Objective

Create the core course abstraction.

Entities:

``` text
Course
CourseVersion
CourseOffering
Organization
Enrollment
```

Support:

``` text
PUBLIC
PRIVATE
DRAFT
READY_FOR_REVIEW
PUBLISHED
ARCHIVED
```

## Required behavior

-   Public courses can be discovered according to policy.
-   Private courses cannot cross organization boundaries.
-   Course versions are immutable after publish.
-   Organization selection is separate from course identity.
-   Students can belong to multiple courses.
-   Duplicate enrollment is rejected.
-   No default Chemistry course is silently created.

## Tests

Include fresh DB, migrated DB, migration replay, isolation,
immutability.

## Gate

Persisted domain behavior must work without Chemistry-specific defaults.

------------------------------------------------------------------------

# 13. PHASE 3 --- GENERIC CURRICULUM & VERSIONED LEARNING GRAPH

## Objective

Replace Chemistry-specific curriculum logic with data-driven curriculum.

Generic structure:

``` text
CourseVersion
→ Curriculum
→ Subject
→ Module
→ Topic
→ Concept
→ Prerequisite
```

## Required fixtures

At minimum:

``` text
Chemistry
Physics
History
Programming
```

The same engine must load all four.

## Required negative tests

-   cyclic prerequisites;
-   orphan concept;
-   missing version;
-   duplicate concept ID;
-   cross-course concept collision;
-   global Chemistry keyword fallback.

## Gate

Generic curriculum must work with Chemistry adapter disabled.

------------------------------------------------------------------------

# 14. PHASE 4 --- COURSE-SCOPED STUDENT LEARNING STATE & SESSIONS

## Objective

Make learning state course-aware and version-aware.

Canonical identity:

``` text
student
+
course
+
course_version
+
concept
```

## Required work

-   Build authoritative `CourseLearningContext`.
-   Require course context.
-   Associate sessions with course/version.
-   Associate events with student/org/course/version.
-   Make event IDs idempotent.
-   Make mastery course-scoped.
-   Make misconceptions course-scoped.
-   Make analytics course-scoped.
-   Remove magic identity fallbacks.
-   Reject ambiguous requests.

## Critical remediation

Fix any path where:

``` text
student_id = session_id
```

or equivalent inference is used.

## Restart test

``` text
write state
→ stop process
→ restart
→ load state
→ compare exact state
```

## Gate

Cross-course contamination matrix must be green.

------------------------------------------------------------------------

# 15. PHASE 5 --- KNOWLEDGE ASSET INGESTION & PUBLICATION PIPELINE

## Objective

Create controlled teacher upload → processing → review → publish
workflow.

Workflow:

``` text
Teacher upload
→ validate file
→ malware/type/size checks
→ parse
→ chunk
→ create candidate asset
→ teacher submits
→ admin reviews
→ admin publishes
→ version becomes student-visible
```

## Required visibility

``` text
COURSE
CLASS
STUDENT
```

Publication and visibility must remain separate.

## Negative tests

-   unpublished content invisible;
-   private content inaccessible cross-org;
-   class notes invisible outside class;
-   remedial content invisible to other students;
-   corrupted document fails explicitly.

------------------------------------------------------------------------

# 16. PHASE 6 --- SCOPED RAG & KNOWLEDGE AUTHORIZATION

## Objective

Make retrieval course/version/scope authorized before retrieval.

Required flow:

``` text
authenticated user
→ authorization
→ course/version resolution
→ visibility policy
→ retrieval query
→ scoped retrieval
→ source validation
→ citations/provenance
```

## Critical remediation

REMOVE:

``` text
legacy Chemistry fallback
global Chemistry keyword retrieval
retrieve-everything-then-filter
silent parse failures
```

If RAG cannot resolve required context:

``` text
explicit RAG_UNAVAILABLE / CONTEXT_REQUIRED
```

not:

``` text
Chemistry answer
```

## Prompt-injection protection

Retrieved content is data, never instructions.

## Gate

Prove:

``` text
Physics query → no Chemistry evidence
History query → no Chemistry evidence
Student A → cannot retrieve Student B scoped content
Org A → cannot retrieve Org B private content
```

------------------------------------------------------------------------

# 17. PHASE 7 --- TEACHER INSTRUCTION HIERARCHY

Scopes:

``` text
ORGANIZATION
COURSE
CLASS
STUDENT
SESSION
```

Precedence:

``` text
platform safety
→ organization
→ course
→ class
→ student
→ session
```

Instructions must be:

-   authenticated;
-   authorized;
-   persisted;
-   validated;
-   time-bounded;
-   revocable;
-   auditable.

Never inject raw teacher text directly as a privileged system
instruction.

## Negative tests

-   unauthorized teacher;
-   expired instruction;
-   revoked instruction;
-   cross-class leakage;
-   cross-student leakage;
-   prompt injection;
-   conflict precedence.

------------------------------------------------------------------------

# 18. PHASE 8 --- COURSE TOOL CAPABILITY & ADAPTER REGISTRY

## Objective

Make tools explicit capabilities.

Example:

``` text
calculator
equation_balancer
periodic_table
graphing
code_execution
```

Each tool requires:

``` text
schema
role policy
course policy
resource limits
timeout
audit
```

## Critical remediation

NO fail-open behavior.

If course policy cannot be resolved:

``` text
deny
```

not:

``` text
enable default tools
```

If user is unauthenticated:

``` text
401
```

not:

``` text
assume STUDENT
```

## Gate

Unauthorized tool execution must fail.

------------------------------------------------------------------------

# 19. PHASE 9 --- MODEL REGISTRY & AI GATEWAY UNIFICATION

## Objective

One authoritative model/provider configuration.

Manifest must define:

``` text
model_id
provider
artifact
format
quantization
prompt template
context window
streaming
tool capabilities
resource profile
checksum
```

## Critical remediation

Remove:

-   hardcoded model fallback;
-   silent provider switching;
-   legacy inference imports;
-   undocumented provider fallback.

## Secret requirement

Production signing/provider secrets cannot have insecure source-code
fallbacks.

Missing required secret must be:

``` text
FAIL
```

not:

``` text
WARN
```

## Failure tests

-   model missing;
-   model corrupt;
-   wrong checksum;
-   provider timeout;
-   provider malformed output;
-   provider unavailable;
-   local-only policy;
-   cancellation;
-   streaming interruption.

------------------------------------------------------------------------

# 20. PHASE 10 --- GENERIC TUTOR ORCHESTRATOR

## Objective

Central tutor flow must use resolved context, not Chemistry mode.

Required context:

``` text
user
organization
enrollment
course
course_version
class
concept
instructions
learning_state
authorized_RAG
tools
model_policy
```

If any required field is ambiguous:

``` text
fail explicitly
```

## Critical remediation

Do NOT:

``` text
create student
auto-enroll student
invent course
invent version
```

inside a normal tutor-turn request.

Enrollment must be a first-class domain action.

## Tutor lifecycle

``` text
request
→ validate identity
→ resolve context
→ authorize
→ understand intent
→ retrieve
→ plan
→ generate
→ validate
→ record event
→ update learning state
→ return response
```

------------------------------------------------------------------------

# 21. PHASE 11 --- GENERIC ASSESSMENT & EVALUATION

## Objective

Build course-independent assessment.

Support:

``` text
MCQ
short answer
numerical
structured response
conceptual
coding where applicable
```

Deterministic evaluation must be used where possible.

LLM evaluation must return structured data and confidence.

## Negative tests

-   malformed answer;
-   unsupported assessment type;
-   duplicate submission;
-   unauthorized assessment;
-   wrong course;
-   wrong version;
-   evaluator unavailable.

------------------------------------------------------------------------

# 22. PHASE 12 --- REAL ONLINE API BOUNDARY

## Objective

Expose the platform through the actual online API.

## Critical security requirements

Protected endpoints must require authentication.

Review:

``` text
/tutor
/tools
/learning
/sync
/student
/teacher
/admin
```

Every endpoint must explicitly answer:

``` text
Who is calling?
What organization?
What student?
What course?
What version?
What permission?
```

## Critical remediation

Eliminate:

``` text
get_current_user_optional()
```

from protected operations unless there is an explicit public endpoint
policy.

A caller-provided `student_id` must never override authenticated
identity.

For students:

``` text
authenticated_user.id == target_student_id
```

For teachers/admins:

``` text
resource authorization service
```

must verify scope.

## Gate

Run actual HTTP requests against the running service.

------------------------------------------------------------------------

# 23. PHASE 13 --- OFFLINE LOCAL RUNTIME

## Objective

Provide a real local runtime using the same domain contracts.

Target:

``` text
UI
→ local API/service
→ local database
→ local course store
→ local RAG
→ local AI Gateway
→ local model
```

No hidden production-only assumptions.

## Required tests

-   fresh offline install;
-   course selection;
-   student session;
-   tutor;
-   RAG;
-   state persistence;
-   restart;
-   no network;
-   model missing;
-   corrupted local data.

------------------------------------------------------------------------

# 24. PHASE 14 --- SYNC & CONFLICT RESOLUTION

## Objective

Safe online/offline synchronization.

Required:

``` text
event ID
operation ID
device ID
student ID
course ID
course version
timestamp
sequence/version
payload hash
```

## Critical remediation

Remove or isolate legacy `SyncManager`.

One authoritative synchronization service must own synchronization.

## Idempotency

Duplicate event:

``` text
must not double count
```

Retry:

``` text
must not duplicate state
```

Out-of-order:

``` text
must resolve deterministically
```

Conflict:

``` text
must have explicit policy
```

------------------------------------------------------------------------

# 25. PHASE 15 --- ADMIN COURSE & CONTENT WORKFLOW UI

## Objective

Real UI for:

``` text
create course
edit draft
set public/private
create version
review content
approve
publish
archive
select offering
```

UI must consume real APIs.

No hardcoded Chemistry/demo data.

## E2E

Use browser/UI boundary, not direct service calls.

------------------------------------------------------------------------

# 26. PHASE 16 --- TEACHER WORKFLOW UI

Teacher must be able to:

``` text
view organization
view assigned courses
view classes
upload content
submit content
view student progress
create instructions
assign work
view interventions
```

Authorization must be enforced server-side.

Negative E2E:

``` text
Teacher A → Student B outside assigned scope → DENIED
```

------------------------------------------------------------------------

# 27. PHASE 17 --- STUDENT MULTI-COURSE WORKFLOW UI

Student must be able to:

``` text
login
view eligible courses
enroll
select course
select active version
start session
ask question
receive answer
see progress
switch course
resume previous course
```

Critical isolation:

``` text
Course A mastery
≠
Course B mastery
```

UI must not infer identity from route parameters.

------------------------------------------------------------------------

# 28. PHASE 18 --- TEACHER INSTRUCTION + RAG INTEGRATION

Integrate:

``` text
teacher instruction
+
course content
+
class/student scope
+
authorized RAG
+
tutor
```

Required precedence:

``` text
platform safety
→ teacher directive
→ authorized knowledge
→ student context
```

Teacher instruction cannot:

-   override security;
-   authorize access;
-   bypass RAG visibility;
-   expose another student's data;
-   turn unsafe behavior into allowed behavior.

Run prompt-injection and cross-scope tests.

------------------------------------------------------------------------

# 29. PHASE 19 --- CHEMISTRY ADAPTER EXTRACTION & DISABLEMENT TEST

## Objective

Prove the generic platform is actually generic.

Chemistry-specific code may contain:

``` text
reaction tools
periodic table
chemistry curriculum
chemistry normalization
chemistry deterministic tools
```

but generic code must not require it.

## Mandatory disablement test

Disable Chemistry adapter entirely.

Then prove:

``` text
Physics works
History works
Programming works
generic tutor works
generic RAG works
generic learning state works
```

If the platform stops working because Chemistry was disabled, Phase 19
fails.

------------------------------------------------------------------------

# 30. PHASE 20 --- LEGACY REMOVAL & DEAD-CODE CLEANUP

## Objective

Remove unreachable architecture and stale compatibility code.

## Critical remediation

The current repository still has active references to `server.py` from
platform code.

Search:

``` bash
grep -R "from server" .
grep -R "import server" .
grep -R "legacy" central_platform
grep -R "crs-chem-101" .
grep -R "demo" central_platform
```

Do not remove a file simply because it looks old.

First prove:

``` text
no production caller
no deployment dependency
no migration dependency
no test dependency that represents real runtime
```

Then delete/archive it.

## Gate

Legacy removal must be proven by import graph and runtime startup.

------------------------------------------------------------------------

# 31. PHASE 21 --- DATABASE & MIGRATION HARDENING

## Objective

Make persistence production-safe and migration-safe.

## Required work

-   one authoritative production database strategy;
-   PostgreSQL production path must be real, not merely documented;
-   SQLite local/offline path remains supported where intended;
-   migrations deterministic;
-   migration IDs unique;
-   rollback documented;
-   backups tested;
-   restore tested.

## Critical remediation

If `PlatformDatabase` remains SQLite-only while production PostgreSQL is
claimed, Phase 21 cannot pass.

## Tests

``` text
fresh DB
old DB
upgrade
downgrade/rollback where supported
duplicate migration
interrupted migration
backup
restore
restart
concurrent access
```

------------------------------------------------------------------------

# 32. PHASE 22 --- SECURITY, PRIVACY & ISOLATION AUDIT

## Objective

Perform a hostile security review.

## P0 checks

### Authentication

-   no synthetic production users;
-   no public privileged demo tokens;
-   no weak login fallback;
-   no default credentials.

### Authorization

-   no optional auth on protected routes;
-   no caller-controlled identity;
-   tenant isolation;
-   student isolation;
-   teacher cohort isolation;
-   admin scope.

### Secrets

-   no source-code production secrets;
-   no insecure fallback JWT secret;
-   required secrets fail closed.

### RAG

-   no cross-tenant retrieval;
-   no cross-course retrieval;
-   no private content leakage;
-   prompt injection defense.

### Tools

-   no unauthenticated execution;
-   no fail-open policy;
-   resource limits enforced.

### Tokens

-   durable revocation strategy;
-   correct expiry;
-   refresh token policy;
-   multi-worker behavior.

## Gate

Any P0/P1 security issue = FAIL.

------------------------------------------------------------------------

# 33. PHASE 23 --- RELIABILITY, FAILURE INJECTION & RECOVERY

## Objective

Prove that failures are explicit and recoverable.

Inject failures into:

``` text
database
RAG
model
provider
filesystem
network
sync
migration
serialization
tool execution
session persistence
```

For every failure:

``` text
detect
→ classify
→ log
→ return explicit status
→ preserve data
→ recover or fail safely
```

## Critical remediation

Fix all broad exception handlers that convert errors to success.

## Restart tests

``` text
during tutor turn
during sync
during RAG ingestion
during migration
during persistence
```

The system must not falsely report success.

------------------------------------------------------------------------

# 34. PHASE 24 --- REAL END-TO-END JOURNEYS & BROWSER/DESKTOP VERIFICATION

## Objective

Test the real product boundary.

## Mandatory journey A --- Student

``` text
login
→ course discovery
→ enrollment
→ start session
→ ask question
→ RAG
→ model
→ answer
→ learning event
→ mastery
→ progress
→ restart
→ resume
```

## Mandatory journey B --- Teacher

``` text
login
→ course
→ upload content
→ submit
→ review state
→ create instruction
→ view student
→ assign/remediate
```

## Mandatory journey C --- Admin

``` text
login
→ create course
→ public/private
→ approve
→ publish
→ offering
→ audit
```

## Mandatory negative journeys

``` text
wrong tenant
wrong student
wrong class
wrong course
wrong version
unpublished content
expired instruction
unauthorized tool
missing model
RAG failure
DB failure
```

These must be exercised through the real application boundary.

------------------------------------------------------------------------

# 35. PHASE 25 --- PERFORMANCE & CAPACITY VERIFICATION

## Objective

Measure, don't guess.

Measure:

``` text
startup time
first token latency
complete response latency
RAG latency
DB latency
sync latency
memory
CPU
concurrency
error rate
queue depth
```

Do not invent thresholds.

For every target threshold:

``` text
target
reason
environment
measurement method
observed result
```

## Required tests

-   single user;
-   concurrent users;
-   sustained load;
-   repeated sessions;
-   offline storage growth;
-   sync backlog;
-   model memory pressure.

## Gate

PASS only against explicitly justified deployment thresholds.

------------------------------------------------------------------------

# 36. PHASE 26 --- PACKAGING, CLEAN INSTALL & DEPLOYMENT VALIDATION

## Objective

Prove the release works outside the developer machine.

## Procedure

``` text
fresh clone/artifact
→ fresh environment
→ install
→ configure secrets
→ initialize DB
→ migrate
→ provision course
→ publish content
→ enroll student
→ run tutor
→ close
→ restart
→ verify state
```

## Required validation

-   dependencies;
-   Python version;
-   migrations;
-   model artifact;
-   checksums;
-   configuration;
-   secrets;
-   static assets;
-   offline assets;
-   startup;
-   shutdown;
-   restart.

## Critical remediation

Deployment validator must perform real checks.

It must not say:

``` text
database = UP
AI = UP
RAG = UP
```

without probing the actual subsystem.

Missing required secret must fail readiness.

------------------------------------------------------------------------

# 37. PHASE 27 --- DOCUMENTATION, STATE RECONCILIATION & FINAL RELEASE GATE

## Objective

Make documentation, implementation, tests, GitHub, and release artifacts
agree.

## Search for stale data

``` text
old branch names
old repository URLs
old test counts
old phase numbers
Chemistry-only claims
legacy imports
demo IDs
obsolete configuration
old model names
```

## Final reports

``` text
FINAL_PRODUCTION_READINESS_REPORT.md
FINAL_PRODUCTION_READINESS.json
FINAL_TEST_REPORT.md
FINAL_TEST_RESULTS.json
```

## Final report must state

``` text
exact commit
branch
timestamp
environment
Python
OS
dependencies
unit results
integration results
E2E results
security results
failure injection results
migration results
clean install results
performance results
known limitations
P0
P1
P2
release decision
```

No unsupported `PRODUCTION READY` claim.

------------------------------------------------------------------------

# 38. FINAL RELEASE GATE

Release is allowed only if ALL are true:

``` text
[ ] Canonical branch confirmed
[ ] Working tree clean
[ ] Remote SHA matches verified local SHA
[ ] Phase 0–27 evidence exists
[ ] Every phase is VERIFIED or explicitly reconciled
[ ] No P0
[ ] No unresolved P1 release blocker
[ ] Authentication is mandatory where required
[ ] Authorization is server-side
[ ] No synthetic production identity
[ ] No privileged demo-token endpoint
[ ] No hardcoded production secret
[ ] Token revocation is production-safe
[ ] No active legacy runtime dependency
[ ] No Chemistry fallback in generic runtime
[ ] RAG is scope-authorized
[ ] Tool policy is fail-closed
[ ] Course/version identity is explicit
[ ] Learning state is course-scoped
[ ] Enrollment is explicit
[ ] Published content is immutable
[ ] PostgreSQL production path is verified
[ ] SQLite offline path is verified
[ ] Sync is idempotent
[ ] Restart preserves state
[ ] Real E2E journeys pass
[ ] Browser/desktop verification passes where applicable
[ ] Failure injection passes
[ ] Clean install passes
[ ] CI passes
[ ] Documentation matches code
[ ] Final evidence is reproducible
```

If any mandatory item is false:

``` text
RELEASE = BLOCKED
```

------------------------------------------------------------------------

# 39. REQUIRED PHASE REPORT TEMPLATE

Every phase report must use:

``` markdown
# Phase NN — <Name>

## Status

VERIFIED / BLOCKED / PARTIAL

## Base

- Branch:
- Base SHA:
- Final SHA:
- Date:
- Environment:

## Objective

...

## Current behavior discovered

...

## Target behavior

...

## Changes implemented

...

## Files changed

...

## Database changes

...

## API changes

...

## Security changes

...

## Tests

### Unit

Command:
Collected:
Passed:
Failed:
Skipped:

### Integration

Command:
Collected:
Passed:
Failed:
Skipped:

### E2E

Command:
Collected:
Passed:
Failed:
Skipped:

### Failure injection

...

### Security

...

### Migration

...

### Runtime

...

## Bugs

- P0:
- P1:
- P2:
- P3:

## Known limitations

...

## GitHub

- Issue:
- Plan comment:
- Commits:
- Verification comment:
- Remote SHA:

## Gate

PASS / BLOCKED

## Next action

...
```

------------------------------------------------------------------------

# 40. REQUIRED TEST RESULT JSON

Every phase must produce machine-readable evidence:

``` json
{
  "phase": 0,
  "name": "",
  "status": "VERIFIED",
  "commit": "",
  "branch": "",
  "timestamp": "",
  "environment": {
    "os": "",
    "python": "",
    "dependencies": ""
  },
  "tests": {
    "unit": {
      "collected": 0,
      "passed": 0,
      "failed": 0,
      "skipped": 0
    },
    "integration": {},
    "e2e": {},
    "failure_injection": {},
    "security": {},
    "migration": {}
  },
  "bugs": {
    "p0": 0,
    "p1": 0,
    "p2": 0,
    "p3": 0
  },
  "runtime_verified": false,
  "github_synced": false,
  "gate": "BLOCKED"
}
```

Never fill unknown values with zero.

Use:

``` text
null
UNKNOWN
NOT_RUN
```

where appropriate.

------------------------------------------------------------------------

# 41. AGENT SESSION RECOVERY

If a coding-agent session ends unexpectedly:

``` text
READ PROJECT_STATE
↓
READ DEVELOPMENT_LOG
↓
READ BUG_REGISTER
↓
READ REQUIREMENTS_TRACEABILITY
↓
READ LAST PHASE REPORT
↓
git status
↓
git log -20
↓
git diff
↓
run previous phase smoke test
↓
verify GitHub SHA
↓
resume current phase
```

Do not begin the next phase merely because the previous agent said:

``` text
almost done
```

------------------------------------------------------------------------

# 42. STOP CONDITIONS

The agent MUST stop and report `BLOCKED` when:

-   authentication behavior is ambiguous;
-   authorization behavior is ambiguous;
-   database migration cannot be proven safe;
-   current branch is uncertain;
-   two competing runtime architectures are active;
-   test environment is invalid;
-   required dependency is missing;
-   model artifact cannot be verified;
-   production secret is missing;
-   RAG scope cannot be proven;
-   state persistence cannot be proven;
-   E2E test is impossible due to missing infrastructure;
-   a P0 remains unresolved.

Stopping is preferable to inventing evidence.

------------------------------------------------------------------------

# 43. WHAT THE AGENT MUST NEVER SAY WITHOUT EVIDENCE

Forbidden:

``` text
Production ready.
Fully secure.
All bugs fixed.
All tests passed.
E2E complete.
Database production ready.
Offline complete.
Sync complete.
Legacy removed.
Course independent.
```

unless the corresponding evidence exists.

Use:

``` text
VERIFIED: <specific evidence>
PARTIAL: <specific missing evidence>
BLOCKED: <specific blocker>
NOT TESTED: <specific test>
```

------------------------------------------------------------------------

# 44. DEFINITION OF A TRUE FIX

A bug is fixed only when:

``` text
root cause identified
+
implementation corrected
+
regression test added
+
negative case tested
+
runtime path verified
+
documentation updated
+
GitHub evidence recorded
```

Example:

``` text
Bug:
unauthenticated tutor request can specify arbitrary student_id.

Fix:
mandatory authentication + authenticated identity binding + service-level authorization.

Regression:
anonymous request → 401.
student A requesting student B → 403.
student A requesting own session → 200.
teacher authorized scope → 200.
teacher outside scope → 403.

Runtime:
actual HTTP request against running server.

Evidence:
test report + commit + GitHub comment.
```

------------------------------------------------------------------------

# 45. DEFINITION OF COURSE INDEPENDENCE

Course independence is proven only when:

``` text
Chemistry adapter ON
→ Chemistry works

Chemistry adapter OFF
→ Physics works
→ History works
→ Programming works
→ generic tutor works
→ generic RAG works
→ generic learning state works
→ generic assessment works
→ generic tools policy works
```

No source-code modification should be required to add a new course.

------------------------------------------------------------------------

# 46. DEFINITION OF ONLINE/OFFLINE PARITY

The same semantic operation must have equivalent behavior:

``` text
ONLINE
API
→ PostgreSQL
→ object/RAG storage
→ AI Gateway

OFFLINE
local service
→ SQLite
→ local course store
→ AI Gateway
```

Differences in transport/storage are acceptable.

Differences in:

``` text
authorization
course identity
learning identity
assessment semantics
event semantics
instruction precedence
RAG scope
```

are not acceptable.

------------------------------------------------------------------------

# 47. DEFINITION OF SAFE SYNC

Sync is safe only when:

``` text
events are append-oriented
IDs are stable
duplicates are idempotent
ordering is deterministic
conflicts have explicit policy
authorization is checked
course/version identity is preserved
failed events remain recoverable
restart does not lose acknowledged work
```

------------------------------------------------------------------------

# 48. DEFINITION OF REAL E2E

A real E2E test crosses real boundaries.

Valid:

``` text
browser
→ HTTP
→ auth
→ application
→ DB
→ RAG
→ AI provider
→ DB
→ HTTP
→ browser
```

or:

``` text
desktop UI
→ bridge
→ runtime
→ model
→ persistence
→ UI
```

Not sufficient:

``` python
orchestrator.execute_turn(...)
```

by itself.

------------------------------------------------------------------------

# 49. REQUIRED FINAL GitHub HISTORY

The final GitHub history should make the development sequence
understandable.

Preferred pattern:

``` text
phase-00: forensic baseline
phase-01: architecture guardrails
phase-02: course version domain
phase-03: generic curriculum
phase-04: scoped learning state
...
phase-22: security hardening
phase-23: failure recovery
phase-24: real e2e
phase-25: performance verification
phase-26: clean install
phase-27: final reconciliation
```

Do not squash evidence into an opaque mega-commit if doing so would
destroy the ability to trace phase changes.

------------------------------------------------------------------------

# 50. FINAL AGENT CHECKLIST

Before every phase:

``` text
[ ] Previous phase VERIFIED
[ ] Git status checked
[ ] Current SHA recorded
[ ] GitHub SHA checked
[ ] State files read
[ ] Bugs read
[ ] Requirements read
[ ] Actual code inspected
[ ] Call graph inspected
[ ] Tests inspected
```

During phase:

``` text
[ ] Plan written
[ ] GitHub updated
[ ] Implementation incremental
[ ] Targeted tests
[ ] Negative tests
[ ] Regression tests
[ ] Failure tests
[ ] Security tests
[ ] Runtime tests
```

After phase:

``` text
[ ] Report written
[ ] JSON evidence written
[ ] Bugs updated
[ ] Requirements traceability updated
[ ] PROJECT_STATE updated
[ ] Commit created
[ ] Pushed
[ ] Remote SHA verified
[ ] GitHub completion comment written
[ ] Gate explicitly PASS/BLOCKED
```

------------------------------------------------------------------------

# 51. FINAL SUCCESS CONDITION

Gayatri is complete only when the following real loop works:

``` text
                         STUDENT
                            │
                            ▼
                       STUDENT UI
                            │
                            ▼
                       PLATFORM API
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              AUTH/RBAC          LEARNING EVENT
                 │                     │
                 ▼                     ▼
             COURSE CONTEXT       EVENT STORE
                 │                     │
        ┌────────┼─────────┐           ▼
        ▼        ▼         ▼       LEARNING STATE
       RAG     TOOLS     MODEL          │
        │        │         │            ▼
        └────────┼─────────┘         ANALYTICS
                 ▼
              RESPONSE
                 │
                 ▼
              STUDENT
```

And all of the following must also work:

``` text
wrong identity → rejected
wrong tenant → rejected
wrong course → rejected
wrong version → rejected
unpublished content → rejected
unauthorized tool → rejected
RAG failure → explicit failure
model failure → explicit failure
DB failure → explicit/recoverable failure
duplicate request → idempotent
restart → state preserved
offline → works
sync → safe
Chemistry disabled → generic platform still works
legacy removed → runtime still works
clean install → works
GitHub evidence → matches implementation
```

**Final rule:**

> Do not move to the next phase because the code looks complete. Move
> only because the current phase has reproducible evidence, a passing
> gate, a synchronized GitHub state, and no unresolved blocker that
> violates the acceptance criteria.
