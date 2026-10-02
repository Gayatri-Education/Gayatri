# Phase 16 Implementation Plan: Teacher Workflow UI

**Document:** `docs/reports/PHASE_16_PLAN.md`  
**Phase:** 16  
**Status:** COMPLETED  
**Target:** Teacher Workflow UI, Class Management, Class Notes, Remedial Content, Scoped Instructions, Assignments, and Real Progress Review  

---

## 1. Architectural Scope & Objectives

Section 12.16 of the Master Plan mandates:
- **Course & Class Selection**: Real course selection and class group management scoped to teacher's organization.
- **Textbook & Content Upload**: Course-level material ingestion into RAG pipeline.
- **Class Note Upload**: Class-scoped notes (`visibility_scope="class"`, `class_id=...`) visible strictly to students in that class.
- **Student Selection**: Roster resolution restricted to authorized students enrolled in teacher's classes. Arbitrary student selection outside authorized scope is denied with HTTP 403 Forbidden.
- **Remedial Content Upload**: Remedial material targeted to specific student IDs (`visibility_scope="student_targeted"`, `target_student_ids=[...]`) visible strictly to selected students.
- **Instruction Composer**: Multilevel instruction composition (`COURSE`, `CLASS`, `STUDENT`) with priority, expiration, and invariant validation.
- **Assignment Creation**: Real assignment distribution to classes/cohorts persisted to `assignments` table (eliminating hardcoded chemistry mock records).
- **Student Progress Review**: Authoritative SLR-backed mastery and misconception review with honest empty states (zero fake demo rosters).
- **Reload Durability**: All state persisted to SQLite / `PlatformDatabase` and surviving process restart.

---

## 2. Component Modifications

### 2.1 Database Extensions (`central_platform/db.py`)
- `get_class_group(class_id: str) -> Optional[ClassGroup]`
- `list_class_groups_by_organization(organization_id: str) -> List[ClassGroup]`
- `list_class_groups_by_course(course_id: str, organization_id: Optional[str] = None) -> List[ClassGroup]`
- `get_students_for_class_group(class_id: str) -> List[User]`
- `get_teacher_courses(teacher_id: str, organization_id: Optional[str] = None) -> List[Course]`
- `get_assigned_student_ids_for_teacher(teacher_id: str) -> Set[str]` (strictly scoped to teacher's organization and assigned classes/courses)
- `list_assignments(...)`: enhance with `class_group_id` filtering and real entity mapping.

### 2.2 API Routes & Schemas (`central_platform/api/schemas.py`, `central_platform/api/routes/teachers.py`)
- Schemas:
  - `ClassGroupCreateRequest`, `ClassGroupResponse`
  - `ClassNoteCreateRequest`, `ClassNoteResponse`
  - `RemedialContentCreateRequest`, `RemedialContentResponse`
  - `TeacherAssignmentCreateRequest`, `TeacherAssignmentResponse`
- Endpoints on `/api/v1/teachers`:
  - `GET /courses`
  - `GET /classes`
  - `POST /classes`
  - `GET /classes/{class_id}/students`
  - `POST /classes/{class_id}/notes`
  - `POST /remedial-content`
  - `POST /assignments`
  - `GET /assignments` (backed by real database)
  - Validation: 403 Forbidden on unauthorized student or class selection.

### 2.3 RAG Retrieval Scoping (`central_platform/rag/service.py`)
- Ensure vector and keyword retrieval honor `class_id` and `student_id` filters without cross-tenant or cross-class leakage.

### 2.4 Teacher Portal Controller (`app/portals/teacher/controller.py`)
- Real DB queries for dashboard metrics (no hardcoded `"enrolled_count": 24`, `"average_mastery_pct": 76`).
- Methods for classes, class notes, remedial content, assignments, and student progress.

### 2.5 Desktop Bridge & Web UI (`app/bridge/facade.py`, `app/ui/teacher_portal.html`)
- Remove hardcoded `"crs-chem-101"` defaults from facade.
- Add bridge slots and UI controls for class selection, class note uploading, remedial targeting, instruction composer, and assignment creation.

---

## 3. Verification & Acceptance Criteria
- 12 comprehensive unit and integration tests in `tests/test_phase16_teacher_workflow_ui.py`.
- 100% green pass on regression suite (1,017 + 12 = 1,029 tests).
- All reports, state files, and sync queue updated.
- Git commit and push to `origin/master`.
