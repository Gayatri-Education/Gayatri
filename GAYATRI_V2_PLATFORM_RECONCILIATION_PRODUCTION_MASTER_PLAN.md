# Gayatri Goddess of Knowledge
# V2 Platform Reconciliation → Production Master Development Plan

**Repository:** `https://github.com/Gayatri-Education/Gayatri-Goddess-of-Knowledge`  
**Execution target:** A production-ready, three-sided adaptive learning platform with Student, Teacher, and Admin experiences.  
**Primary execution mode:** Local AI coding agent working locally first, committing to GitHub only after verification.

---

# 0. PURPOSE

This document is the **authoritative execution plan** for bringing the current repository from its partially migrated state to a fully integrated, production-ready platform.

The agent MUST NOT treat the existing project progress tracker as authoritative where it conflicts with actual repository evidence.

The repository currently contains substantial working tutor intelligence, RAG, adaptive learning, chemistry tooling, security foundations, and several Central Platform service prototypes.

However, the current Central Platform is not yet fully integrated.

The most important architectural gap is:

```text
CURRENT

Student Tutor Core
       +
Central Platform Service Prototypes
       +
In-memory / SQLite state
       +
Missing real web/API integration


TARGET

Student Desktop/Web
       ↓
Platform API
       ↓
Authentication + RBAC
       ↓
Central PostgreSQL
       ↓
Learning Events / SLR
       ↓
Learning Engine
       ↓
RAG / Curriculum / Assessments
       ↓
AI Gateway / Model Router
       ↓
Teacher Portal
       ↓
Admin Portal
```

The goal of this plan is to close every verified gap without unnecessarily rewriting working functionality.

---

# 1. NON-NEGOTIABLE EXECUTION CONTRACT

The AI agent MUST follow these rules.

## 1.1 Work locally first

Never make architectural changes directly against production.

Every phase must be developed and tested locally before being pushed.

## 1.2 Inspect before modifying

Before touching a module:

```text
inspect
→ understand dependencies
→ identify current behavior
→ identify tests
→ identify callers
→ design change
→ implement
```

## 1.3 Preserve working functionality

Do not rewrite the existing tutor engine merely because the new platform layer is being built.

Existing capabilities must remain functional unless a migration explicitly replaces them.

## 1.4 One phase at a time

Never implement multiple large architectural phases simultaneously.

A phase must reach:

```text
IMPLEMENTED
→ TESTING
→ DEBUGGING
→ REGRESSION
→ BACKTESTING
→ SECURITY
→ FRONTEND VERIFICATION
→ DOCUMENTATION
→ VERIFIED
```

before the next dependent phase begins.

## 1.5 No false completion

Code existing is NOT completion.

A feature is `VERIFIED` only when:

```text
implementation exists
AND
unit tests pass
AND
integration tests pass
AND
regression tests pass
AND
relevant backtests pass
AND
security tests pass
AND
frontend verification passes
AND
failure paths are tested
AND
documentation is updated
AND
observability exists
AND
no known P0/P1/P2 defect remains
AND
acceptance criteria pass
```

## 1.6 No silent failures

Never:

```python
except Exception:
    pass
```

Never convert a failed operation into a successful-looking response.

Every important operation needs:

```text
success
failure
timeout
retryable failure
non-retryable failure
```

states where applicable.

## 1.7 Never trust client-controlled identity

Never trust browser-provided:

```text
student_id
teacher_id
admin_id
organization_id
course_id
class_id
session_id
```

without server-side authorization.

## 1.8 Central data must become authoritative

Once the platform migration is complete:

```text
PostgreSQL = authoritative platform state
```

Local SQLite may remain only where explicitly required for offline/local functionality.

Do not maintain two competing authoritative databases.

## 1.9 Do not fabricate progress

Every progress entry must contain evidence:

```text
commit
tests
backtest
security result
frontend verification
known issues
```

---

# 2. TARGET PRODUCT

The completed product has three connected experiences.

## Student

The student can:

```text
sign in
view courses
study curriculum
ask Gayatri questions
receive adaptive teaching
use hints
practice
take assessments
receive remediation
review weak areas
see progress
see recent sessions
see recommendations
complete revision
use exam mode
work offline where supported
sync learning events
```

## Teacher

The teacher can:

```text
sign in
see assigned students
see classes/cohorts
see student progress
see mastery
see weak concepts
see misconceptions
see recent sessions
see learning timeline
write student-specific AI instructions
create assignments
review assessment results
raise interventions
track intervention resolution
use Teacher Copilot
receive alerts
```

## Admin

The admin can:

```text
manage organizations
manage users
manage teachers
manage students
manage courses
manage curricula
manage versions
manage classes
manage enrollments
manage providers
manage models
manage AI policies
manage feature flags
manage system configuration
view audit logs
view platform analytics
control AI kill switches
```

---

# 3. TARGET ARCHITECTURE

The final architecture should be approximately:

```text
                         ┌─────────────────────┐
                         │      ADMIN WEB      │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │    PLATFORM API     │
                         │ Auth / RBAC / Audit │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
     ┌───────▼────────┐    ┌────────▼────────┐    ┌──────▼───────┐
     │  PostgreSQL    │    │ Learning Engine │    │ AI Gateway   │
     │ Authoritative  │    │ SLR / Events    │    │ Model Router │
     └────────────────┘    └────────┬────────┘    └──────┬───────┘
                                    │                    │
                              ┌─────▼─────┐        ┌────▼─────────┐
                              │ RAG / KG  │        │ Providers    │
                              │ Curriculum│        │ OpenAI       │
                              │ Assessment│        │ Anthropic    │
                              └───────────┘        │ Gemini       │
                                                   │ OpenRouter   │
                                                   │ Local        │
                                                   └──────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │    STUDENT CORE     │
                         │ Desktop / Web       │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │    TEACHER WEB      │
                         └─────────────────────┘
```

---

# 4. AUTHORITATIVE PROJECT DOCUMENTATION

Create and maintain:

```text
docs/
├── implementation/
│   ├── V2_PLATFORM_MASTER_PLAN.md
│   ├── V2_PLATFORM_PROGRESS.md
│   ├── DEBUGGING_REGISTER.md
│   ├── REGRESSION_REGISTER.md
│   └── DECISION_LOG.md
│
├── architecture/
│   ├── current-state.md
│   ├── target-architecture.md
│   ├── data-model.md
│   ├── api-contract.md
│   ├── event-model.md
│   ├── auth-rbac.md
│   ├── ai-architecture.md
│   └── sync-architecture.md
│
├── evaluation/
│   ├── baseline/
│   ├── phase-01/
│   ├── phase-02/
│   └── ...
│
├── security/
├── rag/
├── curriculum/
└── product/
```

The files above become the source of truth.

Stale documents must be marked as historical or replaced.

---

# 5. REQUIRED TRACKING SYSTEM

Create:

```text
docs/implementation/V2_PLATFORM_PROGRESS.md
```

Use this exact structure.

```markdown
# V2 Platform Progress

## Overall

Status:
Current Phase:
Overall Completion:
Last Verified Commit:
Last Full Regression:
Last Full Backtest:
Open P0:
Open P1:
Open P2:
Open P3:

## Phase Matrix

| Phase | Status | Unit | Integration | Regression | Backtest | Security | Frontend | Docs | Debug | Commit |
|---|---|---|---|---|---|---|---|---|---|---|
| 00 | NOT_STARTED | - | - | - | - | - | - | - | - | - |
...
| 24 | NOT_STARTED | - | - | - | - | - | - | - | - | - |

## Current Phase

### Objective

### Implemented

### Files Changed

### Tests Added

### Tests Passed

### Backtests

### Security

### Frontend

### Bugs Found

### Bugs Fixed

### Known Issues

### Remaining Work

### Commit

### Verification Evidence
```

Allowed statuses:

```text
NOT_STARTED
IN_PROGRESS
IMPLEMENTED
TESTING
DEBUGGING
BACKTESTING
BLOCKED
REGRESSION_FAILED
ROLLED_BACK
VERIFIED
```

---

# 6. DEFECT / DEBUGGING SYSTEM

Create:

```text
docs/implementation/DEBUGGING_REGISTER.md
```

Every defect must receive an ID.

Format:

```text
BUG-0001
BUG-0002
...
```

Each record:

```markdown
## BUG-0001

Severity: P1
Phase:
Component:
Detected:
Environment:
Commit:

### Reproduction

### Expected

### Actual

### Root Cause

### Fix

### Regression Test

### Verification

### Status
OPEN / FIXED / VERIFIED / WONT_FIX
```

Severity:

```text
P0 = production/data/security catastrophe
P1 = major functionality broken
P2 = important defect with workaround
P3 = minor defect/cosmetic
```

No phase can become `VERIFIED` while unresolved P0/P1 defects exist.

P2 defects require explicit disposition.

---

# 7. REGRESSION SYSTEM

Create:

```text
docs/implementation/REGRESSION_REGISTER.md
```

Maintain three classes:

```text
CORE_REGRESSION
PLATFORM_REGRESSION
INTELLIGENCE_REGRESSION
```

Every phase must run:

```text
existing tests
+
new phase tests
+
previous phase tests
+
critical user journeys
```

A failure must block the next phase until resolved or explicitly approved as a known non-blocking issue.

---

# 8. REQUIRED LOCAL COMMANDS

The agent must establish and document exact commands for:

```bash
install
lint
format-check
type-check
unit-tests
integration-tests
frontend-tests
backend-tests
security-tests
rag-tests
learning-tests
e2e-tests
build
start-backend
start-frontend
full-test
full-regression
full-backtest
```

If the project uses different tooling, preserve the conceptual commands with repository-appropriate implementations.

---

# 9. PHASE 00 — TRUTH RESET / REPOSITORY RECONCILIATION

## Objective

Stop the current documentation/status drift.

## Tasks

1. Inventory every directory.
2. Inventory every backend entry point.
3. Inventory every frontend entry point.
4. Inventory every database.
5. Inventory every service.
6. Inventory all tests.
7. Identify duplicate implementations.
8. Identify legacy modules.
9. Identify active modules.
10. Identify unused modules.
11. Identify all current APIs.
12. Identify current persistence.
13. Identify all external integrations.
14. Identify all configuration/environment requirements.

Create:

```text
docs/architecture/current-state.md
```

## Required classification

Every important module must be marked:

```text
ACTIVE
LEGACY
DUPLICATE
PROTOTYPE
INTEGRATION_PENDING
UNUSED
UNKNOWN
```

## Required output

Create a gap matrix:

| Capability | Existing Location | Actual State | Target | Gap |
|---|---|---|---|---|

## Debugging

Run the complete existing suite before changes.

Record:

```text
startup failures
test failures
lint failures
type failures
frontend build failures
security failures
known runtime errors
```

## Gate

Do not proceed until the repository baseline is reproducible.

---

# 10. PHASE 01 — STABILIZE THE CORE TUTOR

## Objective

Protect existing working functionality.

Do NOT redesign the tutor.

Verify:

```text
student session
question answering
answer evaluation
adaptive learning
mastery
misconceptions
spaced review
RAG
chemistry tools
local inference
provider abstraction
session recovery
security
```

## Tests

Create a frozen baseline.

## Backtest

Freeze:

```text
chemistry benchmark
RAG benchmark
adaptive benchmark
misconception benchmark
```

These benchmarks must not be modified merely to improve scores.

## Gate

Existing functionality must have a reproducible baseline before platform migration continues.

---

# 11. PHASE 02 — REAL PLATFORM API

## Objective

Replace the current API placeholder with a real service layer.

Implement:

```text
FastAPI or existing approved framework
versioned routes
request validation
response schemas
structured errors
health
readiness
liveness
request IDs
logging
authentication middleware
authorization middleware
```

Suggested API groups:

```text
/api/v1/auth
/api/v1/users
/api/v1/students
/api/v1/teachers
/api/v1/admin
/api/v1/courses
/api/v1/curricula
/api/v1/enrollments
/api/v1/sessions
/api/v1/learning
/api/v1/assessments
/api/v1/rag
/api/v1/ai
/api/v1/analytics
/api/v1/notifications
/api/v1/sync
```

## Tests

Test every endpoint for:

```text
valid request
invalid request
missing auth
wrong role
wrong resource owner
not found
duplicate request
server failure
timeout
```

## Gate

No frontend may depend on direct database access.

---

# 12. PHASE 03 — POSTGRESQL CENTRAL DATA LAYER

## Objective

Make PostgreSQL the authoritative platform database.

Implement migrations.

Required entities include at minimum:

```text
organizations
users
roles
permissions
courses
curricula
curriculum_versions
subjects
modules
topics
concepts
prerequisites
classes
cohorts
enrollments
sessions
learning_events
student_learning_records
mastery_states
misconceptions
assessments
assessment_items
assessment_attempts
teacher_instructions
interventions
assignments
notifications
ai_providers
ai_models
ai_execution_logs
audit_logs
```

## Rules

Use:

```text
foreign keys
indexes
unique constraints
timestamps
soft deletion where required
created_by
updated_by
organization scoping
```

## Migration

Never silently delete existing data.

Create:

```text
migration
backup
rollback
verification
```

## Gate

All authoritative platform state must be persisted centrally.

---

# 13. PHASE 04 — AUTHENTICATION + RBAC

## Objective

Implement production-grade authentication and authorization.

Roles:

```text
SUPER_ADMIN
ORG_ADMIN
COURSE_ADMIN
TEACHER
STUDENT
```

Implement:

```text
login
logout
password hashing
session/token management
refresh/expiry
account state
password reset
role assignment
organization scope
resource scope
```

Authorization must enforce:

```text
role
+
permission
+
organization
+
course/class/student resource scope
```

## Security tests

Attempt:

```text
student → another student
student → teacher
teacher → unrelated student
teacher → admin
org admin → another organization
modified student_id
modified session_id
modified organization_id
```

All must fail.

---

# 14. PHASE 05 — CENTRAL LEARNING EVENT SYSTEM

## Objective

Create the authoritative learning-event pipeline.

Events:

```text
session_started
session_completed
question_attempted
answer_submitted
answer_corrected
hint_requested
hint_used
concept_introduced
concept_reinforced
concept_mastered
misconception_detected
misconception_recovered
review_completed
assessment_started
assessment_completed
teacher_instruction_created
teacher_intervention_created
teacher_feedback_added
assignment_created
assignment_completed
```

Each event must contain:

```text
event_id
student_id
organization_id
course_id
session_id
event_type
timestamp
source
payload
schema_version
```

## Rules

Events must be:

```text
immutable
idempotent
auditable
student-scoped
replayable
```

---

# 15. PHASE 06 — AUTHORITATIVE STUDENT LEARNING RECORD

## Objective

Build the real SLR from central events.

SLR must expose:

```text
identity
enrollment
course
curriculum
mastery
recent sessions
learning timeline
misconceptions
assessment results
hints
teacher feedback
teacher instructions
interventions
recommendations
alerts
```

Do not allow separate portals to invent independent versions of student state.

The SLR becomes the canonical student learning view.

---

# 16. PHASE 07 — CONNECT EXISTING LEARNING ENGINE

## Objective

Connect the existing working learning intelligence to the central event/SLR architecture.

Preserve:

```text
BKT
mastery
LDG
difficulty
misconceptions
spaced review
concept selection
adaptive engine
```

Refactor only where necessary.

Target flow:

```text
student action
→ learning event
→ learning engine
→ updated mastery
→ SLR
→ recommendation
```

## Backtest

Replay frozen student histories.

Expected output must remain within agreed tolerance versus the pre-migration baseline.

---

# 17. PHASE 08 — REAL DESKTOP ↔ PLATFORM SYNC

## Objective

Replace in-memory synchronization with real network synchronization.

Architecture:

```text
Desktop
 ↓
local event queue
 ↓
authenticated sync API
 ↓
server validation
 ↓
idempotency
 ↓
PostgreSQL
 ↓
SLR update
```

Support:

```text
offline
online
retry
duplicate event
out-of-order event
partial upload
network timeout
token expiry
conflict
reconciliation
```

## Tests

Simulate:

```text
0 network
slow network
duplicate request
same event twice
events out of order
server restart
client restart
```

No learning event may silently disappear.

---

# 18. PHASE 09 — STUDENT PROGRESS API + UI

## Objective

Expose learning progress from authoritative SLR data.

Student must see:

```text
overall mastery
topic mastery
concept heatmap
recent sessions
recent activity
weak areas
misconceptions
accuracy trends
mastery trends
question-type performance
review due
recommendations
session summary
learning streak
```

Recommendations must be generated by the learning policy, not free-form LLM text.

## UI states

Every screen must handle:

```text
loading
empty
success
partial data
offline
API error
permission error
retry
```

---

# 19. PHASE 10 — TEACHER WEB PORTAL

## Objective

Build the actual browser teacher application.

Minimum pages:

```text
/login
/dashboard
/students
/students/:id
/students/:id/timeline
/students/:id/mastery
/students/:id/misconceptions
/students/:id/sessions
/students/:id/interventions
/students/:id/instructions
/assignments
/assessments
/copilot
/alerts
/settings
```

Teacher dashboard:

```text
students active
average mastery
difficult concepts
common misconceptions
recent activity
intervention alerts
```

Student view:

```text
mastery
learning timeline
sessions
misconceptions
recommendations
assessment results
teacher instructions
interventions
```

All data must come from API/SLR.

No mock data in production screens.

---

# 20. PHASE 11 — TEACHER AI INSTRUCTIONS

## Objective

Allow teachers to influence tutoring for specific students safely.

Example:

```text
"Use more examples for this student."
"Focus on numerical problems."
"Do not advance until stoichiometry is stable."
"Use simpler explanations."
```

Implement:

```text
teacher instruction
scope
priority
start
expiry
status
audit trail
```

Flow:

```text
Teacher instruction
→ policy validation
→ student context
→ AI context builder
→ tutor
```

Teacher instructions must NOT override:

```text
security
safety
system policy
authorization
deterministic calculations
```

---

# 21. PHASE 12 — TEACHER INTERVENTION SYSTEM

Implement:

```text
intervention
reason
priority
assigned teacher
student
created_at
due_at
status
resolution
teacher notes
```

Statuses:

```text
OPEN
ACKNOWLEDGED
IN_PROGRESS
RESOLVED
DISMISSED
```

Trigger examples:

```text
persistent misconception
declining performance
long inactivity
repeated failed assessment
low prerequisite mastery
teacher-created intervention
```

No automatic intervention should be generated without an auditable reason.

---

# 22. PHASE 13 — TEACHER COPILOT

## Objective

Turn the existing prototype into a real retrieval-backed assistant.

The Copilot may answer:

```text
Why is this student struggling?
What concepts are weak?
What changed recently?
Which students need intervention?
What should I assign?
Summarize this student's last week.
```

Every student-specific statement must be traceable to authorized data.

Output:

```text
answer
evidence
source records
confidence
recommended action
```

Never fabricate student performance.

Never expose unauthorized students.

---

# 23. PHASE 14 — ADMIN WEB PORTAL

## Objective

Build the actual browser admin application.

Pages:

```text
/dashboard
/organizations
/users
/teachers
/students
/courses
/curricula
/classes
/cohorts
/enrollments
/providers
/models
/ai-policies
/audit
/analytics
/system
```

Admin controls:

```text
create/update users
roles
organizations
courses
curricula
versions
classes
enrollments
AI providers
AI models
feature flags
kill switches
```

---

# 24. PHASE 15 — PLUG-AND-PLAY CURRICULUM

## Objective

Make courses/curricula replaceable without rewriting the tutor.

Target:

```text
Course
 ↓
Curriculum Version
 ↓
Subject
 ↓
Module
 ↓
Topic
 ↓
Concept
 ↓
Prerequisites
 ↓
Activities
 ↓
Assessments
```

Every curriculum must be:

```text
versioned
validated
published
immutable after publication
```

Support import/export through a documented schema.

The tutor engine must consume curriculum abstractions, not chemistry-specific hardcoded assumptions.

---

# 25. PHASE 16 — RAG PLUG-AND-PLAY

## Objective

Allow administrators to attach knowledge sources to courses/curricula.

Pipeline:

```text
upload
→ parse
→ clean
→ chunk
→ metadata
→ embed
→ index
→ validate
→ publish
```

Support:

```text
PDF
DOCX
HTML
Markdown
text
structured JSON
```

Metadata:

```text
course
subject
topic
concept
chapter
difficulty
source
authority
version
page
```

Security:

Retrieved documents are DATA, never instructions.

---

# 26. PHASE 17 — REAL AI GATEWAY + MODEL ROUTER

## Objective

Create one provider-neutral AI execution layer.

Architecture:

```text
Tutor / Copilot
      ↓
AI Gateway
      ↓
Context Builder
      ↓
Policy Engine
      ↓
Model Router
      ↓
Provider Adapter
      ↓
Model
```

Support configurable providers such as:

```text
OpenAI
Anthropic
Google Gemini
OpenRouter
local models
future providers
```

Provider configuration must include:

```text
name
API key reference
base URL
models
capabilities
context limit
cost
latency
enabled
priority
fallback
```

Never store raw secrets in source control.

---

# 27. PHASE 18 — AI GOVERNANCE / OBSERVABILITY

Track:

```text
provider
model
request_id
student/session scope
task type
input token count
output token count
latency
success/failure
error class
estimated cost
fallback
```

Avoid storing sensitive raw prompts unnecessarily.

Implement:

```text
model allowlist
provider kill switch
global AI kill switch
rate limits
budget limits
fallback policy
timeout
circuit breaker
```

---

# 28. PHASE 19 — ASSESSMENT PLATFORM

Implement:

```text
question bank
diagnostic assessment
formative assessment
summative assessment
adaptive assessment
assignments
attempts
grading
rubrics
teacher review
AI-assisted grading
reassessment
```

Every assessment event must feed the learning engine.

---

# 29. PHASE 20 — ANALYTICS

Analytics must be derived from authoritative learning events.

Student:

```text
mastery
accuracy
retention
session frequency
learning velocity
weak concepts
review compliance
```

Teacher:

```text
class mastery
student activity
difficult concepts
misconceptions
intervention rates
assessment outcomes
```

Admin:

```text
active users
course usage
AI usage
cost
performance
system health
```

Never use fake formulas merely to populate dashboards.

---

# 30. PHASE 21 — NOTIFICATIONS

Implement real delivery abstraction.

Channels:

```text
in-app
email
push
WhatsApp where configured
```

Use a queue where appropriate.

Track:

```text
created
queued
sent
delivered
failed
retried
```

Use exponential backoff for transient errors.

Never report a notification as sent before provider confirmation where confirmation is available.

---

# 31. PHASE 22 — SECURITY HARDENING

Perform a complete security pass.

Test:

```text
authentication bypass
RBAC bypass
IDOR
student data leakage
organization leakage
session hijacking
token replay
prompt injection
RAG injection
system prompt extraction
tool abuse
malicious curriculum
malicious uploaded document
unsafe chemistry requests
secret leakage
SQL injection
XSS
CSRF where applicable
rate-limit bypass
file upload abuse
path traversal
```

Create:

```text
docs/security/security-regression.md
```

Every discovered vulnerability becomes a tracked bug.

---

# 32. PHASE 23 — REAL END-TO-END TESTING

This phase MUST use actual application boundaries.

Do NOT count direct Python service calls as E2E.

Required flow:

```text
Browser/Desktop
→ authentication
→ HTTP API
→ authorization
→ PostgreSQL
→ learning engine
→ AI/RAG where applicable
→ response
→ UI
```

### Student journey

```text
login
→ enroll
→ open course
→ start session
→ ask question
→ answer question
→ use hint
→ misconception
→ remediation
→ session completion
→ progress update
```

### Teacher journey

```text
login
→ view student
→ inspect timeline
→ inspect mastery
→ add instruction
→ create assignment
→ create intervention
→ use Copilot
```

### Admin journey

```text
login
→ create organization
→ create teacher
→ create student
→ create course
→ publish curriculum
→ configure provider
→ configure model
→ inspect analytics
→ inspect audit log
```

---

# 33. PHASE 24 — FAILURE / RECOVERY TESTING

Every critical component must be tested under failure.

Simulate:

```text
database unavailable
database timeout
Redis unavailable
AI provider unavailable
RAG unavailable
model timeout
invalid model response
malformed JSON
network interruption
expired auth token
frontend refresh
desktop crash
server restart
duplicate request
duplicate event
partial sync
notification failure
file parsing failure
```

Expected behavior must be explicit.

The UI must never show successful completion when the operation failed.

---

# 34. PHASE 25 — PERFORMANCE / SCALE TESTING

Measure:

```text
API latency
database latency
RAG latency
LLM latency
total tutoring latency
concurrent students
concurrent teachers
concurrent admins
event ingestion throughput
sync throughput
AI throughput
memory
CPU
database connections
```

Test realistic load.

Identify:

```text
bottleneck
saturation point
failure point
recovery behavior
```

Do not optimize prematurely.

---

# 35. PHASE 26 — DATA MIGRATION / BACKUP / RESTORE

Implement:

```text
backup
restore
migration
rollback
data integrity verification
```

Test:

```text
backup created
database destroyed
database restored
application reconnects
SLR integrity preserved
learning events preserved
```

Document exact recovery commands.

---

# 36. PHASE 27 — PRODUCTION OPERATIONS

Create:

```text
deployment guide
environment variables
secret management
logging
monitoring
health checks
alerts
backup schedule
restore procedure
rollback procedure
incident response
```

Production readiness must include:

```text
HTTPS
secure cookies/tokens
database backups
log rotation
error monitoring
health endpoints
resource monitoring
AI cost monitoring
```

---

# 37. PHASE 28 — FINAL CLEANUP

Only after functionality is verified:

Remove:

```text
dead code
unused imports
temporary files
debug prints
fake data
simulation-only code
obsolete documentation
duplicate implementations
legacy routes
unused feature flags
```

Do NOT remove anything without checking references.

Every deletion must be validated by tests.

---

# 38. PHASE 29 — FINAL AUDIT

Perform six audits.

## Architecture audit

Check:

```text
dependencies
boundaries
coupling
duplicate state
duplicate logic
```

## Data audit

Check:

```text
authoritative DB
event integrity
SLR integrity
migration integrity
```

## Security audit

Check all security requirements.

## Intelligence audit

Check:

```text
adaptive learning
RAG
misconceptions
recommendations
teacher instructions
AI grounding
```

## UX audit

Check:

```text
student
teacher
admin
loading
empty
error
offline
mobile/browser where applicable
```

## Operations audit

Check:

```text
deployment
monitoring
backup
restore
rollback
```

---

# 39. FINAL BENCHMARK SUITE

Create a frozen benchmark.

Minimum:

```text
100 concept questions
100 why questions
100 numerical questions
100 MCQs
100 misconception cases
100 hint cases
100 remediation cases
100 follow-up cases
100 RAG grounding cases
100 prompt injection cases
100 out-of-scope cases
100 transfer cases
```

Minimum total:

```text
1,200 cases
```

Track:

```text
chemistry correctness
intent accuracy
retrieval Recall@k
retrieval Precision@k
grounding
misconception diagnosis
adaptive decision accuracy
structured output validity
latency
failure rate
security block rate
```

Never alter benchmark cases to improve reported results.

---

# 40. CONTINUOUS REGRESSION RULE

After every meaningful implementation batch:

```text
git diff
↓
inspect changed files
↓
targeted tests
↓
phase tests
↓
full regression
↓
backtest
↓
security regression
↓
frontend verification
↓
debug failures
↓
update docs
↓
update tracker
↓
commit
```

For intelligence changes:

```text
baseline benchmark
vs
current benchmark
```

must be compared.

A regression must be investigated.

---

# 41. REQUIRED DEBUGGING LOOP

When a test fails:

```text
1. Reproduce
2. Capture logs
3. Isolate component
4. Identify root cause
5. Fix smallest responsible layer
6. Add regression test
7. Re-run targeted test
8. Re-run phase suite
9. Re-run full regression
10. Update BUG record
11. Commit fix
```

Never:

```text
delete test
weaken assertion
hide exception
increase timeout without understanding cause
mark failure as expected
```

unless explicitly documented and justified.

---

# 42. REQUIRED OBSERVABILITY

Every major subsystem must expose enough information to debug it.

Minimum:

```text
request ID
session ID
student ID where authorized
service name
operation
duration
status
error category
```

For AI:

```text
provider
model
task
latency
token counts
fallback
failure
cost estimate
```

Never log:

```text
API keys
passwords
session secrets
sensitive raw student data unnecessarily
full private prompts unnecessarily
```

---

# 43. DEFINITION OF DONE

A phase is `VERIFIED` only if all applicable items pass.

```text
[ ] implementation
[ ] unit tests
[ ] integration tests
[ ] regression tests
[ ] backtest
[ ] security tests
[ ] frontend verification
[ ] error-path testing
[ ] performance check
[ ] observability
[ ] documentation
[ ] progress tracker
[ ] debugging register
[ ] no unresolved P0/P1
[ ] P2 disposition documented
[ ] commit created
```

---

# 44. FINAL PRODUCT ACCEPTANCE

The product is NOT considered complete until all are true.

## Student

```text
[ ] authentication
[ ] course access
[ ] tutoring
[ ] adaptive learning
[ ] hints
[ ] misconception handling
[ ] assessments
[ ] progress dashboard
[ ] session history
[ ] recommendations
[ ] revision
[ ] exam mode
[ ] offline/sync where supported
```

## Teacher

```text
[ ] authentication
[ ] student list
[ ] student progress
[ ] mastery
[ ] timeline
[ ] misconceptions
[ ] sessions
[ ] teacher instructions
[ ] assignments
[ ] assessments
[ ] interventions
[ ] Copilot
[ ] alerts
```

## Admin

```text
[ ] authentication
[ ] organizations
[ ] users
[ ] roles
[ ] courses
[ ] curricula
[ ] classes
[ ] enrollments
[ ] providers
[ ] models
[ ] AI policies
[ ] analytics
[ ] audit
[ ] system controls
```

## Platform

```text
[ ] real API
[ ] PostgreSQL
[ ] authoritative SLR
[ ] learning events
[ ] RBAC
[ ] sync
[ ] RAG
[ ] curriculum
[ ] assessment
[ ] AI gateway
[ ] model router
[ ] analytics
[ ] notifications
[ ] security
[ ] monitoring
[ ] backups
[ ] restore
```

---

# 45. FINAL “NOTHING REMAINING” CHECK

Before declaring production-ready, the agent MUST generate:

```text
FINAL_READINESS_REPORT.md
```

It must include:

```text
1. Repository state
2. Architecture
3. Database state
4. API state
5. Student state
6. Teacher state
7. Admin state
8. AI state
9. RAG state
10. Security state
11. Test results
12. Backtest results
13. Performance results
14. E2E results
15. Open bugs
16. Known limitations
17. Deployment status
18. Backup/restore verification
19. Final commit
```

The report must explicitly state:

```text
P0 open: 0
P1 open: 0
P2 open: 0 OR explicitly accepted
critical test failures: 0
critical regression failures: 0
security blockers: 0
missing acceptance criteria: 0
```

If any of these are not true:

```text
DO NOT DECLARE COMPLETE.
```

---

# 46. AGENT EXECUTION CHECKLIST

For every phase:

```text
[ ] Read this phase completely
[ ] Inspect relevant existing code
[ ] Inspect dependencies
[ ] Inspect tests
[ ] Establish baseline
[ ] Implement
[ ] Run targeted tests
[ ] Debug
[ ] Add regression tests
[ ] Run integration tests
[ ] Run full regression
[ ] Run backtest
[ ] Run security tests
[ ] Verify frontend
[ ] Verify failure states
[ ] Update architecture docs
[ ] Update progress
[ ] Update debugging register
[ ] Update regression register
[ ] Commit
[ ] Verify clean working tree
[ ] Only then continue
```

---

# 47. COMMIT STRATEGY

Use small logical commits.

Examples:

```text
phase-00: reconcile repository architecture
phase-01: freeze tutor baseline
phase-02: implement platform api
phase-03: add postgres schema
phase-04: implement auth and rbac
phase-05: implement learning event pipeline
phase-06: implement authoritative slr
phase-07: connect adaptive learning engine
phase-08: implement real sync
phase-09: implement student progress
phase-10: implement teacher portal
phase-11: implement teacher ai instructions
phase-12: implement intervention workflow
phase-13: implement teacher copilot
phase-14: implement admin portal
phase-15: implement plug-and-play curriculum
phase-16: implement plug-and-play rag
phase-17: implement ai gateway
phase-18: implement ai governance
phase-19: implement assessment platform
phase-20: implement analytics
phase-21: implement notifications
phase-22: security hardening
phase-23: end-to-end testing
phase-24: failure recovery
phase-25: performance testing
phase-26: migration backup restore
phase-27: production operations
phase-28: cleanup
phase-29: final audit
```

---

# 48. IMPORTANT ANTI-PATTERNS

The agent MUST NOT:

```text
rewrite the whole project
replace working tutor code without evidence
declare services complete because classes exist
declare E2E complete because Python classes were called directly
use mock data in production UI
create duplicate sources of truth
use SQLite as central production state
trust frontend authorization
store secrets in source
silently catch exceptions
delete failing tests
change benchmark cases to improve scores
skip backtesting
skip regression
skip security tests
skip frontend verification
declare completion with known P0/P1 defects
```

---

# 49. FINAL ARCHITECTURAL PRINCIPLE

The platform must preserve this division of responsibility:

```text
APPLICATION
owns:
identity
authorization
student state
mastery
progression
learning events
retrieval policy
safety
security
assessment state
analytics
system configuration


RAG
supplies:
authoritative evidence


DETERMINISTIC TOOLS
handle:
calculations
units
formula processing
chemistry-specific deterministic operations


SLM / LLM
handles:
explanation
questioning
hints
language adaptation
examples
structured response generation


LEARNING ENGINE
decides:
what the student needs
what should happen next
difficulty
remediation
review
progression


TEACHER
controls:
student-specific instructional context
assignments
interventions
feedback


ADMIN
controls:
platform configuration
organizations
users
curricula
providers
models
governance
```

The SLM is not the system brain.

The platform owns learning state.

The central event system owns evidence of learning.

The SLR is the canonical student learning view.

The AI Gateway owns model execution.

The Teacher Portal consumes authorized learning data.

The Admin Portal controls platform configuration.

---

# 50. FINAL SUCCESS CONDITION

Gayatri is complete only when this entire loop works through real application boundaries:

```text
                 STUDENT
                    │
                    ▼
              STUDENT UI
                    │
                    ▼
              PLATFORM API
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       AUTH/RBAC          LEARNING EVENT
                              │
                              ▼
                             SLR
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
             MASTERY       RAG       ASSESSMENT
                  │           │           │
                  └───────────┼───────────┘
                              ▼
                       LEARNING POLICY
                              │
                              ▼
                         AI GATEWAY
                              │
                       MODEL ROUTER
                              │
                         PROVIDER
                              │
                              ▼
                           GAYATRI
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
              STUDENT                 TEACHER
                  │                       │
                  │                 instructions
                  │                 interventions
                  │                 assignments
                  │                       │
                  └───────────┬───────────┘
                              ▼
                            SLR
                              │
                              ▼
                            ADMIN
```

The final objective is not merely:

> “all tests pass.”

The objective is:

> **Every major product capability works through the actual production architecture, is observable, secure, recoverable, regression-tested, backtested, documented, and independently verifiable.**

When the agent reaches the end, there must be no undocumented half-built service, fake integration, mock production path, unresolved critical defect, competing source of truth, or unverified product claim remaining.
