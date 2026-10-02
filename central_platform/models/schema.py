"""Platform schema models for multi-organization RBAC and core domain entities.

Master Plan Section 12 Entity Specifications.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    COURSE_ADMIN = "course_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().lower()
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)


class CurriculumBoard(str, Enum):
    NCERT = "ncert"
    CBSE = "cbse"
    ICSE = "icse"
    STATE_BOARD = "state_board"
    COLLEGE = "college"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AssessmentType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    ADAPTIVE = "adaptive"
    REASSESSMENT = "reassessment"
    ASSIGNMENT = "assignment"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().lower()
            if val_norm.startswith("assessmenttype."):
                val_norm = val_norm.split(".", 1)[1]
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)


# ── 1. Organizations & Identity ──────────────────────────────────────────

@dataclass
class Organization:
    id: str
    name: str
    slug: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class User:
    id: str
    email: str
    full_name: str
    role: UserRole
    organization_id: Optional[str] = None
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["role"] = self.role.value if isinstance(self.role, UserRole) else str(self.role)
        return d


@dataclass
class Role:
    id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Permission:
    id: str
    code: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 2. Academic Curriculum Hierarchy ────────────────────────────────────

class CourseVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().upper()
            for member in cls:
                if member.value == val_norm or member.name == val_norm:
                    return member
        return super()._missing_(value)


class CourseStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().upper()
            for member in cls:
                if member.value == val_norm or member.name == val_norm:
                    return member
        return super()._missing_(value)


@dataclass
class CourseToolPolicy:
    calculator: bool = False
    graphing: bool = False
    code_execution: bool = False
    equation_balancer: bool = False
    periodic_table: bool = False
    custom_tools: Dict[str, bool] = field(default_factory=dict)

    def is_tool_enabled(self, tool_name: str) -> bool:
        if tool_name in self.custom_tools:
            return self.custom_tools[tool_name]
        return getattr(self, tool_name, False)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> CourseToolPolicy:
        if not data:
            return cls()
        known = {k: bool(v) for k, v in data.items() if k in {"calculator", "graphing", "code_execution", "equation_balancer", "periodic_table"}}
        custom = {k: bool(v) for k, v in data.items() if k not in known}
        return cls(**known, custom_tools=custom)


@dataclass
class CoursePolicy:
    allow_cloud_fallback: bool = True
    strict_prerequisites: bool = True
    max_hints_per_concept: int = 3
    remediation_threshold: float = 0.5
    custom_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> CoursePolicy:
        if not data:
            return cls()
        known = {k: v for k, v in data.items() if k in {"allow_cloud_fallback", "strict_prerequisites", "max_hints_per_concept", "remediation_threshold"}}
        custom = {k: v for k, v in data.items() if k not in known}
        return cls(**known, custom_rules=custom)


@dataclass
class CourseVersion:
    id: str
    course_id: str
    version_number: str = "1.0"
    status: CourseStatus = CourseStatus.DRAFT
    tool_policy: CourseToolPolicy = field(default_factory=CourseToolPolicy)
    tutor_policy: CoursePolicy = field(default_factory=CoursePolicy)
    checksum: str = ""
    created_by: str = ""
    published_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None
    is_deleted: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, CourseStatus) else str(self.status)
        return d


@dataclass
class OrganizationCourseOffering:
    id: str
    organization_id: str
    course_id: str
    pinned_version_id: Optional[str] = None
    is_active: bool = True
    enrolled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


CourseOffering = OrganizationCourseOffering


@dataclass
class Course:
    id: str
    organization_id: str
    code: str
    title: str
    description: str = ""
    visibility: CourseVisibility = CourseVisibility.PRIVATE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["visibility"] = self.visibility.value if isinstance(self.visibility, CourseVisibility) else str(self.visibility)
        return d



@dataclass
class Subject:
    id: str
    course_id: str
    name: str
    code: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Curriculum:
    id: str
    course_id: str
    title: str
    board: CurriculumBoard = CurriculumBoard.CUSTOM
    version: str = "1.0.0"
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CurriculumVersion:
    id: str
    curriculum_id: str
    version_num: str
    change_log: str = ""
    status: str = "draft"
    published_at: Optional[str] = None
    schema_data: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Module:
    id: str
    curriculum_id: str
    title: str
    sequence_order: int = 1
    subject_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Topic:
    id: str
    module_id: str
    title: str
    sequence_order: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Concept:
    id: str
    topic_id: str
    name: str
    description: str = ""
    difficulty: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Prerequisite:
    prerequisite_concept_id: str
    dependent_concept_id: str

    def to_dict(self) -> dict:
        return asdict(self)


# ── 3. Class Groups & Enrollments ────────────────────────────────────────

@dataclass
class ClassGroup:
    id: str
    organization_id: str
    course_id: str
    name: str
    section: str = "A"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Cohort:
    id: str
    class_group_id: str
    name: str
    academic_year: str = "2026-2027"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Enrollment:
    id: str
    student_id: str
    course_id: str
    cohort_id: Optional[str] = None
    enrolled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CourseLearningContext:
    """Authoritative scoped context binding a student to a specific course and version."""
    student_id: str
    course_id: str
    organization_id: Optional[str] = None
    course_version_id: Optional[str] = None
    course_offering_id: Optional[str] = None
    cohort_id: Optional[str] = None
    class_id: Optional[str] = None

    def validate(self) -> None:
        if not self.student_id or not str(self.student_id).strip():
            raise ValueError("CourseLearningContext requires a non-empty student_id.")
        if not self.course_id or not str(self.course_id).strip():
            raise ValueError("CourseLearningContext requires a non-empty course_id.")

    def to_dict(self) -> dict:
        return asdict(self)


# ── 4. Sessions & Granular Telemetry ─────────────────────────────────────

@dataclass
class Session:
    id: str
    student_id: str
    course_id: str
    concept_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: Optional[str] = None
    course_version_id: Optional[str] = None
    course_offering_id: Optional[str] = None
    class_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, SessionStatus) else str(self.status)
        return d


@dataclass
class LearningEvent:
    id: str
    session_id: str
    student_id: str
    concept_id: str = ""
    event_type: str = "question_attempted"
    organization_id: Optional[str] = None
    course_id: Optional[str] = None
    course_version_id: Optional[str] = None
    source: str = "student_desktop"
    payload: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    schema_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def event_id(self) -> str:
        return self.id

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_id"] = self.id
        return d



# ── 5. Student Learning Records & Mastery ────────────────────────────────

@dataclass
class StudentLearningRecord:
    id: str
    student_id: str
    course_id: str
    authoritative: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MasteryState:
    id: str = ""
    slr_id: str = ""
    concept_id: str = ""
    score: float = 0.5
    confidence: float = 0.8
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_practiced_at: Optional[str] = None
    state: str = "practicing"
    p_mastery: Optional[float] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"ms_{uuid.uuid4().hex[:8]}"
        if self.p_mastery is not None:
            self.score = self.p_mastery
        else:
            self.p_mastery = self.score

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Misconception:
    id: str
    code: str
    category: str
    name: str
    description: str = ""
    remediation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StudentMisconceptionRecord:
    id: str
    student_id: str
    misconception_code: str
    frequency: int = 1
    concept_id: str = ""
    description: str = ""
    last_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 6. Assessments ───────────────────────────────────────────────────────

@dataclass
class QuestionBankItem:
    id: str
    course_id: str
    question_text: str
    item_type: str = "MCQ"  # MCQ, NUMERICAL, SHORT_ANSWER, ESSAY, CODE, MATCHING
    organization_id: Optional[str] = None
    subject_id: Optional[str] = None
    concept_id: str = ""
    topic_id: str = ""
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    rubric: Dict[str, Any] = field(default_factory=dict)
    difficulty: int = 1  # 1 to 5
    bloom_level: str = "recall"
    hints: List[str] = field(default_factory=list)
    explanation: str = ""
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Assessment:
    id: str
    course_id: str
    title: str
    assessment_type: AssessmentType = AssessmentType.FORMATIVE
    total_marks: float = 100.0
    organization_id: Optional[str] = None
    description: str = ""
    duration_minutes: int = 0  # 0 = untimed
    passing_score: float = 70.0  # percentage
    item_ids: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    rubric: Dict[str, Any] = field(default_factory=dict)
    status: str = "published"  # draft, published, archived
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["assessment_type"] = self.assessment_type.value if isinstance(self.assessment_type, AssessmentType) else str(self.assessment_type)
        return d


@dataclass
class AssessmentItem:
    id: str
    assessment_id: str
    question_text: str
    item_type: str = "MCQ"  # MCQ, NUMERICAL, EQUATION, SHORT_ANSWER, ESSAY, CODE
    correct_answer: str = ""
    max_marks: float = 4.0
    concept_id: str = ""
    options: List[str] = field(default_factory=list)
    rubric: Dict[str, Any] = field(default_factory=dict)
    difficulty: int = 1
    hints: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Assignment:
    id: str
    course_id: str
    title: str
    assessment_id: str = ""
    teacher_id: Optional[str] = None
    due_date: Optional[str] = None
    organization_id: Optional[str] = None
    cohort_id: Optional[str] = None
    class_group_id: Optional[str] = None
    assigned_by: Optional[str] = None
    instructions: str = ""
    due_at: Optional[str] = None
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.assigned_by and self.teacher_id:
            self.assigned_by = self.teacher_id
        if not self.due_at and self.due_date:
            self.due_at = self.due_date
        if not self.teacher_id and self.assigned_by:
            self.teacher_id = self.assigned_by
        if not self.due_date and self.due_at:
            self.due_date = self.due_at

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AssessmentAttempt:
    id: str
    assessment_id: str
    student_id: str
    score: float = 0.0
    passed: bool = False
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    assignment_id: Optional[str] = None
    attempt_number: int = 1
    status: str = "in_progress"  # in_progress, submitted, grading_pending, graded, reviewed
    time_spent_seconds: int = 0
    max_score: float = 100.0
    percentage: float = 0.0
    current_difficulty: int = 1
    answers: Dict[str, Any] = field(default_factory=dict)
    item_results: Dict[str, Any] = field(default_factory=dict)
    ai_grading_summary: Dict[str, Any] = field(default_factory=dict)
    teacher_review: Dict[str, Any] = field(default_factory=dict)
    reassessment_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Reassessment:
    id: str
    original_attempt_id: str
    student_id: str
    course_id: str
    generated_assessment_id: str
    target_concepts: List[str] = field(default_factory=list)
    status: str = "PENDING"
    target_score: float = 80.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 7. Teacher Directives & Interventions ────────────────────────────────

class InstructionScope(str, Enum):
    """Authoritative scopes for teacher instruction cascading."""
    ORGANIZATION = "ORGANIZATION"
    COURSE = "COURSE"
    CLASS = "CLASS"
    STUDENT = "STUDENT"
    SESSION = "SESSION"


@dataclass
class TeacherInstructionRecord:
    id: str
    teacher_id: str
    student_id: str = "all"
    course_id: str = "crs-default"
    instruction_text: str = ""
    concept_scope: str = "ALL"
    priority: int = 2
    is_active: bool = True
    organization_id: Optional[str] = None
    course_version_id: Optional[str] = None
    class_id: Optional[str] = None
    session_id: Optional[str] = None
    scope_type: str = InstructionScope.COURSE.value
    status: str = "ACTIVE"
    safety_status: str = "VALIDATED"
    safety_reasons: List[str] = field(default_factory=list)
    start_at: Optional[str] = None
    expires_at: Optional[str] = None
    version: int = 1
    audit_trail: List[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InterventionRecord:
    id: str
    student_id: str
    course_id: str
    severity: AlertSeverity = AlertSeverity.WARNING
    alert_type: str = "learning_gap"
    message: str = ""
    status: AlertStatus = AlertStatus.ACTIVE
    reason: str = ""
    priority: str = "MEDIUM"
    assigned_teacher: Optional[str] = None
    due_at: Optional[str] = None
    resolution: Optional[str] = None
    teacher_notes: List[dict] = field(default_factory=list)
    trigger_type: str = "teacher_created"
    trigger_evidence: dict = field(default_factory=dict)
    audit_trail: List[dict] = field(default_factory=list)
    resolved_by: Optional[str] = None
    dismissed_at: Optional[str] = None
    dismissed_by: Optional[str] = None
    dismissal_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value if isinstance(self.severity, AlertSeverity) else str(self.severity)
        d["status"] = self.status.value if isinstance(self.status, AlertStatus) else str(self.status)
        return d


@dataclass
class Notification:
    id: str
    recipient_id: str
    title: str
    message: str
    channel: str = "in_app"
    status: str = "created"
    is_read: bool = False
    retry_count: int = 0
    max_retries: int = 3
    backoff_seconds: float = 1.0
    next_retry_at: Optional[str] = None
    delivered_at: Optional[str] = None
    error_message: Optional[str] = None
    provider_message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 8. AI Governance, Observability & Auditing ───────────────────────────

@dataclass
class AIProvider:
    id: str
    name: str
    provider_type: str  # local_gguf, central_platform, anthropic, openai
    base_url: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AIModel:
    id: str
    provider_id: str
    model_name: str
    context_window: int = 8192
    is_default: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AIExecutionLog:
    id: str
    model_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    status: str = "SUCCESS"
    request_id: str = ""
    provider: str = ""
    model: str = ""
    student_id: Optional[str] = None
    session_id: Optional[str] = None
    course_id: Optional[str] = None
    task_type: str = "general"
    error_class: Optional[str] = None
    estimated_cost_usd: float = 0.0
    fallback_used: bool = False
    prompt_hash: str = ""
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if self.cost_usd is not None and self.estimated_cost_usd == 0.0:
            self.estimated_cost_usd = self.cost_usd
        elif self.estimated_cost_usd != 0.0 and self.cost_usd is None:
            self.cost_usd = self.estimated_cost_usd

        if self.total_tokens is None:
            self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict:
        return asdict(self)



@dataclass
class AuditLog:
    id: str
    organization_id: str
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = "127.0.0.1"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 9. Plug-and-Play RAG Knowledge Subsystem ────────────────────────────

class KnowledgeContentType(str, Enum):
    TEXTBOOK = "textbook"
    REFERENCE = "reference"
    TEACHER_NOTE = "teacher_note"
    WORKSHEET = "worksheet"
    REMEDIAL = "remedial"
    ASSESSMENT_SOURCE = "assessment_source"
    SOLUTION_GUIDE = "solution_guide"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().lower()
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)


class KnowledgeVisibilityScope(str, Enum):
    COURSE = "course"
    CLASS = "class"
    STUDENT_TARGETED = "student_targeted"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().lower()
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)


class RAGSourceStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    INGESTED = "ingested"
    VALIDATED = "validated"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_norm = value.strip().lower()
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)


KnowledgeAssetStatus = RAGSourceStatus


@dataclass
class RAGSource:
    id: str
    organization_id: str
    course_id: str
    subject: str
    title: str
    source_type: str = "text"  # pdf, docx, html, markdown, text, json
    authority: str = "NCERT"  # NCERT, APPROVED_CURRICULUM, TRUSTED_CURRICULUM, OFFICIAL_DOCS
    version: str = "1.0.0"
    status: str = "draft"
    checksum: str = ""
    metadata_json: Dict[str, Any] = field(default_factory=dict)
    chunk_count: int = 0
    content_type: str = "textbook"
    uploaded_by: Optional[str] = None
    published_by: Optional[str] = None
    published_at: Optional[str] = None
    error_message: Optional[str] = None
    course_version_id: Optional[str] = None
    visibility_scope: str = "course"
    class_id: Optional[str] = None
    target_student_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        if isinstance(self.status, Enum):
            d["status"] = self.status.value
        if isinstance(self.content_type, Enum):
            d["content_type"] = self.content_type.value
        if isinstance(self.visibility_scope, Enum):
            d["visibility_scope"] = self.visibility_scope.value
        return d


@dataclass
class RAGChunk:
    id: str
    source_id: str
    course_id: str
    subject: str
    chapter: str
    topic: str
    concept: str = ""
    difficulty: float = 0.5
    page: int = 1
    section: str = ""
    content_type: str = "explanation"  # definition, formula, example, explanation, exercise
    text: str = ""
    clean_text: str = ""
    embedding_vector: List[float] = field(default_factory=list)
    provenance_type: str = "NCERT"
    metadata_json: Dict[str, Any] = field(default_factory=dict)
    course_version_id: Optional[str] = None
    visibility_scope: str = "course"
    class_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class SyncOperationRecord:
    operation_id: str
    student_id: str
    device_id: Optional[str] = None
    course_id: Optional[str] = None
    synced_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    acknowledged_ids: List[str] = field(default_factory=list)
    conflicts_resolved: int = 0
    status: str = "SYNCED"
    latest_mastery: float = 0.0
    server_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)



