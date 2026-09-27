"""Canonical Student Learning Record (SLR) Models (Phase 06).

Master Plan Section 15:
The SLR is the canonical student learning view aggregated across 15 dimensions:
1.  identity
2.  enrollment
3.  course
4.  curriculum
5.  mastery
6.  recent_sessions
7.  learning_timeline
8.  misconceptions
9.  assessment_results
10. hints
11. teacher_feedback
12. teacher_instructions
13. interventions
14. recommendations
15. alerts
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SLRIdentity(BaseModel):
    """1. Student identity telemetry."""
    model_config = ConfigDict(extra="ignore")

    student_id: str
    student_name: str = "Student"
    email: str = ""
    organization_id: str = "org-default"
    created_at: str = Field(default_factory=_now_iso)


class SLREnrollment(BaseModel):
    """2. Student enrollment metadata."""
    model_config = ConfigDict(extra="ignore")

    enrollment_id: str = "enr-default"
    course_id: str = "crs-chem-101"
    cohort_id: Optional[str] = None
    is_active: bool = True
    enrolled_at: str = Field(default_factory=_now_iso)


class SLRCourse(BaseModel):
    """3. Course metadata."""
    model_config = ConfigDict(extra="ignore")

    course_id: str = "crs-chem-101"
    code: str = "CHEM101"
    title: str = "Thermodynamics & Physical Chemistry"
    description: str = "Foundational college & high school physical chemistry"


class SLRCurriculum(BaseModel):
    """4. Curriculum progress & nodes."""
    model_config = ConfigDict(extra="ignore")

    curriculum_id: str = "cur-chem-2026"
    version: str = "1.0.0"
    current_concept: str = "chem_thermo_first_law"
    completed_concepts: List[str] = Field(default_factory=list)


class SLRMastery(BaseModel):
    """5. Granular and aggregate concept mastery state."""
    model_config = ConfigDict(extra="ignore")

    overall_score: float = 0.50
    retention_rate: float = 0.85
    concept_scores: Dict[str, float] = Field(default_factory=dict)
    concept_confidences: Dict[str, float] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=_now_iso)


class SLRSession(BaseModel):
    """6. Recent learning session records."""
    model_config = ConfigDict(extra="ignore")

    session_id: str
    concept_id: str = "chem_thermo_first_law"
    status: str = "completed"
    started_at: str = Field(default_factory=_now_iso)
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None


class SLRTimelineItem(BaseModel):
    """7. Chronological timeline event item."""
    model_config = ConfigDict(extra="ignore")

    item_id: str
    event_type: str  # assessment, session, mastery_change, mistake, hint, teacher_intervention
    summary: str
    timestamp: str = Field(default_factory=_now_iso)
    concept_id: str = ""
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SLRMisconception(BaseModel):
    """8. Active and observed misconceptions."""
    model_config = ConfigDict(extra="ignore")

    code: str
    category: str = "thermodynamics"
    name: str = "Conceptual Misconception"
    frequency: int = 1
    last_observed: str = Field(default_factory=_now_iso)
    remediation: str = ""
    status: str = "active"  # active, recovering, resolved


class SLRAssessmentResult(BaseModel):
    """9. Assessment performance telemetry."""
    model_config = ConfigDict(extra="ignore")

    attempt_id: str
    assessment_id: str
    title: str = "Assessment Attempt"
    score: float = 0.0
    max_marks: float = 100.0
    percentage: float = 0.0
    passed: bool = False
    completed_at: str = Field(default_factory=_now_iso)


class SLRHints(BaseModel):
    """10. Hint usage and cognitive dependency."""
    model_config = ConfigDict(extra="ignore")

    total_hints_requested: int = 0
    hints_used: int = 0
    per_concept_breakdown: Dict[str, int] = Field(default_factory=dict)
    last_hint_at: Optional[str] = None


class SLRTeacherFeedback(BaseModel):
    """11. Direct teacher pedagogical comments & reviews."""
    model_config = ConfigDict(extra="ignore")

    feedback_id: str
    teacher_id: str
    feedback_text: str
    created_at: str = Field(default_factory=_now_iso)


class SLRTeacherInstruction(BaseModel):
    """12. Active teacher directives scoped to student or cohort."""
    model_config = ConfigDict(extra="ignore")

    instruction_id: str
    teacher_id: str
    instruction_text: str
    concept_scope: str = "ALL"
    priority: int = 2
    created_at: str = Field(default_factory=_now_iso)


class SLRIntervention(BaseModel):
    """13. Triggered teacher interventions."""
    model_config = ConfigDict(extra="ignore")

    intervention_id: str
    severity: str = "warning"
    alert_type: str = "learning_gap"
    message: str = ""
    status: str = "active"
    created_at: str = Field(default_factory=_now_iso)
    resolved_at: Optional[str] = None


class SLRRecommendation(BaseModel):
    """14. Algorithmic recommendations for student next steps."""
    model_config = ConfigDict(extra="ignore")

    recommendation_id: str
    concept_id: str
    action_type: str = "review"  # review, practice, advance, assessment
    reason: str = ""
    priority: int = 1


class SLRAlert(BaseModel):
    """15. Real-time pedagogical alerts."""
    model_config = ConfigDict(extra="ignore")

    alert_id: str
    alert_type: str = "learning_gap"
    severity: str = "warning"
    message: str = ""
    triggered_at: str = Field(default_factory=_now_iso)


class AuthoritativeSLR(BaseModel):
    """Canonical Authoritative Student Learning Record (SLR).
    
    Single authoritative contract aggregating all 15 learning dimensions.
    """
    model_config = ConfigDict(extra="ignore")

    slr_id: str
    student_id: str
    course_id: str = "crs-chem-101"
    authoritative: bool = True
    schema_version: str = "1.0.0"
    generated_at: str = Field(default_factory=_now_iso)

    identity: SLRIdentity
    enrollment: SLREnrollment
    course: SLRCourse
    curriculum: SLRCurriculum
    mastery: SLRMastery
    recent_sessions: List[SLRSession] = Field(default_factory=list)
    learning_timeline: List[SLRTimelineItem] = Field(default_factory=list)
    misconceptions: List[SLRMisconception] = Field(default_factory=list)
    assessment_results: List[SLRAssessmentResult] = Field(default_factory=list)
    hints: SLRHints = Field(default_factory=SLRHints)
    teacher_feedback: List[SLRTeacherFeedback] = Field(default_factory=list)
    teacher_instructions: List[SLRTeacherInstruction] = Field(default_factory=list)
    interventions: List[SLRIntervention] = Field(default_factory=list)
    recommendations: List[SLRRecommendation] = Field(default_factory=list)
    alerts: List[SLRAlert] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
