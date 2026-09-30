# GAYATRI — PRODUCTION DEVELOPMENT MASTER PLAN

## AI-Agent Execution Specification

**Repository:** `https://github.com/Gayatri-Education/Gayatri`

**Objective:** Transform Gayatri into a production-grade AI-powered learning operating system for schools, colleges, coaching institutes, teachers, students, and parents.

---

# 0. NON-NEGOTIABLE EXECUTION CONTRACT

This document is an execution contract for an AI coding agent.

The agent MUST work in small, independently verifiable phases.

For EVERY phase:

1. Read current GitHub state.
2. Read current local project state.
3. Read previous phase status.
4. Define the phase objective.
5. Inspect relevant files.
6. Map impact across the entire repository.
7. Identify files to create, modify, deprecate, or remove.
8. Identify database, API, UI, AI, security, configuration, and test impact.
9. Write the phase implementation plan.
10. Implement the smallest coherent change set.
11. Run unit tests.
12. Run integration tests.
13. Run regression tests.
14. Run static, security, and quality checks.
15. Debug every newly introduced failure.
16. Re-check repository health.
17. Update tracking, README, CHANGELOG, and state documents.
18. Commit.
19. Push to GitHub.
20. Verify the remote commit.
21. Mark the phase complete only with evidence.
22. Move to the next phase.

Never skip directly from planning to coding.

Never mark a phase complete merely because code was written.

---

# 1. PRODUCT VISION

Gayatri is not merely an AI chatbot.

> **Gayatri is an AI-powered learning operating system that understands what a learner is studying, what they understand, where they are struggling, what happened previously, and what they should do next.**

Four experiences:

- **Student:** Help me learn.
- **Teacher:** Help me teach better.
- **Parent:** Help me understand and support my child.
- **Admin:** Help me operate and improve the institution.

Core principle:

> **The application understands the state. The SLM understands the language. Together they decide what should happen next.**

The application owns deterministic educational state. The language model provides language intelligence, explanation, questioning, interpretation, summarization, and conversational reasoning.

---

# 2. ORGANIZATIONAL MODEL

Support:

```text
Institution
├── Campus
├── Academic Year
├── Curriculum
├── Classes / Courses
├── Sections
├── Teachers
├── Students
├── Parents / Guardians
├── Assessments
├── Fees
└── Institutional Policies
```

A person can belong to multiple institutions.

Example:

```text
Student: Abhinav
├── School A
│   └── Class 11
└── Coaching Institute B
    └── Chemistry
```

The student has one persistent learner identity, while institutional memberships and institutional academic contexts are scoped separately.

---

# 3. CURRICULUM

Support:

- NCERT
- CBSE
- ICSE
- State Boards
- College curriculum
- Custom institutional curriculum

Curriculum must be modular:

```text
Curriculum
└── Subject
    └── Chapter
        └── Topic
            └── Concept
                ├── Prerequisites
                ├── Learning Objectives
                ├── Content
                ├── Assessments
                └── Mastery Rules
```

Institutions must eventually be able to add curriculum/content without modifying core tutor code.

---

# 4. FOUR PORTALS

## 4.1 Student Portal

Primary question:

> What should I do next?

Required capabilities:

- AI Tutor
- course navigation
- curriculum
- learning graph
- mastery
- strengths
- weak concepts
- misconceptions
- practice
- assessments
- review queue
- learning history
- attendance where applicable
- assignments
- teacher instructions where permitted
- recommendations
- profile/settings
- notifications
- English/Hindi

## 4.2 Teacher Portal

Primary question:

> Which students need my attention and what should I do?

Required capabilities:

- class/section overview
- student list
- learning graph
- mastery
- misconceptions
- recent attempts
- assessment performance
- intervention history
- attendance
- assignments
- teacher instructions
- AI Copilot
- assign concepts
- set learning objectives
- request remediation
- influence next action
- evidence-backed recommendations
- English/Hindi

Teacher instructions must be structured:

```text
Teacher Instruction
├── Target: Student / Class / Section / Cohort
├── Objective
├── Concept
├── Priority
├── Instruction
├── Start Date
├── End Date
└── Status
```

## 4.3 Parent Portal

Primary question:

> How is my child doing and how can I support them?

Required:

- child selector
- academic progress
- subject progress
- learning trends
- attendance
- assignments
- upcoming assessments
- achievements
- areas needing attention
- recommended home support
- institution announcements
- fee status
- invoices
- receipts
- payment history
- outstanding fees
- due dates
- notifications

Parents must not automatically receive private student-AI conversations. Visibility is controlled by institution policy.

## 4.4 Admin Portal

Primary question:

> How is the institution operating and how healthy is learning?

Required:

- institution management
- campuses
- academic years
- classes
- sections
- teachers
- students
- parents
- enrollments
- curricula
- courses
- assessments
- learning analytics
- learning health
- AI configuration
- provider configuration
- privacy policies
- roles/permissions
- fee structures
- invoices
- payments
- reports
- audit logs
- system health

Admin is an operations/governance center, not a generic dashboard.

---

# 5. LEARNING GRAPH — CORE PRODUCT SYSTEM

Every student must have a persistent learning graph containing:

- profile
- institution memberships
- curriculum
- subject
- chapter
- topic
- concept
- prerequisites
- mastery
- confidence
- attempts
- questions
- answers
- hints
- misconceptions
- assessments
- review history
- teacher interventions
- learning objectives
- time spent
- learning velocity
- recommended next action

Meaningful interactions must generate learning events.

Recommended event types:

```text
SESSION_STARTED
SESSION_ENDED
QUESTION_ASKED
QUESTION_PRESENTED
ANSWER_SUBMITTED
ANSWER_EVALUATED
HINT_REQUESTED
HINT_GIVEN
MISCONCEPTION_DETECTED
REMEDIATION_STARTED
REMEDIATION_COMPLETED
CONCEPT_PRACTICED
CONCEPT_MASTERED
CONCEPT_REVIEW_DUE
CONCEPT_REVIEWED
ASSESSMENT_STARTED
ASSESSMENT_COMPLETED
ASSIGNMENT_CREATED
ASSIGNMENT_COMPLETED
TEACHER_INTERVENTION
TEACHER_INSTRUCTION_CREATED
TEACHER_INSTRUCTION_COMPLETED
COURSE_STARTED
COURSE_COMPLETED
```

The graph must be reconstructable from evidence. Never invent mastery without evidence.

---

# 6. CANONICAL LEARNING STATE

The existing repository contains overlapping state systems such as:

- SQLite mastery
- StudentProfile JSON
- events JSONL
- LDG mastery
- TutorContext
- TutorStateManager

The agent MUST inspect these and consolidate them.

Target:

```text
AUTHORITATIVE PERSISTENT STATE
├── Student
├── Institution Membership
├── Curriculum
├── Concept Mastery
├── Learning Events
├── Assessments
├── Interventions
└── Review Schedule
        ↓
SESSION RUNTIME STATE
└── TutorContext
```

There must be one authoritative source for persistent learning state.

---

# 7. INTELLIGENCE ARCHITECTURE

Target pipeline:

```text
USER QUERY
↓
QUERY UNDERSTANDING
↓
CONTEXT BUILDER
↓
LEARNING STATE
↓
PEDAGOGICAL POLICY
↓
RAG / KNOWLEDGE
↓
MODEL ROUTER
↓
LOCAL SLM
↓
RESPONSE VALIDATOR
↓
STATE COMMIT
↓
NEXT ACTION
```

Required conceptual modules:

```text
QueryUnderstanding
ContextBuilder
ResponsePlanner
NextActionEngine
ResponseValidator
StateCommitter
ModelRouter
```

Do not put all intelligence inside one oversized orchestrator.

---

# 8. QUERY UNDERSTANDING

Use structured interpretation, for example:

```json
{
  "intent": "clarification",
  "learning_intent": "remediation",
  "concept": "chem_thermo_work",
  "subconcept": "sign_convention",
  "difficulty": "foundation",
  "requires_evaluation": false,
  "requires_rag": true,
  "requires_calculation": false
}
```

The exact schema must be reconciled with existing contracts before implementation.

---

# 9. RESPONSE PLANNING

Example:

```json
{
  "mode": "REMEDIATE",
  "goal": "repair_sign_convention_misconception",
  "tone": "supportive",
  "depth": "foundation",
  "must_include": [
    "system vs surroundings",
    "direction of work"
  ],
  "must_avoid": [
    "final answer leakage"
  ],
  "must_end_with": "micro_question",
  "source_required": true
}
```

Supported pedagogical modes should include:

- Explain
- Ask
- Hint
- Remediate
- Challenge
- Review
- Evaluate
- Summarize
- Advance

The application selects the mode; the SLM expresses it naturally.

---

# 10. LOCAL-FIRST AI

The platform must work with a local model.

Cloud AI is optional.

Target:

```text
Deterministic Local Intelligence
↓
Local SLM
↓
Validation
↓
Optional Cloud Escalation
```

Institution-controlled modes:

```text
LOCAL_ONLY
LOCAL_FIRST
CLOUD_PREFERRED
```

Never silently send private institutional/student data to a cloud provider.

---

# 11. AUTHORITATIVE MODEL MANIFEST

The repository currently contains model/configuration inconsistencies. Resolve them.

Create one authoritative manifest defining:

```text
model_id
display_name
provider
local_path
download_source
quantization
context_length
architecture
parameter_count
chat_template
capabilities
hardware_requirements
language_support
version
checksum
license
```

All model-loading code must consume this manifest.

---

# 12. UI/UX DESIGN SYSTEM

The local agent will NOT receive a sample UI file.

Therefore this specification is the UI source of truth.

Product personality:

- premium
- academic
- calm
- intelligent
- precise
- trustworthy
- minimal
- modern

Avoid:

- excessive gradients
- neon colors
- generic SaaS-card clutter
- emoji navigation
- oversized headings
- unnecessary animation

---

# 13. DARK THEME TOKENS

```css
--bg: #0B0D10;
--surface: #111418;
--surface-raised: #171B21;
--surface-hover: #1C2128;

--border: #262C34;
--border-strong: #343B45;

--text: #F3F4F6;
--text-secondary: #A7AFBA;
--text-tertiary: #737C88;
--text-disabled: #505761;

--brand: #D6A85F;
--brand-hover: #E2B96D;
--brand-soft: rgba(214,168,95,.12);

--success: #4CAF7D;
--warning: #D9A441;
--error: #D76565;
--info: #6D9ED8;
```

# 14. LIGHT THEME TOKENS

```css
--bg: #F7F7F5;
--surface: #FFFFFF;
--surface-raised: #F1F2EF;
--surface-hover: #ECEDE9;

--border: #E2E4E0;
--border-strong: #D1D4CE;

--text: #17191C;
--text-secondary: #626A73;
--text-tertiary: #858C94;

--brand: #A87528;
--brand-hover: #8F631F;
--brand-soft: rgba(168,117,40,.10);
```

No component may hardcode colors when a semantic theme token exists.

---

# 15. TYPOGRAPHY

Preferred:

```text
UI: Inter or Manrope
Code/equations: JetBrains Mono or IBM Plex Mono
```

Hierarchy should use size, weight, line height, spacing, and contrast.

---

# 16. TUTOR UI

Target:

```text
┌──────────────┬───────────────────────────────┬─────────────┐
│ Sidebar      │ Conversation                 │ Learning    │
│              │                               │ Context     │
│ New Chat     │ User                         │ Topic       │
│ Search       │ Assistant                    │ Mastery     │
│ Chats        │ Response actions              │ Focus       │
│ Knowledge    │                               │ Sources     │
│ Progress     │ Composer                     │             │
│ Settings     │                               │             │
└──────────────┴───────────────────────────────┴─────────────┘
```

Desktop sidebar target: ~260px.

Right Learning Context is collapsible.

Tutor should feel like a premium AI workspace rather than a conventional LMS.

Response actions:

- Copy
- Explain simpler
- Give hint
- Practice
- Ask another question
- Show sources where appropriate

Hide provider/model/RAG chunks/telemetry from ordinary students. Authorized users may use a technical-details view.

Truthful AI status messages may include:

- Searching your course material…
- Checking your progress…
- Reviewing your recent attempts…
- Adapting this question…
- Preparing a practice question…

Never show fake progress.

---

# 17. SHARED UI COMPONENTS

Create or normalize a shared design system for:

```text
Theme
AppShell
Sidebar
Topbar
Button
IconButton
Input
Textarea
Select
Badge
Status
Tooltip
Dropdown
Modal
Drawer
Toast
Tabs
Card
Stat
Progress
Timeline
Table
EmptyState
ErrorState
Skeleton
ChatMessage
MessageActions
Citation
SourceCard
Composer
CommandPalette
```

Before creating a component, search for an existing equivalent.

---

# 18. RESPONSIVE DESIGN

Breakpoints:

```text
< 768px       Mobile
768–1199px    Tablet/small desktop
1200px+       Desktop
```

Mobile must be intentionally designed, not merely shrunk.

Required:

- collapsible navigation
- drawer-based context panels
- responsive tables
- full-width composer
- touch-friendly controls

---

# 19. ACCESSIBILITY

Target:

- keyboard navigation
- visible focus
- semantic HTML
- screen-reader labels
- sufficient contrast
- reduced motion
- accessible validation
- accessible dialogs
- accessible tables
- accessible status messages

---

# 20. FEE MANAGEMENT

Build a modular subsystem.

Core concepts:

```text
FeeStructure
FeePlan
FeeAccount
Invoice
Payment
Receipt
Discount
Refund
DueDate
PaymentStatus
```

Statuses:

```text
DRAFT
ISSUED
PARTIALLY_PAID
PAID
OVERDUE
CANCELLED
REFUNDED
```

Support:

- monthly fees
- quarterly fees
- annual fees
- custom schedules
- discounts
- configurable late fees
- online payments
- admin-recorded payments
- receipts
- reports

Payment providers must be abstracted.

Never store raw card data.

---

# 21. ENGLISH + HINDI

Internationalization must be architectural.

Use translation keys such as:

```text
student.dashboard.title
student.progress.mastery
teacher.students.needs_attention
parent.fees.outstanding
```

Do not scatter language conditionals throughout application code.

Store user language preference.

Provide English fallback when a Hindi key is missing.

---

# 22. PRIVACY AND VISIBILITY

Minimum roles:

```text
Platform Admin
Institution Admin
Campus Admin
Teacher
Student
Parent
```

Permissions must distinguish:

- view
- edit
- assign
- intervene
- export
- manage fees
- view AI conversations
- view learning graph
- view financial data

Tenant isolation is mandatory.

---

# 23. TEACHER CONTROL LAYER

Teacher instructions must be structured, not raw prompt injection.

AI context precedence should be defined explicitly:

```text
System/Safety Constraints
↓
Institution Policy
↓
Teacher Instruction
↓
Curriculum
↓
Learning State
↓
Student Request
```

The exact precedence must be documented and tested.

---

# 24. FINANCIAL DATA ISOLATION

Financial data must not enter:

- student AI context
- learning graph
- RAG context
- teacher dashboard unless explicitly authorized

Parent/admin financial access must be explicit.

---

# 25. REPOSITORY AS DEVELOPMENT MEMORY

GitHub is part of the product's development memory.

At the start of EVERY phase run/check:

```text
git status
git branch
git log
git remote -v
latest phase tracker
README
architecture docs
tests
```

The agent must know what was actually completed before modifying anything.

---

# 26. REQUIRED DEVELOPMENT CONTROL FILES

If equivalent files do not already exist, create:

```text
/docs/AI_AGENT_DEVELOPMENT_PLAN.md
/docs/PROJECT_STATE.md
/docs/ARCHITECTURE.md
/docs/DATA_MODEL.md
/docs/LEARNING_GRAPH.md
/docs/UI_UX_SYSTEM.md
/docs/SECURITY_MODEL.md
/docs/TESTING_STRATEGY.md
/docs/DEPLOYMENT.md
/docs/DECISIONS.md
/docs/BUG_TRACKER.md
/docs/PHASE_LOG.md
```

Do not create duplicates if equivalent documentation already exists.

---

# 27. PROJECT_STATE.md

Must contain:

```text
Current Phase
Phase Status
Last Successful Commit
Last Verification Date
Current Branch
Known Failing Tests
Known Bugs
Known Warnings
Current Architecture
Current Database State
Current Model
Current Provider Configuration
Current UI State
Current Security State
Pending Migrations
Pending Deprecations
Next Action
```

Update after every phase.

---

# 28. PHASE_LOG.md

Every completed phase records:

```text
Phase
Date
Objective
Files Added
Files Modified
Files Removed
Database Changes
API Changes
UI Changes
Configuration Changes
Tests Added
Tests Executed
Test Results
Bugs Found
Bugs Fixed
Known Limitations
Git Commit
Git Push
Remote Verification
```

---

# 29. BUG_TRACKER.md

Each bug:

```text
BUG-ID
Title
Severity
Detected In
Symptoms
Root Cause
Affected Files
Affected Systems
Fix
Regression Test
Status
Commit
```

Severity:

```text
P0 Critical
P1 High
P2 Medium
P3 Low
```

No P0/P1 bug may be silently carried into production.

---

# 30. DECISIONS.md

Record architectural decisions.

Example:

```text
ADR-001
Decision: one authoritative persistent learning-state store.
Reason: avoid conflicting mastery sources.
Alternatives:
- JSON-only
- event-only
- in-memory
```

The agent must consult this before reversing architecture.

---

# 31. README REPLACEMENT

The current README must eventually be replaced with a production README.

Before deleting/replacing it:

1. inventory its useful information
2. inventory setup instructions
3. inventory architecture claims
4. inventory model instructions
5. inventory known limitations
6. preserve anything still valid

Then create the new README containing:

- product overview
- architecture
- portals
- learning graph
- AI architecture
- local model setup
- optional cloud providers
- supported curriculum
- institution model
- parent portal
- fee management
- English/Hindi
- development setup
- testing
- security
- configuration
- deployment
- development workflow
- known limitations
- project status

Never claim a feature is production-ready until verified.

---

# 32. NO DEMO LOGIC IN PRODUCTION

The current repository contains scenario-specific/demo-oriented logic.

The agent must:

1. locate every demo implementation
2. classify it
3. move it into tests, fixtures, examples, or development-only tooling
4. remove it from production execution paths
5. add regression tests

Production must not depend on:

- specific student names
- hardcoded answers
- demonstration values
- fake conversations
- fake mastery
- fake institutions

---

# 33. FILE CHANGE DISCIPLINE

Before modifying a file, determine:

```text
Why is it changing?
What contract does it provide?
Who imports it?
What imports it?
What tests cover it?
What configuration references it?
What UI/API/database behavior depends on it?
```

Before creating a file:

```text
Does an equivalent exist?
Why can't it be extended?
Who imports it?
What tests cover it?
What docs reference it?
```

Avoid duplicate services and utilities.

---

# 34. IMPACT ANALYSIS

Before every phase document:

```text
Files affected
Modules affected
Imports affected
Database tables affected
API endpoints affected
Frontend routes affected
Authentication affected
Authorization affected
RAG affected
Model/provider affected
Tests affected
Deployment affected
Documentation affected
Migration requirements
Backward compatibility risks
```

---

# 35. PHASE SIZE RULE

Keep phases small.

Prefer 40+ focused phases over a few enormous phases.

A phase should normally represent:

- one architectural concern
- one migration
- one UI subsystem
- one major service
- one coherent feature

Do not combine unrelated database, AI, parent, fee, and UI work in one phase.

---

# 36. PHASE COMPLETION GATE

Before moving on:

```text
[ ] Implementation complete
[ ] Unit tests pass
[ ] Integration tests pass
[ ] Regression tests pass
[ ] Existing functionality checked
[ ] Security checks pass
[ ] No unintended API break
[ ] No unintended DB break
[ ] UI verified
[ ] Light theme verified
[ ] Dark theme verified
[ ] Error states verified
[ ] Loading states verified
[ ] Empty states verified
[ ] Documentation updated
[ ] PROJECT_STATE updated
[ ] BUG_TRACKER updated
[ ] PHASE_LOG updated
[ ] README updated when necessary
[ ] CHANGELOG updated
[ ] Git commit created
[ ] Git push successful
[ ] Remote commit verified
```

Only then mark:

```text
PHASE_STATUS = COMPLETE
```

---

# 37. GIT WORKFLOW

Preferred branch pattern:

```text
main
├── phase/001-baseline
├── phase/002-state-audit
├── phase/003-state-canonicalization
└── phase/xxx-feature
```

If repository policy requires direct main development, preserve equivalent commit discipline.

Meaningful commits:

```text
phase 01: establish repository baseline
phase 02: normalize project state tracking
phase 03: canonicalize learning state
```

Avoid meaningless commit messages such as `updates`, `fixes`, `changes`, `final`.

---

# 38. RESUMABILITY

If interrupted, resume from:

```text
PROJECT_STATE.md
PHASE_LOG.md
BUG_TRACKER.md
DECISIONS.md
README.md
Git history
Tests
```

At restart:

1. read PROJECT_STATE
2. read latest phase log
3. check git status
4. check current commit
5. run relevant tests
6. identify incomplete phase
7. continue from the last verified checkpoint

Never assume unfinished work is complete.

---

# 39. PHASE PLAN

## PHASE 00 — Repository Safety Baseline

Inspect:

- repository
- branches
- Git status
- README
- project tree
- dependencies
- tests
- configuration
- database
- UI entry points
- providers
- RAG
- authentication
- learning state
- deployment

Create/update control documents.

Run baseline tests.

Commit and push.

## PHASE 01 — Documentation Audit

Inventory existing documentation, setup instructions, architecture claims, model instructions, contradictions, and stale information.

Do not rewrite README yet.

Commit and push.

## PHASE 02 — Architecture Audit

Map:

```text
UI
API
Core
Providers
RAG
Learning Engine
Database
Storage
Auth
Config
Tests
Deployment
```

Identify duplicate modules, dead code, oversized modules, circular dependencies, and legacy code.

Commit and push.

## PHASE 03 — Test Baseline

Run all existing tests and create a failure inventory.

Every failure becomes a BUG-ID or documented baseline limitation.

Commit and push.

## PHASE 04 — Model Configuration Normalization

Create authoritative model manifest and normalize discovery, loading, context, hardware configuration, download, and health.

Add manifest/model tests.

Commit and push.

## PHASE 05 — Demo Isolation

Remove hardcoded demo scenarios from production execution.

Move them into tests/fixtures/examples.

Add regression tests.

Commit and push.

## PHASE 06 — Identity Model

Implement/reconcile:

```text
Person
User
Student
Teacher
Parent
Admin
InstitutionMembership
```

Support multiple institutional memberships.

Do not blindly replace authentication.

Commit and push.

## PHASE 07 — Institution Hierarchy

Implement/reconcile:

```text
Institution
Campus
AcademicYear
Class
Section
Enrollment
```

Add tenant isolation tests.

Commit and push.

## PHASE 08 — Roles and Permissions

Implement/reconcile:

```text
Platform Admin
Institution Admin
Campus Admin
Teacher
Student
Parent
```

Create a permission matrix and test critical boundaries.

Commit and push.

## PHASE 09 — Curriculum Abstraction

Support:

- NCERT
- CBSE
- ICSE
- State Boards
- College
- Custom

Keep curriculum out of hardcoded tutor logic.

Commit and push.

## PHASE 10 — Curriculum Ingestion / Plugin Architecture

Create interfaces for:

```text
Curriculum Provider
Content Provider
Course Provider
Knowledge Source
```

Connect these to RAG architecture.

Commit and push.

## PHASE 11 — Canonical Learning State

Consolidate:

- TutorContext
- StudentProfile
- TutorStateManager
- SQLite mastery
- LDG
- event storage

into one authoritative persistent model plus session runtime state.

Commit and push.

## PHASE 12 — Learning Event System

Implement normalized event creation, validation, persistence, and querying.

Commit and push.

## PHASE 13 — Learning Graph

Implement concept graph with prerequisites, mastery, confidence, attempts, misconceptions, review, assessments, and teacher interventions.

Commit and push.

## PHASE 14 — Mastery and Evidence Engine

Implement deterministic evidence-backed mastery.

Test:

- correct answer
- incorrect answer
- repeated attempts
- review
- decay
- prerequisite effects

Commit and push.

## PHASE 15 — Next Action Engine

Implement:

```text
CONTINUE
EXPLAIN
HINT
REMEDIATE
PRACTICE
REVIEW
ASSESS
CHALLENGE
ADVANCE
```

Add explainability.

Commit and push.

## PHASE 16 — Query Understanding

Add structured query interpretation using the local SLM with schema validation and deterministic fallback.

Commit and push.

## PHASE 17 — Context Builder

Build context from:

- conversation
- learner state
- curriculum
- teacher instructions
- institution policy
- RAG
- recent events

Avoid irrelevant context.

Commit and push.

## PHASE 18 — Response Planner

Implement structured pedagogical planning and schema validation.

Commit and push.

## PHASE 19 — Response Validator

Validate:

- factual consistency
- curriculum alignment
- source requirements
- educational safety
- answer leakage
- model failure
- formatting

Commit and push.

## PHASE 20 — State Commit Pipeline

Only commit learning-state changes after response/evaluation validation.

Ensure failed AI requests cannot corrupt state.

Commit and push.

## PHASE 21 — Local-First Router

Implement:

```text
LOCAL_ONLY
LOCAL_FIRST
CLOUD_PREFERRED
```

Use capability matching.

Commit and push.

## PHASE 22 — Cloud Provider Abstraction

Normalize optional OpenAI-compatible, Anthropic, Google, and other configured providers.

Commit and push.

## PHASE 23 — RAG Reliability

Audit retrieval, citations, source quality, curriculum scope, prompt-injection protection, source isolation, and learning-context integration.

Commit and push.

## PHASE 24 — Shared UI Design System

Implement shared:

```text
tokens
themes
typography
buttons
inputs
cards
tables
tabs
modal
drawer
toast
tooltip
progress
timeline
status
skeleton
empty state
error state
chat components
```

Implement light and dark themes.

Commit and push.

## PHASE 25 — Application Shell

Implement consistent sidebar, topbar, navigation, responsive shell, user menu, theme selector, and language selector.

Commit and push.

## PHASE 26 — Tutor UI Redesign

Implement the premium conversation-first Tutor defined in this document.

Required:

- conversation
- intelligent composer
- learning context
- response actions
- sources
- truthful AI status
- responsive design
- dark/light themes

Commit and push.

## PHASE 27 — Student Portal

Implement:

- dashboard
- curriculum
- learning graph
- progress
- review queue
- assignments
- assessments
- activity
- profile
- notifications

Commit and push.

## PHASE 28 — Teacher Portal

Implement:

- class overview
- students
- learning health
- student profile
- interventions
- assessments
- teacher instructions
- AI Copilot

Commit and push.

## PHASE 29 — Parent Portal

Implement:

- child selector
- progress
- attendance
- assignments
- assessments
- teacher updates
- recommendations
- fees
- notifications

Commit and push.

## PHASE 30 — Fee Data Layer

Implement:

- fee structures
- fee plans
- fee accounts
- invoices
- payments
- receipts
- discounts
- refunds

Commit and push.

## PHASE 31 — Fee Administration UI

Implement:

- fee setup
- monthly billing
- student fee account
- payment recording
- receipts
- outstanding reports
- filtering
- exports

Commit and push.

## PHASE 32 — Payment Provider Abstraction

Create a provider interface and keep payment-specific logic outside core financial models.

Commit and push.

## PHASE 33 — English/Hindi Internationalization

Implement translation registry, language preference, English fallback, Hindi UI coverage, and AI language preference.

Commit and push.

## PHASE 34 — Parent Privacy and Visibility

Implement explicit visibility policies and test parent/student/teacher/institution boundaries.

Commit and push.

## PHASE 35 — Learning Analytics

Build:

```text
Student Learning Health
Class Learning Health
Section Learning Health
Institution Learning Health
```

Use evidence from learning events.

Commit and push.

## PHASE 36 — Explainability

Implement:

```text
Why am I seeing this?
Why was I flagged?
Why is this my next lesson?
Why is this concept due for review?
```

Recommendations must be traceable to evidence.

Commit and push.

## PHASE 37 — Security Audit

Audit:

- authentication
- authorization
- tenant isolation
- session handling
- secrets
- uploads
- prompt injection
- API validation
- payment security
- logs
- PII
- student data
- parent data

Commit and push.

## PHASE 38 — Failure Recovery

Test:

- local model unavailable
- corrupt model
- provider timeout
- RAG failure
- database failure
- malformed model output
- network failure
- interrupted transaction
- invalid curriculum
- payment failure

Commit and push.

## PHASE 39 — Full Regression

Run:

```text
unit
integration
API
database
RAG
learning graph
AI orchestration
UI
responsive
theme
auth
authorization
privacy
fees
payments
i18n
```

Commit and push.

## PHASE 40 — Performance

Measure:

- startup
- model startup
- first token latency
- response latency
- RAG latency
- DB latency
- concurrency
- memory
- CPU
- UI load

Optimize only after measurement.

Commit and push.

## PHASE 41 — Deployment Validation

Verify:

- environment configuration
- secrets
- migrations
- backups
- logging
- monitoring
- health checks
- model availability
- provider configuration
- assets
- HTTPS
- error handling

Commit and push.

## PHASE 42 — Documentation Completion

Finalize:

```text
README.md
ARCHITECTURE.md
DATA_MODEL.md
LEARNING_GRAPH.md
UI_UX_SYSTEM.md
SECURITY_MODEL.md
TESTING_STRATEGY.md
DEPLOYMENT.md
```

Remove obsolete documentation.

Commit and push.

## PHASE 43 — Production Readiness Gate

Do not declare production readiness unless:

```text
[ ] No critical bugs
[ ] No known P1 bugs
[ ] Tests pass
[ ] Migrations verified
[ ] Tenant isolation verified
[ ] Authentication verified
[ ] Authorization verified
[ ] Parent privacy verified
[ ] Fee/payment security verified
[ ] Local model works
[ ] Cloud fallback works when enabled
[ ] RAG works
[ ] Learning graph works
[ ] Student portal works
[ ] Teacher portal works
[ ] Parent portal works
[ ] Admin portal works
[ ] Light mode works
[ ] Dark mode works
[ ] English works
[ ] Hindi works
[ ] Mobile works
[ ] Accessibility checked
[ ] Failure recovery checked
[ ] No demo data in production
[ ] No secrets committed
[ ] Documentation complete
[ ] GitHub state verified
```

---

# 40. BACKTESTING

Create deterministic educational scenarios.

Example:

```text
Student starts concept
→ asks question
→ receives explanation
→ answers incorrectly
→ misconception detected
→ remediation
→ answers correctly
→ mastery changes
→ review scheduled
→ review completed
→ concept advances
```

Expected state transitions must be tested.

Do not rely only on UI tests.

---

# 41. AI OUTPUT CONTRACTS

Every structured model output must be schema-validated.

If invalid:

1. attempt safe repair
2. retry only when policy permits
3. fall back to deterministic behavior
4. never commit invalid state

Parsing JSON is not equivalent to validating an AI decision.

---

# 42. OBSERVABILITY

Track enough information to debug without unnecessarily exposing private student data:

```text
request ID
user role
institution ID
session ID
model
provider
latency
RAG usage
pipeline stage
success/failure
error category
```

Do not log raw private conversations unless policy explicitly permits it.

---

# 43. PHASE PLANNING TEMPLATE

Before coding:

```text
PHASE:
OBJECTIVE:

CURRENT STATE:
-

FILES TO INSPECT:
-

FILES TO CREATE:
-

FILES TO MODIFY:
-

FILES TO DELETE/DEPRECATE:
-

DATABASE IMPACT:
-

API IMPACT:
-

UI IMPACT:
-

AI/RAG IMPACT:
-

AUTHORIZATION IMPACT:
-

SECURITY IMPACT:
-

TEST IMPACT:
-

DEPLOYMENT IMPACT:
-

BACKWARD COMPATIBILITY:
-

RISKS:
-

ROLLBACK PLAN:
-

SUCCESS CRITERIA:
-
```

---

# 44. CHANGE REVIEW TEMPLATE

After implementation and before final phase verification:

```text
FILES CHANGED:
-

WHY EACH FILE CHANGED:
-

NEW DEPENDENCIES:
-

REMOVED DEPENDENCIES:
-

API CONTRACT CHANGES:
-

DATABASE CHANGES:
-

STATE CHANGES:
-

UI CHANGES:
-

AUTH CHANGES:
-

SECURITY CHANGES:
-

POTENTIAL REGRESSIONS:
-

MIGRATION REQUIRED:
-
```

---

# 45. COMPLETION REPORT

At the end of every phase:

```text
PHASE:
STATUS: COMPLETE / BLOCKED

IMPLEMENTED:
-

FILES CREATED:
-

FILES MODIFIED:
-

FILES REMOVED:
-

TESTS:
-

TEST RESULT:
-

BUGS FOUND:
-

BUGS FIXED:
-

KNOWN LIMITATIONS:
-

DATABASE MIGRATION:
-

SECURITY CHECK:
-

GIT COMMIT:
-

GIT PUSH:
-

REMOTE VERIFIED:
-

NEXT PHASE:
-
```

---

# 46. DO NOT OVERWRITE WORKING SYSTEMS BLINDLY

Before replacing an existing subsystem:

1. understand it
2. test it
3. identify what works
4. identify what fails
5. identify dependencies
6. design migration
7. implement incrementally
8. run regression
9. remove old code only after verification

Never blindly rewrite:

- authentication
- database
- RAG
- model providers
- learning engine
- working APIs

---

# 47. DATABASE MIGRATIONS

Every database change requires:

```text
schema change
migration
rollback consideration
data migration
validation
test
```

Never manually change production schema without a tracked migration.

---

# 48. API COMPATIBILITY

Before changing an API:

- find callers
- find frontend consumers
- find tests
- find external integrations
- find documentation

Prefer backwards-compatible evolution.

If breaking change is unavoidable:

```text
version endpoint
→ migrate callers
→ test
→ document
→ deprecate old endpoint
→ remove only after verification
```

---

# 49. UI COMPATIBILITY

Do not redesign one page in isolation.

Shared components must drive:

```text
Student
Teacher
Parent
Admin
Tutor
```

Any change to a shared:

```text
Button
Input
Modal
Sidebar
Typography
Theme
```

must be checked across all portals.

---

# 50. STUDENT DATA MODEL

Distinguish:

```text
Person Identity
User Authentication
Student Profile
Institution Membership
Academic Enrollment
Learning State
Learning Events
Parent Relationship
Teacher Relationship
```

Do not put all of these into one giant student record.

---

# 51. MULTI-INSTITUTION STUDENT

Target:

```text
Global Learner Identity
├── Institution A Membership
│   └── Academic Context
└── Institution B Membership
    └── Academic Context
```

Institution-specific data must remain isolated.

Global learning data must have explicit visibility rules.

---

# 52. PARENT RELATIONSHIP

Use explicit relationship data:

```text
Parent
Student
Relationship
Permissions
Visibility Policy
```

Do not infer parental access from matching email addresses.

---

# 53. LEARNING GRAPH VISIBILITY

Student sees:

```text
Mastery
Progress
Strengths
Developing Concepts
Review
Next Action
```

Teacher sees, subject to permission:

```text
Learning evidence
Misconceptions
Interventions
Assessment evidence
```

Parent sees:

```text
High-level progress
Attendance
Assessments
Areas needing attention
Recommended support
```

Admin sees:

```text
Aggregated institutional learning health
```

---

# 54. QUALITY PRINCIPLE

Optimize for:

```text
Correctness
Maintainability
Explainability
Security
Resumability
Testability
User Experience
Institutional Scalability
```

Not for:

```text
number of features
number of files
amount of code
```

---

# 55. DEFINITION OF DONE

A feature is DONE only when:

```text
Code exists
+
Architecture is correct
+
Tests exist
+
Tests pass
+
Failure cases handled
+
Security considered
+
UI states implemented
+
Documentation updated
+
Git checkpoint created
+
GitHub verified
```

---

# 56. FINAL AGENT RULE

Never report only:

> "The feature is implemented."

Report:

> "The feature is implemented, tested, regression-checked, documented, committed, pushed, and verified at commit `<hash>`."

If incomplete:

```text
INCOMPLETE
Reason:
Impact:
Required Next Action:
```

Never hide incomplete work.

---

# 57. FIRST ACTION WHEN THIS DOCUMENT IS PROVIDED

The first action MUST NOT be coding.

The agent must:

1. Inspect the GitHub repository.
2. Inspect branch and Git status.
3. Read README.
4. Read existing documentation.
5. Map the repository.
6. Run baseline tests.
7. Identify working/broken/partial systems.
8. Inspect database/state architecture.
9. Inspect model/provider architecture.
10. Inspect RAG.
11. Inspect all existing portal surfaces.
12. Identify demo code.
13. Identify duplicate state systems.
14. Identify migrations.
15. Identify security boundaries.
16. Create/update `PROJECT_STATE.md`.
17. Create/update `PHASE_LOG.md`.
18. Create/update `BUG_TRACKER.md`.
19. Create/update `DECISIONS.md`.
20. Produce the Phase 0 assessment.
21. Commit Phase 0.
22. Push Phase 0.
23. Verify the remote commit.

Only then begin Phase 1.

---

# 58. MASTER PROGRESS TRACKER

Maintain this table in the repository and update it after every phase.

| Phase | Area | Status | Tests | Commit | Notes |
|---|---|---|---|---|---|
| 00 | Repository Baseline | NOT_STARTED | — | — | — |
| 01 | Documentation Audit | NOT_STARTED | — | — | — |
| 02 | Architecture Audit | NOT_STARTED | — | — | — |
| 03 | Test Baseline | NOT_STARTED | — | — | — |
| 04 | Model Manifest | NOT_STARTED | — | — | — |
| 05 | Demo Isolation | NOT_STARTED | — | — | — |
| 06 | Identity Model | NOT_STARTED | — | — | — |
| 07 | Institution Hierarchy | NOT_STARTED | — | — | — |
| 08 | Permissions | NOT_STARTED | — | — | — |
| 09 | Curriculum | NOT_STARTED | — | — | — |
| 10 | Curriculum Plugins | NOT_STARTED | — | — | — |
| 11 | Canonical Learning State | NOT_STARTED | — | — | — |
| 12 | Learning Events | NOT_STARTED | — | — | — |
| 13 | Learning Graph | NOT_STARTED | — | — | — |
| 14 | Mastery Engine | NOT_STARTED | — | — | — |
| 15 | Next Action Engine | NOT_STARTED | — | — | — |
| 16 | Query Understanding | NOT_STARTED | — | — | — |
| 17 | Context Builder | NOT_STARTED | — | — | — |
| 18 | Response Planner | NOT_STARTED | — | — | — |
| 19 | Response Validator | NOT_STARTED | — | — | — |
| 20 | State Commit | NOT_STARTED | — | — | — |
| 21 | Local-First Router | NOT_STARTED | — | — | — |
| 22 | Cloud Providers | NOT_STARTED | — | — | — |
| 23 | RAG Reliability | NOT_STARTED | — | — | — |
| 24 | UI Design System | NOT_STARTED | — | — | — |
| 25 | Application Shell | NOT_STARTED | — | — | — |
| 26 | Tutor UI | NOT_STARTED | — | — | — |
| 27 | Student Portal | NOT_STARTED | — | — | — |
| 28 | Teacher Portal | NOT_STARTED | — | — | — |
| 29 | Parent Portal | NOT_STARTED | — | — | — |
| 30 | Fee Data Layer | NOT_STARTED | — | — | — |
| 31 | Fee Admin UI | NOT_STARTED | — | — | — |
| 32 | Payment Abstraction | NOT_STARTED | — | — | — |
| 33 | English/Hindi | NOT_STARTED | — | — | — |
| 34 | Parent Privacy | NOT_STARTED | — | — | — |
| 35 | Learning Analytics | NOT_STARTED | — | — | — |
| 36 | Explainability | NOT_STARTED | — | — | — |
| 37 | Security Audit | NOT_STARTED | — | — | — |
| 38 | Failure Recovery | NOT_STARTED | — | — | — |
| 39 | Full Regression | NOT_STARTED | — | — | — |
| 40 | Performance | NOT_STARTED | — | — | — |
| 41 | Deployment Validation | NOT_STARTED | — | — | — |
| 42 | Documentation | NOT_STARTED | — | — | — |
| 43 | Production Gate | NOT_STARTED | — | — | — |

---

# 59. SUCCESSFUL END STATE

```text
                         GAYATRI
                            │
             ┌──────────────┼──────────────┐
             │              │              │
          STUDENT        TEACHER         PARENT
             │              │              │
             └──────────────┼──────────────┘
                            │
                          ADMIN
                            │
                            ▼
                    LEARNING GRAPH
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
     CURRICULUM          EVIDENCE              AI
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    LOCAL-FIRST SLM
                            │
                    OPTIONAL CLOUD AI
                            │
                            ▼
                NEXT BEST LEARNING ACTION
```

The final platform should be able to answer, for every authorized user:

```text
What is happening?
Why is it happening?
What evidence supports it?
What should happen next?
Who should act?
```

---

# 60. FINAL PRINCIPLE

The objective is not to make the repository larger.

The objective is to make Gayatri:

**coherent, testable, explainable, institution-ready, student-centered, AI-native, locally capable, secure, and maintainable.**

Every code change must make the system easier to understand and safer to extend.

Every phase must leave the repository in a working, recoverable state.

Every major decision must be documented.

Every bug must become traceable.

Every important learning action must become observable evidence.

Every AI recommendation must be explainable.

Every deployment checkpoint must be reproducible.

The AI coding agent must always know:

> **where the project is, what changed, why it changed, what remains broken, what must happen next, and exactly which GitHub commit represents the verified state.**
