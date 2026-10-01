# Data Model & Schema Target Specification — Gayatri Platform

**Document:** `docs/DATA_MODEL_TARGET.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** FROZEN (Phase 1 Deliverable)  
**Governing Plan:** `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## 1. High-Level Entity Relationship Model

```text
Platform
└── Organization (Tenants)
    ├── Users (Admins, Teachers, Students, Parents)
    │   └── Roles & Permissions
    │
    ├── Course Offerings (Pinned version per organization)
    │   └── Course (PUBLIC or PRIVATE)
    │       ├── Course Versions (Immutable once PUBLISHED)
    │       │   ├── Curriculum (CurriculumVersion)
    │       │   │   └── Subjects
    │       │   │       └── Modules
    │       │   │           └── Topics
    │       │   │               └── Concepts
    │       │   │                   └── Prerequisites (DAG)
    │       │   ├── Knowledge Sources (RAG Sources & Chunks)
    │       │   ├── Assessments & Item Bank
    │       │   ├── Course Tool Policy (Enabled tools per course)
    │       │   └── Course Tutor Policy (Pedagogical parameters)
    │       │
    │       └── Enrollments (Student -> Course Offering)
    │
    └── Classes / Cohorts (Class Groups)
        ├── Assigned Teachers
        ├── Enrolled Students
        ├── Class-Scoped Teacher Notes
        └── Class-Scoped Teacher Instructions
```

---

## 2. Core Identities & Composite Keys

### 2.1 Learning Identity
$$\text{Learning Identity} = (\text{student\_id}, \text{course\_id}, \text{course\_version\_id}, \text{concept\_id})$$
- Mastery is strictly namespaced. A student learning "Force" in Physics maintains an independent mastery record from "Force" in Mathematics or Engineering.
- Concept IDs follow a deterministic, version-aware pattern:
  `course:<course_id>:version:<version_id>:concept:<stable_key>`

### 2.2 Content Authorization Key
$$\text{Content Authorization} = (\text{org\_id}, \text{course\_id}, \text{course\_version\_id}, \text{class\_id}, \text{student\_id}, \text{visibility\_scope}, \text{publication\_status})$$
- Content is visible to students ONLY if `publication_status == 'PUBLISHED'` and the student's enrollment matches the scope.

### 2.3 AI Context Identity
$$\text{Context Identity} = (\text{org\_id}, \text{student\_id}, \text{enrollment\_id}, \text{course\_id}, \text{course\_version\_id}, \text{class\_id}, \text{concept\_id}, \text{active\_instructions}, \text{allowed\_knowledge}, \text{allowed\_tools})$$

---

## 3. Enumerations & Value Types

### 3.1 Course Visibility
- `PUBLIC`: Discoverable and selectable by any registered organization. Content is shared at the course level, but student data, mastery, class notes, and instructions remain strictly isolated per organization.
- `PRIVATE`: Restricted exclusively to the creating organization. Cross-organization access is strictly forbidden (HTTP 403).

### 3.2 Content Lifecycle Status
- `DRAFT`: Content uploaded, undergoing validation.
- `PROCESSING`: Text extraction, cleaning, and chunking active.
- `READY_FOR_REVIEW`: Indexing complete, awaiting administrative approval.
- `PUBLISHED`: Approved by administrator; immutable; retrievable by authorized students.
- `ARCHIVED`: Deprecated; retrievable only by historical sessions pinned to this version.
- `FAILED`: Ingestion failed; accompanied by structured diagnostic error code.

### 3.3 Content Types & Audience Scope
- **Content Types:** `TEXTBOOK`, `REFERENCE`, `TEACHER_NOTE`, `WORKSHEET`, `REMEDIAL`, `ASSESSMENT_SOURCE`, `SOLUTION_GUIDE`, `ANNOUNCEMENT`, `OTHER`.
- **Visibility Scopes:**
  - `ORGANIZATION`: All users within the organization.
  - `COURSE`: All students enrolled in the active course version.
  - `CLASS`: Strictly students enrolled in the specified `class_id`.
  - `STUDENT`: Strictly students specified in `student_ids`.

---

## 4. Relational Database Schema (PostgreSQL & SQLite Unified)

### 4.1 Organizations & Multi-Tenancy
```sql
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    domain TEXT DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL, -- super_admin, org_admin, teacher, student, parent
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(org_id, email)
);
```

### 4.2 Courses & Course Offerings
```sql
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    owner_org_id TEXT NOT NULL REFERENCES organizations(id),
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    visibility TEXT NOT NULL DEFAULT 'PRIVATE', -- PUBLIC, PRIVATE
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(owner_org_id, code)
);

CREATE TABLE IF NOT EXISTS course_versions (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES courses(id),
    version_number TEXT NOT NULL, -- e.g. "1.0", "1.1"
    status TEXT NOT NULL DEFAULT 'DRAFT', -- DRAFT, PROCESSING, READY_FOR_REVIEW, PUBLISHED, ARCHIVED, FAILED
    tool_policy TEXT NOT NULL DEFAULT '{}', -- JSON: allowed tools
    tutor_policy TEXT NOT NULL DEFAULT '{}', -- JSON: pedagogy params
    checksum TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES users(id),
    published_by TEXT REFERENCES users(id),
    created_at TEXT NOT NULL,
    published_at TEXT,
    UNIQUE(course_id, version_number)
);

CREATE TABLE IF NOT EXISTS organization_course_offerings (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    pinned_version_id TEXT NOT NULL REFERENCES course_versions(id),
    is_active INTEGER NOT NULL DEFAULT 1,
    enrolled_at TEXT NOT NULL,
    UNIQUE(org_id, course_id)
);
```

### 4.3 Generic Curriculum Hierarchy
```sql
CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    course_version_id TEXT NOT NULL REFERENCES course_versions(id),
    title TEXT NOT NULL,
    code TEXT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(id),
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL REFERENCES modules(id),
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY, -- course:<c>:version:<v>:concept:<key>
    topic_id TEXT NOT NULL REFERENCES topics(id),
    stable_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    difficulty_level INTEGER NOT NULL DEFAULT 1, -- 1 to 5
    order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS prerequisites (
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    prerequisite_concept_id TEXT NOT NULL REFERENCES concepts(id),
    PRIMARY KEY (concept_id, prerequisite_concept_id)
);
```

### 4.4 Classes & Enrollments
```sql
CREATE TABLE IF NOT EXISTS class_groups (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(org_id, code)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES users(id),
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_offering_id TEXT NOT NULL REFERENCES organization_course_offerings(id),
    class_id TEXT REFERENCES class_groups(id),
    is_active INTEGER NOT NULL DEFAULT 1,
    enrolled_at TEXT NOT NULL,
    UNIQUE(student_id, course_offering_id)
);
```

### 4.5 Course-Scoped Learning State & Events
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES users(id),
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    course_version_id TEXT NOT NULL REFERENCES course_versions(id),
    class_id TEXT REFERENCES class_groups(id),
    mode TEXT NOT NULL DEFAULT 'tutor',
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS learning_events (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    course_version_id TEXT NOT NULL REFERENCES course_versions(id),
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    event_type TEXT NOT NULL, -- ATTEMPT, HINT_REQUEST, EXPLANATION, MISCONCEPTION, MASTERY_UPDATE
    accuracy REAL,
    hint_penalty REAL DEFAULT 0.0,
    payload TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_concept_mastery (
    student_id TEXT NOT NULL REFERENCES users(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    course_version_id TEXT NOT NULL REFERENCES course_versions(id),
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    mastery REAL NOT NULL DEFAULT 0.0,
    confidence REAL NOT NULL DEFAULT 0.0,
    consecutive_successes INTEGER NOT NULL DEFAULT 0,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    last_reviewed_at TEXT,
    next_review_due TEXT,
    learning_status TEXT NOT NULL DEFAULT 'NEW', -- NEW, IN_PROGRESS, MASTERED, NEEDS_REVIEW
    updated_at TEXT NOT NULL,
    PRIMARY KEY(student_id, course_id, concept_id)
);
```

### 4.6 Scoped Knowledge Assets & RAG
```sql
CREATE TABLE IF NOT EXISTS knowledge_assets (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    course_version_id TEXT NOT NULL REFERENCES course_versions(id),
    content_type TEXT NOT NULL, -- TEXTBOOK, TEACHER_NOTE, REMEDIAL, etc.
    visibility_scope TEXT NOT NULL, -- ORGANIZATION, COURSE, CLASS, STUDENT
    target_class_id TEXT REFERENCES class_groups(id),
    target_student_ids TEXT DEFAULT '[]', -- JSON array of student IDs
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_checksum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT', -- DRAFT, PROCESSING, READY_FOR_REVIEW, PUBLISHED, ARCHIVED, FAILED
    uploaded_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES knowledge_assets(id),
    org_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    course_version_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    visibility_scope TEXT NOT NULL,
    target_class_id TEXT,
    target_student_ids TEXT DEFAULT '[]',
    concept_id TEXT,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_vector BLOB,
    checksum TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 4.7 Hierarchical Teacher Instructions
```sql
CREATE TABLE IF NOT EXISTS teacher_instructions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    course_version_id TEXT REFERENCES course_versions(id),
    class_id TEXT REFERENCES class_groups(id),
    student_id TEXT REFERENCES users(id),
    session_id TEXT REFERENCES sessions(id),
    scope_type TEXT NOT NULL, -- ORGANIZATION, COURSE, CLASS, STUDENT, SESSION
    priority INTEGER NOT NULL DEFAULT 100,
    instruction_text TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);
```

### 4.8 Offline Sync Outbox
```sql
CREATE TABLE IF NOT EXISTS sync_outbox (
    id TEXT PRIMARY KEY, -- operation_id / event_id
    device_id TEXT NOT NULL,
    entity_type TEXT NOT NULL, -- learning_event, session, assessment_attempt
    entity_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, IN_FLIGHT, SYNCED, FAILED
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL,
    synced_at TEXT
);
```

---

## 5. Canonical Python Dataclass Contracts

### 5.1 `CourseModel` & `CourseVersionModel`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class CourseVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

class ContentStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"

@dataclass(frozen=True)
class CourseModel:
    id: str
    owner_org_id: str
    code: str
    title: str
    description: str = ""
    visibility: CourseVisibility = CourseVisibility.PRIVATE
    is_active: bool = True
    created_at: str = ""

@dataclass(frozen=True)
class CourseVersionModel:
    id: str
    course_id: str
    version_number: str
    status: ContentStatus
    tool_policy: Dict[str, bool] = field(default_factory=dict)
    tutor_policy: Dict[str, any] = field(default_factory=dict)
    checksum: str = ""
    created_by: str = ""
    published_by: Optional[str] = None
    created_at: str = ""
    published_at: Optional[str] = None
```

### 5.2 `CanonicalLearningState` (Course-Scoped)
```python
@dataclass
class CanonicalLearningState:
    student_id: str
    org_id: str
    course_id: str
    course_version_id: str
    concept_mastery: Dict[str, float] = field(default_factory=dict)
    concept_confidence: Dict[str, float] = field(default_factory=dict)
    misconceptions: List[Dict[str, any]] = field(default_factory=list)
    recent_events: List[Dict[str, any]] = field(default_factory=list)
    due_reviews: List[str] = field(default_factory=list)
    active_teacher_instructions: List[str] = field(default_factory=list)
    last_updated: str = ""
```
