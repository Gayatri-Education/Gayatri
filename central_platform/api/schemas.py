"""Gayatri AI Platform — Pydantic Request, Response, and Envelope Schemas (Phase 02).

Defines standard schemas for all versioned platform endpoints (/api/v1/*),
ensuring type safety, validation, and consistent error envelopes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Metadata and Envelopes ───────────────────────────────────────────────

class MetaDetail(BaseModel):
    request_id: str = Field(default="", description="Unique request correlation ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
    api_version: str = Field(default="v1", description="API Version")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Granular error context")


class ApiResponse(BaseModel, Generic[T]):
    ok: bool = Field(default=True, description="Success flag")
    data: Optional[T] = Field(default=None, description="Payload data")
    error: Optional[ErrorDetail] = Field(default=None, description="Error detail if ok is False")
    meta: MetaDetail = Field(default_factory=MetaDetail, description="Request metadata")


# ── Health & Probes ──────────────────────────────────────────────────────

class HealthStatusResponse(BaseModel):
    status: str = "ONLINE"
    service: str = "GayatriPlatformAPI"
    version: str = "v2.0-reconciliation"
    database: str = "CONNECTED"
    students_monitored: int = 5
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Authentication & Users ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=4)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    username: str
    role: str
    organization_id: str = "org-default"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: str
    new_password: str = Field(..., min_length=4)
    token: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    organization_id: str
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=4)
    role: str = Field(default="STUDENT")
    organization_id: str = Field(default="org-default")


# ── Student & Telemetry ──────────────────────────────────────────────────

class StudentSnapshotRequest(BaseModel):
    student_id: str
    student_name: str
    course_id: str = "crs-chem-101"
    mastery: float = Field(default=0.5, ge=0.0, le=1.0)
    needs_attention: bool = False
    misconceptions: List[str] = Field(default_factory=list)
    hint_count: int = 0
    retention_rate: float = Field(default=0.85, ge=0.0, le=1.0)


class StudentProfileResponse(BaseModel):
    student_id: str
    student_name: str
    course_id: str
    current_concept: str
    mastery: float
    retention_rate: float
    hint_count: int
    misconceptions: List[str]
    recent_activity: Any = Field(default_factory=list)


# ── Teacher & Directives ─────────────────────────────────────────────────

class TeacherInstructionCreateRequest(BaseModel):
    instruction: str = Field(..., min_length=3)
    student_id: str = Field(default="all")
    course_id: str = Field(default="crs-chem-101")
    priority: int = Field(default=2, ge=1, le=5)
    concept_scope: str = Field(default="ALL")
    start_at: Optional[str] = None
    expires_at: Optional[str] = None
    scope_type: Optional[str] = None


class TeacherInstructionResponse(BaseModel):
    instruction_id: str
    teacher_id: str
    student_id: str
    course_id: str
    instruction_text: str
    priority: int
    concept_scope: str
    scope_type: str = "STUDENT"
    is_active: bool
    status: str = "ACTIVE"
    start_at: Optional[str] = None
    expires_at: Optional[str] = None
    safety_status: str = "VALIDATED"
    safety_reasons: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: Optional[str] = None


class TeacherInstructionUpdateRequest(BaseModel):
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    concept_scope: Optional[str] = None
    expires_at: Optional[str] = None
    status: Optional[str] = None
    instruction_text: Optional[str] = None


class TeacherInstructionValidateRequest(BaseModel):
    instruction: str = Field(..., min_length=1)


class TeacherInstructionValidateResponse(BaseModel):
    is_valid: bool
    safety_status: str
    violations: List[str] = Field(default_factory=list)
    sanitized_text: str = ""
    target_invariants: List[str] = Field(default_factory=list)


class TeacherInstructionToggleRequest(BaseModel):
    instruction_id: str
    active: bool


class AlertResolveRequest(BaseModel):
    alert_id: str
    resolution_note: str = Field(default="Resolved by teacher directive")


# ── Teacher Interventions (Section 21) ──────────────────────────────────

class TeacherInterventionCreateRequest(BaseModel):
    student_id: str
    course_id: str = Field(default="crs-chem-101")
    reason: str = Field(..., min_length=5)
    priority: str = Field(default="MEDIUM")
    assigned_teacher: Optional[str] = None
    due_at: Optional[str] = None
    trigger_type: str = Field(default="teacher_created")
    trigger_evidence: Dict[str, Any] = Field(default_factory=dict)


class TeacherInterventionResponse(BaseModel):
    intervention_id: str
    student_id: str
    course_id: str
    reason: str
    priority: str
    assigned_teacher: Optional[str] = None
    trigger_type: str
    trigger_evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    due_at: Optional[str] = None
    status: str
    resolution: Optional[str] = None
    teacher_notes: List[Dict[str, Any]] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    dismissed_at: Optional[str] = None
    dismissed_by: Optional[str] = None
    dismissal_reason: Optional[str] = None


class TeacherInterventionUpdateRequest(BaseModel):
    priority: Optional[str] = None
    due_at: Optional[str] = None
    assigned_teacher: Optional[str] = None
    status: Optional[str] = None


class TeacherInterventionNoteRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TeacherInterventionResolveRequest(BaseModel):
    resolution_note: str = Field(..., min_length=3)


class TeacherInterventionDismissRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class TeacherInterventionEvaluateRequest(BaseModel):
    student_id: str
    course_id: str = Field(default="crs-chem-101")


class TeacherDashboardResponse(BaseModel):
    total_students: int
    active_today: int
    average_mastery: float
    critical_alerts_count: int
    mastery_distribution: Dict[str, int]
    chapter_averages: Dict[str, float]
    recent_alerts: List[Dict[str, Any]]
    students: List[Dict[str, Any]]
    # Master Plan Section 19 Core Teacher Dimensions
    students_active: int = 0
    difficult_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    common_misconceptions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    intervention_alerts: List[Dict[str, Any]] = Field(default_factory=list)


# ── Curriculum & Courses ─────────────────────────────────────────────────

class CourseResponse(BaseModel):
    course_id: str
    title: str
    description: str
    subject: str
    grade_level: str
    total_concepts: int = 12
    version: str = "v1.0"


class CurriculumResponse(BaseModel):
    course_id: str
    chapters: List[Dict[str, Any]]
    total_topics: int
    total_concepts: int


# ── Sessions & Learning Events ───────────────────────────────────────────

class SessionStartRequest(BaseModel):
    student_id: str
    course_id: str = "crs-chem-101"
    initial_concept: Optional[str] = "chem_thermo_first_law"


class SessionResponse(BaseModel):
    session_id: str
    student_id: str
    course_id: str
    active_concept: str
    status: str = "ACTIVE"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LearningEventSchema(BaseModel):
    event_id: str
    student_id: str
    session_id: str
    event_type: str = "question_attempted"
    organization_id: str = "org-default"
    course_id: str = "crs-chem-101"
    source: str = "student_desktop"
    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0.0"
    turn_id: str = "turn-01"
    concept_id: str = ""
    correctness: str = "correct"
    hint_used: int = 0
    difficulty: float = 0.5
    score: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    misconception_code: str = ""


# ── Assessments ──────────────────────────────────────────────────────────

class AssessmentItemSchema(BaseModel):
    question_id: str
    topic_id: str
    difficulty: int
    question: str
    question_type: str = "mcq"
    options: List[str] = Field(default_factory=list)


class AssessmentSubmitRequest(BaseModel):
    assessment_id: str
    student_id: str
    answers: Dict[str, Any]


class AssessmentSubmitResponse(BaseModel):
    assessment_id: str
    student_id: str
    score: float
    total_questions: int
    passed: bool
    feedback: Dict[str, str] = Field(default_factory=list)


# ── RAG & Evidence ───────────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2)
    concept_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)


class RAGResultItem(BaseModel):
    chunk_id: str
    chapter: str
    topic: str
    page: int
    text: str
    score: float
    citation: str


class RAGQueryResponse(BaseModel):
    status: str
    query: str
    results: List[RAGResultItem]
    count: int


# ── AI Gateway & Governance ──────────────────────────────────────────────

class AIStatusResponse(BaseModel):
    gateway_status: str = "HEALTHY"
    active_provider: str = "local_llama"
    active_model: str = "Qwen2.5-3B-Instruct-Q4_K_M"
    available_providers: List[str] = Field(default_factory=lambda: ["local_llama", "ollama", "openai", "gemini"])
    token_usage_today: int = 4210
    budget_remaining_usd: float = 98.45
    kill_switch_active: bool = False


# ── Analytics ────────────────────────────────────────────────────────────

class CohortAnalyticsResponse(BaseModel):
    cohort_id: str = "cohort_chem_101"
    student_count: int = 5
    average_mastery: float = 0.76
    mastery_tiers: Dict[str, int]
    weak_concepts: List[str]
    frequent_misconceptions: List[Dict[str, Any]]


# ── Notifications ────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    notification_id: str
    recipient_id: str
    channel: str = "in_app"
    title: str
    message: str
    created_at: str
    is_read: bool = False


# ── Sync ─────────────────────────────────────────────────────────────────

class BatchSyncEventsRequest(BaseModel):
    student_id: str
    events: List[Dict[str, Any]]


class BatchSyncEventsResponse(BaseModel):
    ok: bool = True
    synced_count: int
    duplicate_count: int = 0
    failed_count: int = 0
    acknowledged_ids: List[str] = Field(default_factory=list)
    status: str = "SYNCED"
    latest_mastery: float = 0.50
    server_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



# ── Student Actions & Learning Engine Bridge (Phase 07) ─────────────────

class StudentActionRequest(BaseModel):
    concept_id: str
    action_type: str = "answer_submitted"
    course_id: str = "crs-chem-101"
    session_id: Optional[str] = None
    turn_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answer: Optional[str] = None
    correctness: Optional[str] = None
    score: Optional[float] = None
    hint_level: int = 0
    difficulty: Optional[float] = None
    response_time_ms: Optional[float] = None
    misconception_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Teacher Copilot (Phase 13 / Section 22) ───────────────────────────────

class CopilotEvidenceItemSchema(BaseModel):
    evidence_id: str
    category: str
    concept_id: Optional[str] = None
    metric_value: Optional[float] = None
    description: str = ""
    timestamp: Optional[str] = None


class CopilotSourceRecordSchema(BaseModel):
    record_id: str
    record_type: str
    timestamp: str = ""
    summary: str = ""


class CopilotCitationSchema(BaseModel):
    evidence_id: str
    category: str
    summary: str


class TeacherCopilotQueryRequest(BaseModel):
    query: str
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    time_window_days: Optional[int] = 7


class TeacherCopilotQueryResponse(BaseModel):
    answer: str
    evidence: List[CopilotEvidenceItemSchema] = Field(default_factory=list)
    source_records: List[CopilotSourceRecordSchema] = Field(default_factory=list)
    confidence: float = 1.0
    recommended_action: str = ""
    citations: List[CopilotCitationSchema] = Field(default_factory=list)
    summary: Optional[str] = None
    recommended_focus_concept: Optional[str] = None
    query: Optional[str] = None
    student_id: Optional[str] = None
    course_id: Optional[str] = None


