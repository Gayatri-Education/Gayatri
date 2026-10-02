# Phase 17 Implementation Plan: Student Multi-Course Workflow UI

**Document:** `docs/reports/PHASE_17_PLAN.md`  
**Phase:** 17  
**Status:** IN_PROGRESS  
**Target:** Student Multi-Course Workflow UI, Course Selector, Active Course Context, Scoped Curriculum, Scoped Assignments, Scoped Knowledge, Safe Switching, and Progress per Course  

---

## 1. Architectural Scope & Objectives

Section 12.17 of the Master Plan mandates:
- **My Courses**: Comprehensive listing of enrolled courses for a student across all active enrollments.
- **Course Selector**: Dynamic UI control allowing instant course switching with active context preservation.
- **Active Course Context**: Every session launch, tutor turn, RAG retrieval, and progress query explicitly binds `course_id`. Zero default fallback to chemistry.
- **Module/Topic/Concept Navigation**: Curriculum rendered dynamically per course DAG/tree with concept mastery heatmaps.
- **Assignments per Course**: Strict isolation of assignments (course A assignments never leak into course B).
- **Course Knowledge & Notes**: RAG documents, class notes, and targeted remedial content scoped strictly to active course, class group, and student.
- **Safe Course Switching Invariant**: Students cannot switch courses while an AI turn is generating unless the session cancellation/transition path is safely handled.
- **Progress & Mastery per Course**: Authoritative SLR mastery and misconception tracking completely isolated by course.
- **Offline Indicators**: Real-time display of local cache and sync status for the active course.

---

## 2. Component Modifications

### 2.1 Database Layer (`central_platform/db.py`)
- `get_assignments_for_student(student_id: str, course_id: str) -> List[Assignment]`
- `get_knowledge_sources_for_student(student_id: str, course_id: str) -> List[RAGSource]`

### 2.2 Schemas & REST API (`central_platform/api/schemas.py`, `central_platform/api/routes/students.py`)
- Schemas:
  - `StudentEnrolledCourseResponse`
  - `StudentCourseCurriculumResponse`
  - `StudentCourseSwitchRequest`, `StudentCourseSwitchResponse`
  - `StudentOfflineStatusResponse`
- Endpoints on `/api/v1/students/{student_id}`:
  - `GET /courses`
  - `GET /courses/{course_id}/curriculum`
  - `GET /courses/{course_id}/assignments`
  - `GET /courses/{course_id}/knowledge`
  - `POST /courses/switch`
  - `GET /courses/{course_id}/offline-status`

### 2.3 Student Portal Controller (`app/portals/student/controller.py`)
- Full rewrite integrating `PlatformDatabase`, `CourseService`, `CurriculumService`, `RAGService`, and `SLRService`.
- Methods for enrolled courses, curriculum navigation, assignments, knowledge, safe switching, and offline status.

### 2.4 Desktop Bridge Facade (`app/bridge/facade.py`)
- PySide6 slots:
  - `get_student_courses`
  - `switch_student_course`
  - `get_student_course_curriculum`
  - `get_student_course_assignments`
  - `get_student_course_knowledge`
  - `get_student_course_offline_status`

### 2.5 Student Dashboard UI (`app/ui/student_dashboard.html`)
- Header course switcher dropdown with change event listeners.
- Active course metadata and offline sync indicator pill.
- Scoped curriculum, assignment, and knowledge rendering.
- Frontend lock preventing course change while turn is generating.

---

## 3. Verification & Acceptance Criteria
- 12 comprehensive unit and integration tests in `tests/test_phase17_student_multi_course_workflow_ui.py`.
- 1 student enrolled in 3 courses (Mathematics, Physics, Chemistry).
- 100% green pass on regression suite (1,029 + 12 = 1,041 tests).
- All reports, state files, and sync queue updated.
- Git commit and push to `origin/master`.
