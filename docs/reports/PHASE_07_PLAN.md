# Phase 07 Execution Plan — Teacher Instruction Hierarchy

**Document:** `docs/reports/PHASE_07_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.7)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Implement teacher instructions as persisted, authorized, time-bounded pedagogical directives structured across an explicit institutional hierarchy (`ORGANIZATION`, `COURSE`, `CLASS`, `STUDENT`, `SESSION`) that adapt tutor behavior without compromising non-negotiable platform safety policies.

Specifically:
1. **Multi-Tiered Hierarchical Scopes:**
   - `ORGANIZATION`: Institutional-wide pedagogical policies.
   - `COURSE`: Course-wide directives (e.g. emphasize derivations, notation standards).
   - `CLASS`: Section/cohort-specific pacing or homework guidance.
   - `STUDENT`: Individual personalized pedagogical instructions (e.g. provide extra scaffolding, focus on visual intuition).
   - `SESSION`: Live session-specific directives (e.g. review previous quiz errors).
2. **Deterministic Resolution Hierarchy & Conflict Precedence:**
   - Resolution Cascade: `Platform Safety Policies` → `Organization` → `Course` → `Class` → `Student` → `Session`.
   - Precedence: More granular scopes override broader scopes (`SESSION` > `STUDENT` > `CLASS` > `COURSE` > `ORGANIZATION`).
   - Tie-breaking: Higher priority (1=Low to 5=Urgent), followed by latest timestamp.
3. **Non-Negotiable Safety Policy Invariants:**
   - Platform safety policies can **never** be overridden by any teacher instruction at any tier.
   - Directives attempting prompt injection, jailbreaks, answer leakage (bypassing Socratic guidance), toxic language, privilege escalation, or scientific/mathematical falsehoods are rejected and quarantined (`REJECTED`).
4. **Secure Prompt Framing Invariant:**
   - Instruction content is distinct from knowledge content. Raw teacher text is **never** injected directly into system prompts. All instructions are validated, sanitized, and wrapped in structural data frames with explicit invariant guardrails.
5. **Role-Based Authorization & Auditing:**
   - Teachers can only create instructions for their assigned courses and classes within their organization.
   - Students are strictly forbidden from creating, modifying, or revoking instructions (403 PermissionError).
   - Every instruction maintains an immutable audit trail (`created`, `updated`, `revoked`, `toggled`).

---

## 2. Forensic Findings & Architectural Pipeline Strategy

1. **Current State & Gaps:**
   - `central_platform/teacher/instruction.py` defines basic validator and in-memory engine, but `ScopeType` uses `STUDENT, COHORT, COURSE, CONCEPT`, lacking `ORGANIZATION`, `CLASS`, and `SESSION`.
   - The SQL table `teacher_instructions` in `migrations/001_initial_schema.sql` lacks columns for `organization_id`, `course_version_id`, `class_id`, `session_id`, `scope_type`, `status`, `safety_status`, `start_at`, `expires_at`, `version`, `audit_trail_json`, and `updated_at`.
   - `PlatformDatabase` CRUD methods for teacher instructions are minimal and don't query across the complete hierarchical cascade.
   - API endpoints in `central_platform/api/routes/teachers.py` don't expose the full hierarchical scope fields or role checks.

2. **Target Pipeline Design:**
   - **Database Migration 007 (`migrations/007_teacher_instruction_hierarchy.sql` & down):**
     - Add `organization_id`, `course_version_id`, `class_id`, `session_id`, `scope_type`, `status`, `safety_status`, `start_at`, `expires_at`, `version`, `audit_trail_json`, `updated_at` to `teacher_instructions`.
     - Composite indexes for rapid hierarchical queries: `idx_teacher_inst_hierarchy (course_id, class_id, student_id, is_active)`.
   - **Hierarchical Resolver (`TeacherInstructionEngine.resolve_hierarchical_instructions`):**
     - Collects active, non-expired, and validated instructions across applicable scopes (`ORGANIZATION`, `COURSE`, `CLASS`, `STUDENT`, `SESSION`).
     - Deduplicates and resolves conflicts using scope specificity, priority, and timestamp.
     - Formats prompt directives with data framing and anti-override invariant clauses.
   - **Authorization Gate:**
     - Enforces institutional ownership and role permissions (`TEACHER`, `ORG_ADMIN`, `SUPER_ADMIN`).

---

## 3. Planned Implementation Steps

### Step 1: Entity & Schema Definitions
- Update `central_platform/models/schema.py`:
  - Define `InstructionScope` enum: `ORGANIZATION`, `COURSE`, `CLASS`, `STUDENT`, `SESSION`.
  - Extend `TeacherInstructionRecord` with `organization_id`, `course_version_id`, `class_id`, `session_id`, `scope_type`, `status`, `safety_status`, `start_at`, `expires_at`, `version`, `audit_trail_json`, `updated_at`.
- Update `central_platform/teacher/instruction.py`:
  - Update `ScopeType` to align with `InstructionScope`.
  - Extend `TeacherInstruction` dataclass with all Section 12.7 fields.

### Step 2: Database Migration 007 (`migrations/007_teacher_instruction_hierarchy.sql` & down)
- Create forward migration 007 adding columns and composite indexes.
- Create rollback migration `007_teacher_instruction_hierarchy_down.sql` with clean reversible table rebuild.
- Test bidirectional rollback and idempotent re-application via `scripts/migrate_db.py`.

### Step 3: Database Access Layer (`central_platform/db.py`)
- Update `create_teacher_instruction`, `get_teacher_instruction`, `update_teacher_instruction`, `delete_teacher_instruction`.
- Implement `get_hierarchical_teacher_instructions(course_id, organization_id, class_id, student_id, session_id)` in `PlatformDatabase`.

### Step 4: Hierarchical Instruction Engine & Security Validator (`central_platform/teacher/instruction.py`)
- Implement `resolve_hierarchical_instructions(...)` supporting the complete resolution cascade:
  `Platform Safety Invariants` → `ORGANIZATION` → `COURSE` → `CLASS` → `STUDENT` → `SESSION`.
- Implement conflict resolution and deterministic precedence ordering.
- Update `format_prompt_directive(...)` to enforce secure structural data framing without raw prompt leakage.
- Enforce role-based creation, modification, and revocation authorization.

### Step 5: REST API Route & Schema Updates (`central_platform/api/routes/teachers.py`, `schemas.py`)
- Update `TeacherInstructionCreateRequest`, `TeacherInstructionResponse`, `TeacherInstructionUpdateRequest` with hierarchical fields.
- Update endpoints to support hierarchical query parameters.

### Step 6: Test Suite & Invariant Verification (`tests/test_phase07_teacher_instruction_hierarchy.py`)
- Write 10+ comprehensive unit, integration, and security tests:
  1. Authorized teacher can create hierarchical instructions.
  2. Unauthorized teacher denied cross-org/unassigned course instruction.
  3. Student strictly forbidden from creating/modifying instructions (403 PermissionError).
  4. Expired/revoked instructions are excluded from resolution.
  5. Class instruction reaches only students in that class.
  6. Student instruction reaches only the targeted student.
  7. Deterministic precedence: Session > Student > Class > Course > Organization.
  8. Conflicting priority tie-breaking: Higher priority takes precedence; newest timestamp tie-breaker.
  9. Prompt injection and jailbreak attempts rejected (`SafetyStatus.REJECTED`).
  10. System policy protection: Anti-answer leakage cannot be bypassed by any teacher instruction.
  11. Secure data framing: Raw text never directly injected into system prompt.
  12. End-to-end REST API lifecycle for hierarchical instructions.

---

## 4. Acceptance Criteria & Quality Gates

1. **Safety Invariant:** Zero tolerance for prompt injection or system invariant overrides.
2. **Scoping Fidelity:** Class and student instructions never leak across boundaries.
3. **Database Integrity:** Migration 007 applies and rolls back cleanly with 100% reversible fidelity.
4. **Zero Regressions:** All 908 existing tests continue to pass 100% green.
5. **Documentation & Tracking:** Test report and results recorded, ledgers updated, committed and pushed to `origin/master`.
