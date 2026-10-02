# Phase 17 Test Report: Student Multi-Course Workflow UI

**Document:** `docs/reports/PHASE_17_TEST_REPORT.md`  
**Phase:** 17  
**Module:** Student Multi-Course Workflow UI, Course Selector, Active Course Context, Scoped Curriculum, Scoped Assignments, Scoped Knowledge, Safe Switching, and Progress per Course  
**Status:** PASSED (12/12 Phase 17 tests passed; 100% full regression pass)  
**Execution Timestamp:** 2026-10-02T10:15:00+05:30  

---

## 1. Executive Summary

Phase 17 delivers the complete **Student Multi-Course Workflow UI** implementation in compliance with Section 12.17 of the Master Plan (`GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`).

Key deliverables verified:
- **My Courses Listing**: Authoritative endpoint and controller querying active enrollments, course metadata, cohort, class group, live SLR mastery, and current active concept.
- **Dynamic Course Selector**: PySide6 Desktop Bridge slots and frontend HTML header control enabling instantaneous course switching with persistent state preservation.
- **Strict Active Course Context**: Explicit scoping across all session starts, curriculum views, tutor turns, and RAG operations with zero fallback to hardcoded default courses.
- **Module/Topic/Concept Navigation**: Curriculum rendered per course DAG/tree with concept mastery heatmaps dynamically overlaid from student learning records.
- **Assignments per Course**: Strict boundary enforcement ensuring assignments for Course A never leak into Course B, and class group assignments remain strictly partitioned.
- **Course Knowledge & Remedial Notes**: RAG documents, class notes, and remedial content scoped strictly to active course, class group, and student targets.
- **Safe Course Switching Invariant**: Concurrency guard preventing course switching while an AI turn is generating (HTTP 409 Conflict / Bridge error).
- **Progress & Mastery per Course**: Completely partitioned BKT/SLR mastery states per course.
- **Offline Indicators**: Real-time display of local cache and sync status for the active course.

---

## 2. Test Execution Breakdown

All 12 tests in `tests/test_phase17_student_multi_course_workflow_ui.py` passed with 100% success rate:

| Test ID | Test Name | Target Layer | Result |
|---|---|---|---|
| TC-17-01 | `test_student_enrolled_courses_listing` | Database & REST API | **PASSED** |
| TC-17-02 | `test_student_course_selector_default_and_context` | StudentPortalController | **PASSED** |
| TC-17-03 | `test_student_course_switching_active_context_preservation` | Controller & REST API | **PASSED** |
| TC-17-04 | `test_safe_course_switching_invariant_turn_generating_blocked` | Concurrency & Validation | **PASSED** |
| TC-17-05 | `test_course_switching_unauthorized_course_rejected` | Security & Boundaries | **PASSED** |
| TC-17-06 | `test_scoped_curriculum_navigation_per_course` | Curriculum & SLR Overlay | **PASSED** |
| TC-17-07 | `test_scoped_assignments_isolation_per_course` | Database & REST API | **PASSED** |
| TC-17-08 | `test_scoped_assignments_class_group_boundary` | Class Group Boundary | **PASSED** |
| TC-17-09 | `test_scoped_knowledge_sources_and_remedial_notes` | RAG & Targeting Boundary | **PASSED** |
| TC-17-10 | `test_offline_status_and_caching_indicator` | Offline & Sync Indicator | **PASSED** |
| TC-17-11 | `test_desktop_bridge_facade_student_multi_course_slots` | PySide6 Desktop Bridge | **PASSED** |
| TC-17-12 | `test_student_dashboard_html_structure_and_controls` | UI DOM & JS Controller | **PASSED** |

---

## 3. Files Created & Modified

1. **`central_platform/db.py`**:
   - Added `get_assignments_for_student(student_id, course_id)`.
   - Added `get_knowledge_sources_for_student(student_id, course_id)`.
   - Added `get_mastery_states(student_id, course_id)`.
2. **`central_platform/api/schemas.py`**:
   - Added `StudentEnrolledCourseResponse`, `StudentCourseSwitchRequest`, `StudentCourseSwitchResponse`, `StudentOfflineStatusResponse`.
3. **`central_platform/api/routes/students.py`**:
   - Added `GET /{student_id}/courses`.
   - Added `GET /{student_id}/courses/{course_id}/curriculum`.
   - Added `GET /{student_id}/courses/{course_id}/assignments`.
   - Added `GET /{student_id}/courses/{course_id}/knowledge`.
   - Added `POST /{student_id}/courses/switch` (with HTTP 409 safe-switching guard).
   - Added `GET /{student_id}/courses/{course_id}/offline-status`.
4. **`app/portals/student/controller.py`**:
   - Full rewrite with multi-course workflows, active course tracking, and safe switching checks.
5. **`app/bridge/facade.py`**:
   - Added student controller singleton and reset helper.
   - Added PySide6 slots: `get_student_courses`, `switch_student_course`, `get_student_course_curriculum`, `get_student_course_assignments`, `get_student_course_knowledge`, `get_student_course_offline_status`.
6. **`app/ui/student_dashboard.html`**:
   - Integrated dynamic course switcher dropdown, sync status badge, and JavaScript multi-course handlers.
7. **`tests/test_phase17_student_multi_course_workflow_ui.py`**:
   - 12 comprehensive unit and integration tests.
