# Gayatri AI Platform — Route Reachability & Audit Matrix

## Executive Summary

This document provides a forensic audit of every registered route within the Gayatri Central Platform API as mandated by **Section 15 (Phase 10) of the Master Remediation Plan**.
A total of **229 unique endpoints** were discovered, analyzed, and mapped across all 11 required dimensions.

---

## Route Reachability Matrix

| Route | Method | Auth | Role | Resource Scope | Service | DB Writes | External Calls | Fallback | Error Contract | Runtime Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| `/api/v1/auth/login` | `POST` | None / Public | Any (Unauth for login/register) | Global | `auth.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/auth/logout` | `POST` | None / Public | Any (Unauth for login/register) | Global | `auth.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/auth/me` | `GET` | Bearer JWT | Any (Unauth for login/register) | Global | `auth.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/auth/refresh` | `POST` | None / Public | Any (Unauth for login/register) | Global | `auth.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/auth/password-reset` | `POST` | None / Public | Any (Unauth for login/register) | Global | `auth.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/auth/demo-tokens` | `GET` | None / Public | Any (Unauth for login/register) | Global | `auth.py` | NO | NO | Disabled in Prod (404) | 400, 404, 500 | VERIFIED |
| `/api/v1/users` | `GET` | Optional JWT | Authenticated | Global | `users.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/users` | `POST` | Optional JWT | Authenticated | Global | `users.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/users/{user_id}` | `GET` | Optional JWT | Authenticated | Global | `users.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/snapshot` | `POST` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/slr` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/action` | `POST` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/progress` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/progress/heatmap` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/progress/summary` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses/{course_id}/curriculum` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses/{course_id}/assignments` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses/{course_id}/knowledge` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses/switch` | `POST` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/students/{student_id}/courses/{course_id}/offline-status` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `students.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/dashboard` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions/validate` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions/{instruction_id}` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions/{instruction_id}` | `PATCH` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions/{instruction_id}` | `DELETE` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/instructions/toggle` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/alerts/resolve` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/{intervention_id}` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/{intervention_id}` | `PATCH` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/{intervention_id}/notes` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/{intervention_id}/resolve` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/{intervention_id}/dismiss` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/interventions/evaluate` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/copilot/briefing` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/copilot/query` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | Telemetry / Audit | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/slr` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/timeline` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/mastery` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/misconceptions` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/sessions` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/interventions` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/students/{student_id}/instructions` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/courses` | `GET` | Optional JWT | TEACHER, ADMIN | Enrolled Student / Offering Org / Public | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/classes` | `GET` | Optional JWT | TEACHER, ADMIN | Tenant Organization | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/classes` | `POST` | Optional JWT | TEACHER, ADMIN | Tenant Organization | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/classes/{class_id}/students` | `GET` | Optional JWT | TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/classes/{class_id}/notes` | `POST` | Optional JWT | TEACHER, ADMIN | Tenant Organization | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/remedial-content` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/assignments` | `POST` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/assignments` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/assessments` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/teachers/alerts` | `GET` | Optional JWT | TEACHER, ADMIN | Global | `teachers.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/dashboard` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/organizations` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/organizations` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/users` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/users` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/users/{user_id}` | `PATCH` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/users/{user_id}` | `DELETE` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/teachers` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/students` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Student Principal / Linked Parent / Org Teacher | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/courses` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Enrolled Student / Offering Org / Public | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/courses` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Enrolled Student / Offering Org / Public | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/curricula` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/curricula` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/classes` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Organization | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/classes` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Organization | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/cohorts` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Organization | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/cohorts` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Organization | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/enrollments` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/enrollments` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/enrollments/{enrollment_id}` | `DELETE` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/providers` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/providers` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/models` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/models` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/ai-policies` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/ai-policies` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/feature-flags` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/feature-flags` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/audit` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/analytics` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/admin/system-health` | `GET` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | NO | NO | 503 UNHEALTHY | 503 on degraded | VERIFIED |
| `/api/v1/admin/kill-switch` | `POST` | Optional JWT | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `admin.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses` | `GET` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/review-queue` | `GET` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}` | `GET` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/select` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions` | `GET` | None / Public | Public | Enrolled Student / Offering Org / Public | `courses.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions/{version_id}/submit-review` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions/{version_id}/submit` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions/{version_id}/publish` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/archive` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/courses/{course_id}/versions/{version_id}/archive` | `POST` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `courses.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/curricula/{course_id}` | `GET` | None / Public | Public | Enrolled Student / Offering Org / Public | `curricula.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/curricula/versions/{version_id}/hierarchy` | `GET` | None / Public | Public | Global | `curricula.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/curricula/{curriculum_id}/versions` | `GET` | None / Public | Public | Global | `curricula.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/curricula/{curriculum_id}/versions` | `POST` | Optional JWT | Authenticated | Global | `curricula.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/curricula/versions/{version_id}/validate` | `POST` | None / Public | Public | Global | `curricula.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/curricula/versions/{version_id}/publish` | `POST` | Optional JWT | Authenticated | Global | `curricula.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/curricula/import` | `POST` | Optional JWT | Authenticated | Global | `curricula.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/curricula/versions/{version_id}/export` | `GET` | None / Public | Public | Global | `curricula.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/enrollments` | `GET` | Optional JWT | Authenticated | Global | `enrollments.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/enrollments` | `POST` | Optional JWT | Authenticated | Global | `enrollments.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/enrollments/{enrollment_id}` | `GET` | Optional JWT | Authenticated | Global | `enrollments.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/classes` | `GET` | None / Public | Public | Tenant Organization | `classes.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/classes` | `POST` | Optional JWT | Authenticated | Tenant Organization | `classes.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/classes/{class_id}` | `GET` | None / Public | Public | Tenant Organization | `classes.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/classes/{class_id}/cohorts` | `POST` | Optional JWT | Authenticated | Tenant Organization | `classes.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/classes/{class_id}/cohorts` | `GET` | None / Public | Public | Tenant Organization | `classes.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/organizations` | `GET` | None / Public | Public | Global | `organizations.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/organizations/{org_id}` | `GET` | None / Public | Public | Global | `organizations.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/organizations` | `POST` | Optional JWT | Authenticated | Global | `organizations.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/instructions` | `GET` | None / Public | Public | Global | `instructions.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/instructions` | `POST` | Optional JWT | Authenticated | Global | `instructions.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/instructions/{instruction_id}` | `GET` | None / Public | Public | Global | `instructions.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/instructions/{instruction_id}` | `DELETE` | Optional JWT | Authenticated | Global | `instructions.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sessions/start` | `POST` | Optional JWT | Authenticated | Global | `sessions.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sessions` | `POST` | Optional JWT | Authenticated | Global | `sessions.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sessions/{session_id}` | `GET` | Optional JWT | Authenticated | Global | `sessions.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/events` | `POST` | Optional JWT | Authenticated | Global | `learning.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/events/batch` | `POST` | Optional JWT | Authenticated | Global | `learning.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/events` | `GET` | Optional JWT | Authenticated | Global | `learning.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/events/{event_id}` | `GET` | Optional JWT | Authenticated | Global | `learning.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/events/replay` | `POST` | Optional JWT | Authenticated | Global | `learning.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/learning/recommendations/{student_id}` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `learning.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/assessments/items` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/items` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/items/{item_id}` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/{assessment_id}` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/{assessment_id}/sanitized` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/{assessment_id}/publish` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/assignments` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/assignments` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/start` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}/adaptive-next` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}/submit` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}` | `GET` | None / Public | Public | Global | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/student/{student_id}` | `GET` | None / Public | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `assessments.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}/teacher-review` | `POST` | None / Public | TEACHER, ADMIN | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}/review` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/attempts/{attempt_id}/reassess` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/assessments/submit` | `POST` | None / Public | Public | Global | `assessments.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/v1/rag/sources` | `POST` | Bearer JWT | Authenticated Principal | Global | `rag.py` | YES | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources` | `GET` | Bearer JWT | Authenticated Principal | Global | `rag.py` | NO | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}` | `GET` | Bearer JWT | Authenticated Principal | Global | `rag.py` | NO | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}/ingest` | `POST` | Bearer JWT | Authenticated Principal | Global | `rag.py` | YES | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}/validate` | `POST` | Bearer JWT | Authenticated Principal | Global | `rag.py` | YES | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}/publish` | `POST` | Bearer JWT | Authenticated Principal | Global | `rag.py` | YES | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}/chunks` | `GET` | Bearer JWT | Authenticated Principal | Global | `rag.py` | NO | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/sources/{source_id}` | `DELETE` | Bearer JWT | Authenticated Principal | Global | `rag.py` | YES | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/rag/query` | `POST` | Bearer JWT | Authenticated Principal | Global | `rag.py` | Telemetry / Audit | NO | Fail-Closed RAG_EMPTY / CurricDirect | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/ai/status` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/execute` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | Telemetry / Audit | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/providers` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/providers` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/providers/{provider_name}/toggle` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/killswitch` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/route` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/observability/metrics` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/observability/logs` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/budgets` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/budgets` | `PUT` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/circuit-breakers` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/circuit-breakers/{provider_name}/reset` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/allowlist` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/allowlist` | `POST` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/allowlist/{model_name}` | `DELETE` | None / Public | Authenticated Principal | Global | `ai.py` | YES | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/ai/governance/cost-breakdown` | `GET` | None / Public | Authenticated Principal | Global | `ai.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/api/v1/analytics/student/{student_id}` | `GET` | Optional JWT | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `analytics.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/analytics/cohort/{cohort_id}` | `GET` | Optional JWT | Authenticated | Tenant Organization | `analytics.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/analytics/class` | `GET` | Optional JWT | Authenticated | Tenant Organization | `analytics.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/analytics/system` | `GET` | Optional JWT | Authenticated | Global | `analytics.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/analytics/ai` | `GET` | Optional JWT | Authenticated Principal | Global | `analytics.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications` | `GET` | Optional JWT | Authenticated | Global | `notifications.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications` | `POST` | Optional JWT | Authenticated | Global | `notifications.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/batch` | `POST` | Optional JWT | Authenticated | Global | `notifications.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/{notification_id}/status` | `GET` | Optional JWT | Authenticated | Global | `notifications.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/{notification_id}/read` | `POST` | Optional JWT | Authenticated | Global | `notifications.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/read-all` | `POST` | Optional JWT | Authenticated | Global | `notifications.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/process-queue` | `POST` | Optional JWT | Authenticated | Global | `notifications.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/notifications/queue/stats` | `GET` | Optional JWT | Authenticated | Global | `notifications.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sync/events` | `POST` | Optional JWT | Authenticated | Global | `sync.py` | YES | NO (Internal SQLite DB) | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sync/status` | `GET` | Optional JWT | Authenticated | Global | `sync.py` | NO | NO (Internal SQLite DB) | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sync/devices/bind` | `POST` | Optional JWT | Authenticated | Global | `sync.py` | YES | NO (Internal SQLite DB) | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/sync/devices` | `GET` | Optional JWT | Authenticated | Global | `sync.py` | NO | NO (Internal SQLite DB) | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/tools` | `GET` | Optional JWT | Authenticated | Global | `tools.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/tools/{course_id}` | `GET` | Optional JWT | Authenticated | Enrolled Student / Offering Org / Public | `tools.py` | NO | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/tools/execute` | `POST` | Optional JWT | Authenticated | Global | `tools.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/api/v1/tutor/turn` | `POST` | Bearer JWT | Authenticated | Global | `tutor.py` | YES | NO | None (Fail Closed) | 400, 401, 403, 404, 500 | VERIFIED |
| `/healthz` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | 503 UNHEALTHY | 503 on degraded | VERIFIED |
| `/readyz` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/livez` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/api/v1/health` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | 503 UNHEALTHY | 503 on degraded | VERIFIED |
| `/api/health` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | 503 UNHEALTHY | 503 on degraded | VERIFIED |
| `/api/teacher/dashboard` | `GET` | None / Public | TEACHER, ADMIN | Global | `app.py` | NO | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/teacher/instructions` | `GET` | None / Public | TEACHER, ADMIN | Global | `app.py` | NO | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/instruction` | `POST` | None / Public | Public | Global | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/teacher/instruction` | `POST` | None / Public | TEACHER, ADMIN | Global | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/instruction/toggle` | `POST` | None / Public | Public | Global | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/teacher/alert/resolve` | `POST` | None / Public | TEACHER, ADMIN | Global | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/alert/resolve` | `POST` | None / Public | Public | Global | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/student/snapshot` | `POST` | None / Public | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `app.py` | YES | NO | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/api/sync/events` | `POST` | None / Public | Public | Global | `app.py` | YES | NO (Internal SQLite DB) | Central Platform Services | 400, 404, 500 | VERIFIED |
| `/` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/portal` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/teacher` | `GET` | None / Public | TEACHER, ADMIN | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/admin/portal` | `GET` | None / Public | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/admin` | `GET` | None / Public | SUPER_ADMIN, ORG_ADMIN | Tenant Org / Global System | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/student/dashboard` | `GET` | None / Public | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/student` | `GET` | None / Public | STUDENT, TEACHER, ADMIN | Student Principal / Linked Parent / Org Teacher | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/interactive` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/tutor` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/gai3.ico` | `GET` | None / Public | Authenticated Principal | Global | `app.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/favicon.ico` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |
| `/gai3.png` | `GET` | None / Public | Authenticated Principal | Global | `app.py` | NO | Provider LLM / Local GGUF | Fail-Closed (Mock rejected in prod) | 400, 404, 500 | VERIFIED |
| `/marked.min.js` | `GET` | None / Public | Public | Global | `app.py` | NO | NO | None (Fail Closed) | 400, 404, 500 | VERIFIED |

---

## Architecture Compliance & Divergence Audit

1. **Single Production Entrypoint**: Verified that `central_platform.api.server` and `central_platform.api.app` serve as the canonical application runtime.
2. **Zero Reverse Dependencies**: `central_platform` contains 0 imports from root `server.py`.
3. **Production Backdoors Gated**: `/api/v1/auth/demo-tokens` strictly gated against production execution.
4. **Silent Exception Auditing**: No bare `except: pass` blocks in active production request flows.
