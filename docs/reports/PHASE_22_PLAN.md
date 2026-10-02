# Phase 22 Implementation & Test Plan: Security, Privacy & Isolation Audit

**Document:** `docs/reports/PHASE_22_PLAN.md`  
**Phase:** 22  
**Section:** 12.22 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  

---

## 1. Objective

Perform an independent security, privacy, and isolation audit across identity, RAG, courses, classes, students, instructions, uploads, model prompts, logs, and sync.
Enforce actual boundary defenses requiring negative tests with live denied responses (HTTP 400, 401, 403, 404, 422) instead of mocking or generic PASS labels.

Per Section 12.22:
- Inspect RBAC/auth, security modules, upload handling, instruction validation, RAG access control, audit logs, parent privacy, sync, API routes, bridge methods.
- Eliminate bugs, deadends, and silent fails at security boundaries.
- Execute attack-style tests across all Section 12.22 threat vectors:
  1. Cross-tenant access
  2. IDOR (Insecure Direct Object Reference)
  3. Privilege escalation
  4. Prompt injection
  5. Malicious course content & script injection
  6. Malicious teacher instruction
  7. Path traversal
  8. Unsafe upload & executable file extension
  9. Secret & credential leakage
  10. Log PII leakage & data masking
  11. RAG data leakage across course, version, and class boundaries
  12. Sync replay idempotency & unauthorized device hijacking

---

## 2. Boundary Defenses & Implementation Adjustments

1. **Cross-Tenant & Privilege Escalation in Classes & Cohorts (`central_platform/api/routes/classes.py`):**
   - Enforce RBAC in `create_class_group`: Reject `STUDENT` role with 403 Forbidden. Reject cross-organization creation (`actor.organization_id != req.organization_id` for non-superadmin) with 403 Forbidden.
   - Enforce RBAC in `create_cohort_for_class`: Check class exists. Reject student role with 403 Forbidden. Reject cross-organization creation with 403 Forbidden.

2. **Malicious Teacher Instructions & Cross-Tenant Target Student (`central_platform/api/routes/instructions.py`):**
   - Enforce `TeacherInstructionValidator.validate(req.instruction)`. If invariant violations detected, return HTTP 400 Bad Request.
   - Enforce tenant isolation on `create_instruction`: Non-superadmin cannot create instructions for a different organization (HTTP 403). Non-superadmin cannot target a student belonging to a different organization (HTTP 403).

3. **Malicious Course Content & Script Injection (`central_platform/courses/service.py`):**
   - Validate course `code` for path traversal (`..`, `/`, `\`) and illegal characters; raise `CourseValidationError` (HTTP 400).
   - Validate course `title` and `description` against embedded `<script>`, `javascript:`, and HTML event handlers (`onerror=`, `onload=`); raise `CourseValidationError` (HTTP 400).

4. **Unsafe Upload & Path Traversal in RAG (`central_platform/rag/service.py`):**
   - Validate `file_name` in `upload_knowledge_asset` and `ingest_document`: Neutralize/reject path traversal sequences (`..`, `/`, `\`) and executable extensions (`.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.py`, `.dll`, `.so`). Raise `ValueError` (HTTP 400).

5. **Sync Replay & Device Authorization (`central_platform/api/routes/sync.py`):**
   - Catch `PermissionError` from `SyncService.process_sync_batch` (e.g. device bound to another student) and map to HTTP 403 Forbidden.
   - Verify `operation_id` replay returns cached receipt without duplicating events or state mutations.

6. **Prompt Injection & IDOR in Tutor Route (`central_platform/api/routes/tutor.py`, `central_platform/tutor/orchestrator.py`):**
   - Enforce `enforce_resource_boundaries` in `/tutor/turn` against student IDOR.
   - Sanitize student prompt via `SecurityAuditor.sanitize_prompt`. If jailbreak, system prompt override, or chemical weapon synthesis pattern detected, return safe pedagogical redirection turn without executing LLM overrides.

---

## 3. Test Architecture Plan

Create `tests/test_phase22_security_privacy_isolation_audit.py` with 12 attack-style test suites:
1. `test_attack_cross_tenant_course_access`: Verify private course of Org Alpha is denied to Org Beta user (HTTP 403).
2. `test_attack_idor_student_learning_record`: Verify Student A cannot read or snapshot Student B's SLR/telemetry (HTTP 403).
3. `test_attack_privilege_escalation_student_actions`: Verify Student cannot create courses, class groups, cohorts, or approve knowledge assets (HTTP 403).
4. `test_attack_prompt_injection_in_tutor_turn`: Inject jailbreak & system prompt override in tutor turn; verify safe pedagogical redirection without system prompt disclosure.
5. `test_attack_malicious_course_content_injection`: Inject script tags and path traversal into course creation; verify rejection (HTTP 400).
6. `test_attack_malicious_teacher_instruction`: Submit instruction violating anti-answer leakage / security invariants or targeting cross-tenant student; verify rejection (HTTP 400 / 403).
7. `test_attack_path_traversal_in_rag_upload`: Submit upload filenames containing `../../etc/passwd` or `..\..\windows\system32`; verify rejection.
8. `test_attack_unsafe_executable_file_upload`: Attempt uploading `.exe`, `.bat`, or `.sh` files to RAG; verify rejection.
9. `test_attack_secret_and_credential_exposure`: Verify user profile and auth responses never expose password hashes, salts, or API secrets.
10. `test_attack_log_pii_leakage_masking`: Verify audit log sanitizer masks emails and phone numbers while preserving technical context.
11. `test_attack_rag_data_leakage_cross_boundaries`: Query RAG from another org or unauthorized class; verify RAG_DENIED or zero cross-tenant leakage.
12. `test_attack_sync_replay_and_device_hijack`: Verify duplicate sync operations return cached receipts (idempotent), and device bound to Student A rejects Student B (HTTP 403).
