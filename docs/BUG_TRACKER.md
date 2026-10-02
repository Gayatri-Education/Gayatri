# Bug Tracker

Track all known bugs across the system here.

## Phase 22 Bugs — All Fixed (2026-10-02)

| ID | Severity | File | Description | Status |
|----|----------|------|-------------|--------|
| BUG-A | CRITICAL | `api/routes/courses.py` | `list_courses` created guest User with `SUPER_ADMIN` role when unauthenticated — privilege escalation | ✅ FIXED |
| BUG-B | HIGH | `api/routes/courses.py` | `get_course_review_queue` created unauthenticated `ORG_ADMIN` actor | ✅ FIXED |
| BUG-C | HIGH | `api/routes/tutor.py` | No prompt injection sanitization before LLM forwarding in `/tutor/turn` | ✅ FIXED |
| BUG-D | CRITICAL | `api/routes/rag.py` | All RAG write endpoints (POST /sources, /ingest, /validate, /publish, DELETE) had zero authentication | ✅ FIXED |
| BUG-E | HIGH | `api/routes/rag.py`, `courses.py` | Role enum values are lowercase (`'teacher'`) but RBAC checks used uppercase (`'TEACHER'`) — all checks silently failed | ✅ FIXED |

*All active bugs resolved. No open bugs.*
