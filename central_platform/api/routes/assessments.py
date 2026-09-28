"""Gayatri AI Central Platform — Authoritative Assessments API Endpoints (Phase 19).

Fulfills Master Plan Section 28:
- Question item banks with difficulty, Bloom taxonomy levels, and rubrics
- Diagnostic, Formative, Summative, and Adaptive assessment generation
- Assignments and attempt lifecycle management
- Deterministic and AI-assisted rubric grading
- Teacher manual reviews, adjustments, and sign-offs
- Targeted reassessment recommendations and generation
- Complete learning event ingestion and SLR synchronization
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from central_platform.api.schemas import (
    ApiResponse,
    AssessmentCreateRequest,
    AssessmentItemSchema,
    AssessmentResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    AssignmentCreateRequest,
    AssignmentResponse,
    AttemptDetailResponse,
    AttemptStartRequest,
    AttemptStartResponse,
    AttemptSubmitRequest,
    QuestionBankItemCreateRequest,
    QuestionBankItemResponse,
    ReassessmentGenerateRequest,
    ReassessmentResponse,
    TeacherReviewAttemptRequest,
)
from central_platform.assessment.models import AssessmentType
from central_platform.assessment.service import AssessmentService
from central_platform.models.schema import (
    Assessment,
    Assignment,
    QuestionBankItem,
)
from core.assessment.manager import SAMPLE_QUESTION_BANK

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def get_assessment_service() -> AssessmentService:
    return AssessmentService()


# ── 1. Question Bank Endpoints ───────────────────────────────────────────────

@router.get("/items", response_model=ApiResponse[List[QuestionBankItemResponse]])
async def list_assessment_items(
    course_id: Optional[str] = Query(None, description="Course ID filter"),
    concept_id: Optional[str] = Query(None, description="Concept ID filter"),
    difficulty: Optional[int] = Query(None, description="Difficulty filter (1-5)"),
    item_type: Optional[str] = Query(None, description="Question type filter"),
    topic_id: Optional[str] = Query(None, description="Legacy topic ID alias"),
    service: AssessmentService = Depends(get_assessment_service),
):
    """Retrieve question bank items with filtering. Defaults to populated bank or sample items."""
    effective_concept = concept_id or topic_id
    items = service.list_questions(
        course_id=course_id,
        concept_id=effective_concept,
        difficulty=difficulty,
        item_type=item_type,
    )

    if not items:
        # Fallback to SAMPLE_QUESTION_BANK for seamless backward compatibility
        for q in SAMPLE_QUESTION_BANK:
            q_concept = getattr(q, "concept_id", getattr(q, "topic_id", "chem_thermo_first_law"))
            if not effective_concept or q_concept == effective_concept:
                items.append(
                    QuestionBankItem(
                        id=getattr(q, "id", getattr(q, "question_id", "q1")),
                        course_id=course_id or "crs-chem-101",
                        concept_id=q_concept,
                        question_text=getattr(q, "question", getattr(q, "question_text", "")),
                        item_type=str(getattr(q, "type", getattr(q, "question_type", "MCQ"))).upper(),
                        options=getattr(q, "options", ["A", "B", "C", "D"]),
                        correct_answer=str(getattr(q, "answer", getattr(q, "correct_answer", "A"))),
                        difficulty=int(getattr(q, "difficulty", 2)),
                    )
                )

    data = [
        QuestionBankItemResponse(
            id=it.id,
            course_id=it.course_id,
            question_text=it.question_text,
            item_type=it.item_type,
            organization_id=it.organization_id,
            subject_id=it.subject_id,
            concept_id=it.concept_id,
            topic_id=it.topic_id,
            options=it.options,
            correct_answer=it.correct_answer,
            rubric=it.rubric,
            difficulty=it.difficulty,
            bloom_level=it.bloom_level,
            hints=it.hints,
            explanation=it.explanation,
            tags=it.tags,
            is_active=it.is_active,
            created_at=it.created_at,
        )
        for it in items
    ]
    return ApiResponse(ok=True, data=data)


@router.post("/items", response_model=ApiResponse[QuestionBankItemResponse], status_code=status.HTTP_201_CREATED)
async def create_question_bank_item(
    req: QuestionBankItemCreateRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Create a new question bank item."""
    item = QuestionBankItem(
        id=f"qb-{uuid.uuid4().hex[:10]}",
        course_id=req.course_id,
        question_text=req.question_text,
        item_type=req.item_type,
        organization_id=req.organization_id,
        subject_id=req.subject_id,
        concept_id=req.concept_id,
        topic_id=req.topic_id,
        options=req.options,
        correct_answer=req.correct_answer,
        rubric=req.rubric,
        difficulty=req.difficulty,
        bloom_level=req.bloom_level,
        hints=req.hints,
        explanation=req.explanation,
        tags=req.tags,
    )
    created = service.create_question(item)
    return ApiResponse(
        ok=True,
        data=QuestionBankItemResponse(
            id=created.id,
            course_id=created.course_id,
            question_text=created.question_text,
            item_type=created.item_type,
            organization_id=created.organization_id,
            subject_id=created.subject_id,
            concept_id=created.concept_id,
            topic_id=created.topic_id,
            options=created.options,
            correct_answer=created.correct_answer,
            rubric=created.rubric,
            difficulty=created.difficulty,
            bloom_level=created.bloom_level,
            hints=created.hints,
            explanation=created.explanation,
            tags=created.tags,
            is_active=created.is_active,
            created_at=created.created_at,
        ),
    )


@router.get("/items/{item_id}", response_model=ApiResponse[QuestionBankItemResponse])
async def get_question_bank_item(
    item_id: str,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Get question bank item details by ID."""
    item = service.get_question(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Question '{item_id}' not found.")
    return ApiResponse(
        ok=True,
        data=QuestionBankItemResponse(
            id=item.id,
            course_id=item.course_id,
            question_text=item.question_text,
            item_type=item.item_type,
            organization_id=item.organization_id,
            subject_id=item.subject_id,
            concept_id=item.concept_id,
            topic_id=item.topic_id,
            options=item.options,
            correct_answer=item.correct_answer,
            rubric=item.rubric,
            difficulty=item.difficulty,
            bloom_level=item.bloom_level,
            hints=item.hints,
            explanation=item.explanation,
            tags=item.tags,
            is_active=item.is_active,
            created_at=item.created_at,
        ),
    )


# ── 2. Assessment Definition Endpoints ───────────────────────────────────────

@router.post("", response_model=ApiResponse[AssessmentResponse], status_code=status.HTTP_201_CREATED)
async def create_assessment(
    req: AssessmentCreateRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Create an assessment definition (Diagnostic, Formative, Summative, Adaptive, etc.)."""
    try:
        asmt_type = AssessmentType(req.assessment_type.lower())
    except ValueError:
        asmt_type = AssessmentType.FORMATIVE

    asmt = Assessment(
        id=f"asmt-{uuid.uuid4().hex[:10]}",
        course_id=req.course_id,
        title=req.title,
        assessment_type=asmt_type,
        total_marks=100.0,
        organization_id=req.organization_id,
        description=req.description,
        duration_minutes=req.duration_minutes,
        passing_score=req.passing_score,
        item_ids=req.item_ids,
        config=req.config,
        rubric=req.rubric,
        status=req.status,
    )
    created = service.create_assessment(asmt)
    return ApiResponse(
        ok=True,
        data=AssessmentResponse(
            id=created.id,
            course_id=created.course_id,
            title=created.title,
            assessment_type=created.assessment_type.value if hasattr(created.assessment_type, "value") else str(created.assessment_type),
            total_marks=created.total_marks,
            organization_id=created.organization_id,
            description=created.description,
            duration_minutes=created.duration_minutes,
            passing_score=created.passing_score,
            item_ids=created.item_ids,
            config=created.config,
            rubric=created.rubric,
            status=created.status,
            created_at=created.created_at,
            updated_at=created.updated_at,
        ),
    )


@router.get("", response_model=ApiResponse[List[AssessmentResponse]])
async def list_assessments(
    course_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    assessment_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    service: AssessmentService = Depends(get_assessment_service),
):
    """List assessments matching filters."""
    asmts = service.list_assessments(
        course_id=course_id,
        organization_id=organization_id,
        assessment_type=assessment_type,
        status=status_filter,
    )
    data = [
        AssessmentResponse(
            id=a.id,
            course_id=a.course_id,
            title=a.title,
            assessment_type=a.assessment_type.value if hasattr(a.assessment_type, "value") else str(a.assessment_type),
            total_marks=a.total_marks,
            organization_id=a.organization_id,
            description=a.description,
            duration_minutes=a.duration_minutes,
            passing_score=a.passing_score,
            item_ids=a.item_ids,
            config=a.config,
            rubric=a.rubric,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in asmts
    ]
    return ApiResponse(ok=True, data=data)


@router.get("/{assessment_id}", response_model=ApiResponse[AssessmentResponse])
async def get_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Get assessment definition by ID."""
    asmt = service.get_assessment(assessment_id)
    if not asmt:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return ApiResponse(
        ok=True,
        data=AssessmentResponse(
            id=asmt.id,
            course_id=asmt.course_id,
            title=asmt.title,
            assessment_type=asmt.assessment_type.value if hasattr(asmt.assessment_type, "value") else str(asmt.assessment_type),
            total_marks=asmt.total_marks,
            organization_id=asmt.organization_id,
            description=asmt.description,
            duration_minutes=asmt.duration_minutes,
            passing_score=asmt.passing_score,
            item_ids=asmt.item_ids,
            config=asmt.config,
            rubric=asmt.rubric,
            status=asmt.status,
            created_at=asmt.created_at,
            updated_at=asmt.updated_at,
        ),
    )


@router.post("/{assessment_id}/publish", response_model=ApiResponse[AssessmentResponse])
async def publish_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Publish an assessment."""
    published = service.publish_assessment(assessment_id)
    if not published:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return ApiResponse(
        ok=True,
        data=AssessmentResponse(
            id=published.id,
            course_id=published.course_id,
            title=published.title,
            assessment_type=published.assessment_type.value if hasattr(published.assessment_type, "value") else str(published.assessment_type),
            total_marks=published.total_marks,
            organization_id=published.organization_id,
            description=published.description,
            duration_minutes=published.duration_minutes,
            passing_score=published.passing_score,
            item_ids=published.item_ids,
            config=published.config,
            rubric=published.rubric,
            status=published.status,
            created_at=published.created_at,
            updated_at=published.updated_at,
        ),
    )


# ── 3. Assignments Endpoints ─────────────────────────────────────────────────

@router.post("/assignments", response_model=ApiResponse[AssignmentResponse], status_code=status.HTTP_201_CREATED)
async def create_assignment(
    req: AssignmentCreateRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Assign an assessment to a course, cohort, or class group."""
    assign = Assignment(
        id=f"assign-{uuid.uuid4().hex[:10]}",
        course_id=req.course_id,
        assessment_id=req.assessment_id,
        title=req.title,
        organization_id=req.organization_id,
        cohort_id=req.cohort_id,
        class_group_id=req.class_group_id,
        instructions=req.instructions,
        due_at=req.due_at,
    )
    created = service.create_assignment(assign)
    return ApiResponse(
        ok=True,
        data=AssignmentResponse(
            id=created.id,
            course_id=created.course_id,
            assessment_id=created.assessment_id,
            title=created.title,
            organization_id=created.organization_id,
            cohort_id=created.cohort_id,
            class_group_id=created.class_group_id,
            assigned_by=created.assigned_by,
            instructions=created.instructions,
            due_at=created.due_at,
            is_active=created.is_active,
            created_at=created.created_at,
        ),
    )


@router.get("/assignments", response_model=ApiResponse[List[AssignmentResponse]])
async def list_assignments(
    course_id: Optional[str] = Query(None),
    cohort_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    service: AssessmentService = Depends(get_assessment_service),
):
    """List active assignments."""
    assignments = service.list_assignments(
        course_id=course_id,
        cohort_id=cohort_id,
        organization_id=organization_id,
    )
    data = [
        AssignmentResponse(
            id=a.id,
            course_id=a.course_id,
            assessment_id=a.assessment_id,
            title=a.title,
            organization_id=a.organization_id,
            cohort_id=a.cohort_id,
            class_group_id=a.class_group_id,
            assigned_by=a.assigned_by,
            instructions=a.instructions,
            due_at=a.due_at,
            is_active=a.is_active,
            created_at=a.created_at,
        )
        for a in assignments
    ]
    return ApiResponse(ok=True, data=data)


# ── 4. Attempts Lifecycle Endpoints ──────────────────────────────────────────

@router.post("/attempts/start", response_model=ApiResponse[AttemptStartResponse], status_code=status.HTTP_201_CREATED)
async def start_attempt(
    req: AttemptStartRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Start an assessment attempt (Diagnostic, Formative, Summative, Adaptive)."""
    try:
        attempt = service.start_attempt(
            assessment_id=req.assessment_id,
            student_id=req.student_id,
            assignment_id=req.assignment_id,
            initial_difficulty=req.initial_difficulty,
        )
        return ApiResponse(
            ok=True,
            data=AttemptStartResponse(
                attempt_id=attempt.id,
                assessment_id=attempt.assessment_id,
                student_id=attempt.student_id,
                assignment_id=attempt.assignment_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status,
                started_at=attempt.started_at,
                max_score=attempt.max_score,
                current_difficulty=attempt.current_difficulty,
            ),
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/attempts/{attempt_id}/adaptive-next", response_model=ApiResponse[Optional[QuestionBankItemResponse]])
async def get_next_adaptive_question(
    attempt_id: str,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Get the next dynamically selected question for an adaptive assessment."""
    try:
        item = service.get_next_adaptive_item(attempt_id)
        if not item:
            return ApiResponse(ok=True, data=None)
        return ApiResponse(
            ok=True,
            data=QuestionBankItemResponse(
                id=item.id,
                course_id=item.course_id,
                question_text=item.question_text,
                item_type=item.item_type,
                organization_id=item.organization_id,
                subject_id=item.subject_id,
                concept_id=item.concept_id,
                topic_id=item.topic_id,
                options=item.options,
                correct_answer=item.correct_answer,
                rubric=item.rubric,
                difficulty=item.difficulty,
                bloom_level=item.bloom_level,
                hints=item.hints,
                explanation=item.explanation,
                tags=item.tags,
                is_active=item.is_active,
                created_at=item.created_at,
            ),
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/attempts/{attempt_id}/submit", response_model=ApiResponse[AttemptDetailResponse])
async def submit_attempt(
    attempt_id: str,
    req: AttemptSubmitRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Submit attempt answers, trigger hybrid grading, and feed central learning events."""
    try:
        attempt = service.submit_attempt(
            attempt_id=attempt_id,
            answers=req.answers,
            student_id=req.student_id,
        )
        return ApiResponse(
            ok=True,
            data=AttemptDetailResponse(
                id=attempt.id,
                assessment_id=attempt.assessment_id,
                student_id=attempt.student_id,
                assignment_id=attempt.assignment_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
                time_spent_seconds=attempt.time_spent_seconds,
                score=attempt.score,
                max_score=attempt.max_score,
                percentage=attempt.percentage,
                passed=attempt.passed,
                current_difficulty=attempt.current_difficulty,
                answers=attempt.answers,
                item_results=attempt.item_results,
                ai_grading_summary=attempt.ai_grading_summary,
                teacher_review=attempt.teacher_review,
                reassessment_recommendations=attempt.reassessment_recommendations,
            ),
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/attempts/{attempt_id}", response_model=ApiResponse[AttemptDetailResponse])
async def get_attempt(
    attempt_id: str,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Retrieve full attempt details with rubric evaluation and feedback."""
    attempt = service.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail=f"Attempt '{attempt_id}' not found.")
    return ApiResponse(
        ok=True,
        data=AttemptDetailResponse(
            id=attempt.id,
            assessment_id=attempt.assessment_id,
            student_id=attempt.student_id,
            assignment_id=attempt.assignment_id,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            time_spent_seconds=attempt.time_spent_seconds,
            score=attempt.score,
            max_score=attempt.max_score,
            percentage=attempt.percentage,
            passed=attempt.passed,
            current_difficulty=attempt.current_difficulty,
            answers=attempt.answers,
            item_results=attempt.item_results,
            ai_grading_summary=attempt.ai_grading_summary,
            teacher_review=attempt.teacher_review,
            reassessment_recommendations=attempt.reassessment_recommendations,
        ),
    )


@router.get("/attempts/student/{student_id}", response_model=ApiResponse[List[AttemptDetailResponse]])
async def list_student_attempts(
    student_id: str,
    limit: int = Query(50, ge=1, le=200),
    service: AssessmentService = Depends(get_assessment_service),
):
    """List all assessment attempts for a student."""
    attempts = service.get_student_attempts(student_id, limit=limit)
    data = [
        AttemptDetailResponse(
            id=a.id,
            assessment_id=a.assessment_id,
            student_id=a.student_id,
            assignment_id=a.assignment_id,
            attempt_number=a.attempt_number,
            status=a.status,
            started_at=a.started_at,
            completed_at=a.completed_at,
            time_spent_seconds=a.time_spent_seconds,
            score=a.score,
            max_score=a.max_score,
            percentage=a.percentage,
            passed=a.passed,
            current_difficulty=a.current_difficulty,
            answers=a.answers,
            item_results=a.item_results,
            ai_grading_summary=a.ai_grading_summary,
            teacher_review=a.teacher_review,
            reassessment_recommendations=a.reassessment_recommendations,
        )
        for a in attempts
    ]
    return ApiResponse(ok=True, data=data)


# ── 5. Teacher Review & Reassessment Endpoints ───────────────────────────────

@router.post("/attempts/{attempt_id}/teacher-review", response_model=ApiResponse[AttemptDetailResponse])
async def teacher_review_attempt(
    attempt_id: str,
    req: TeacherReviewAttemptRequest,
    teacher_id: str = Query("teacher-default"),
    service: AssessmentService = Depends(get_assessment_service),
):
    """Teacher review, score override, and approval."""
    try:
        attempt = service.teacher_review_attempt(
            attempt_id=attempt_id,
            teacher_id=teacher_id,
            item_score_adjustments=req.item_score_adjustments,
            teacher_comments=req.teacher_comments,
            status=req.status,
        )
        return ApiResponse(
            ok=True,
            data=AttemptDetailResponse(
                id=attempt.id,
                assessment_id=attempt.assessment_id,
                student_id=attempt.student_id,
                assignment_id=attempt.assignment_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
                time_spent_seconds=attempt.time_spent_seconds,
                score=attempt.score,
                max_score=attempt.max_score,
                percentage=attempt.percentage,
                passed=attempt.passed,
                current_difficulty=attempt.current_difficulty,
                answers=attempt.answers,
                item_results=attempt.item_results,
                ai_grading_summary=attempt.ai_grading_summary,
                teacher_review=attempt.teacher_review,
                reassessment_recommendations=attempt.reassessment_recommendations,
            ),
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/attempts/{attempt_id}/reassess", response_model=ApiResponse[ReassessmentResponse], status_code=status.HTTP_201_CREATED)
async def generate_reassessment(
    attempt_id: str,
    req: ReassessmentGenerateRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Generate targeted diagnostic/adaptive reassessment based on weak concepts from a prior attempt."""
    try:
        new_asmt, reassessment = service.generate_reassessment(
            original_attempt_id=attempt_id,
            target_score=req.target_score,
        )
        return ApiResponse(
            ok=True,
            data=ReassessmentResponse(
                reassessment_id=reassessment.id,
                original_attempt_id=reassessment.original_attempt_id,
                student_id=reassessment.student_id,
                course_id=reassessment.course_id,
                generated_assessment_id=reassessment.generated_assessment_id,
                target_concepts=reassessment.target_concepts,
                status=reassessment.status,
                target_score=reassessment.target_score,
                created_at=reassessment.created_at,
            ),
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ── 6. Legacy Submit Endpoint ────────────────────────────────────────────────

@router.post("/submit", response_model=ApiResponse[AssessmentSubmitResponse])
async def submit_assessment_legacy(
    submission: AssessmentSubmitRequest,
    service: AssessmentService = Depends(get_assessment_service),
):
    """Legacy backward-compatible submission endpoint."""
    total = max(len(submission.answers), 1)
    asmt = service.get_assessment(submission.assessment_id)
    if not asmt:
        item_ids = []
        for q_id, ans_val in submission.answers.items():
            matching_sample = next((sq for sq in SAMPLE_QUESTION_BANK if getattr(sq, "id", "") == q_id or getattr(sq, "question_id", "") == q_id), None)
            if matching_sample:
                qb_item = QuestionBankItem(
                    id=q_id,
                    course_id="crs-chem-101",
                    concept_id=getattr(matching_sample, "concept_id", "chem_thermo_first_law"),
                    question_text=getattr(matching_sample, "question", getattr(matching_sample, "question_text", f"Question {q_id}")),
                    item_type=str(getattr(matching_sample, "type", getattr(matching_sample, "question_type", "MCQ"))).upper(),
                    options=getattr(matching_sample, "options", ["A", "B", "C", "D"]),
                    correct_answer=str(getattr(matching_sample, "answer", getattr(matching_sample, "correct_answer", ans_val))),
                )
                service.create_question(qb_item)
                item_ids.append(q_id)
            else:
                qb_item = QuestionBankItem(
                    id=q_id,
                    course_id="crs-chem-101",
                    concept_id="chem_thermo_first_law",
                    question_text=f"Question {q_id}",
                    item_type="SHORT_ANSWER",
                    correct_answer=str(ans_val),
                )
                service.create_question(qb_item)
                item_ids.append(q_id)

        asmt = Assessment(
            id=submission.assessment_id,
            course_id="crs-chem-101",
            title=f"Assessment {submission.assessment_id}",
            assessment_type=AssessmentType.FORMATIVE,
            total_marks=float(total * 4.0),
            item_ids=item_ids,
        )
        service.create_assessment(asmt)

    attempt = service.start_attempt(submission.assessment_id, submission.student_id)
    completed_attempt = service.submit_attempt(attempt.id, submission.answers, submission.student_id)

    return ApiResponse(
        ok=True,
        data=AssessmentSubmitResponse(
            assessment_id=completed_attempt.assessment_id,
            student_id=completed_attempt.student_id,
            score=completed_attempt.score,
            total_questions=total,
            passed=completed_attempt.passed,
            feedback={"general": "Assessment graded successfully."},
            item_results=completed_attempt.item_results,
            reassessment_recommendations=completed_attempt.reassessment_recommendations,
        ),
    )
