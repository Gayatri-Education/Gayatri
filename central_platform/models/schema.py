"""Platform schema models for multi-organization RBAC and core domain entities.

Master Plan Section 12 Entity Specifications.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    COURSE_ADMIN = "course_admin"
    TEACHER = "teacher"
    STUDENT = "student"


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

@dataclass
class Course:
    id: str
    organization_id: str
    code: str
    title: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


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
    version: str = "1.0.0"
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CurriculumVersion:
    id: str
    curriculum_id: str
    version_num: str
    change_log: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Module:
    id: str
    curriculum_id: str
    title: str
    sequence_order: int = 1
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

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, SessionStatus) else str(self.status)
        return d


@dataclass
class LearningEvent:
    id: str
    session_id: str
    student_id: str
    concept_id: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


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
    id: str
    slr_id: str
    concept_id: str
    score: float = 0.5
    confidence: float = 0.8
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
    last_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ── 6. Assessments ───────────────────────────────────────────────────────

@dataclass
class Assessment:
    id: str
    course_id: str
    title: str
    assessment_type: AssessmentType = AssessmentType.FORMATIVE
    total_marks: float = 100.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["assessment_type"] = self.assessment_type.value if isinstance(self.assessment_type, AssessmentType) else str(self.assessment_type)
        return d


@dataclass
class AssessmentItem:
    id: str
    assessment_id: str
    question_text: str
    item_type: str = "MCQ"  # MCQ, NUMERICAL, EQUATION
    correct_answer: str = ""
    max_marks: float = 4.0

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

    def to_dict(self) -> dict:
        return asdict(self)


# ── 7. Teacher Directives & Interventions ────────────────────────────────

@dataclass
class TeacherInstructionRecord:
    id: str
    teacher_id: str
    student_id: str
    course_id: str
    instruction_text: str
    concept_scope: str = "ALL"
    priority: int = 2
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value if isinstance(self.severity, AlertSeverity) else str(self.severity)
        d["status"] = self.status.value if isinstance(self.status, AlertStatus) else str(self.status)
        return d


@dataclass
class Assignment:
    id: str
    course_id: str
    teacher_id: str
    title: str
    due_date: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Notification:
    id: str
    recipient_id: str
    title: str
    message: str
    is_read: bool = False
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
    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    status: str = "SUCCESS"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
