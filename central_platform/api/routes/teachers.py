"""Gayatri AI Platform — Teachers API Endpoints (Phase 04).

Master Plan Section 13:
- Role-based gatekeeping (TEACHER, ORG_ADMIN, SUPER_ADMIN)
- Student access blocked (student -> teacher 403 Forbidden)
- Teacher cohort and assignment resource scoping (teacher -> unrelated student 403 Forbidden)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from central_platform.api.schemas import (
    AlertResolveRequest,
    ApiResponse,
    TeacherDashboardResponse,
    TeacherInstructionCreateRequest,
    TeacherInstructionResponse,
    TeacherInstructionToggleRequest,
    TeacherInstructionUpdateRequest,
    TeacherInstructionValidateRequest,
    TeacherInstructionValidateResponse,
)
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
    get_db,
)
from central_platform.models.schema import User, UserRole
from central_platform.teacher.portal import TeacherPortalService
from central_platform.teacher.instruction import (
    InstructionStatus,
    SafetyStatus,
    TeacherInstruction,
    TeacherInstructionEngine,
    TeacherInstructionValidator,
)
from central_platform.teacher.intervention import (
    TeacherAlert,
    TeacherInterventionEngine,
)
from central_platform.teacher.copilot import TeacherCopilot
from central_platform.slr.service import SLRService

router = APIRouter(prefix="/teachers", tags=["Teachers"])

_slr_service = SLRService()

try:
    from server import (
        portal as _portal_service,
        instruction_engine as _instruction_engine,
        intervention_engine as _intervention_engine,
        copilot as _copilot,
    )
except Exception:
    _portal_service = TeacherPortalService()
    _instruction_engine = TeacherInstructionEngine()
    _intervention_engine = TeacherInterventionEngine()
    _copilot = TeacherCopilot()


@router.get("/dashboard", response_model=ApiResponse[TeacherDashboardResponse])
async def get_teacher_dashboard(
    course_id: str = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve full teacher dashboard analytics, alerts, and student roster."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students are not authorized to access teacher dashboard",
            )
        enforce_resource_boundaries(current_user)

    overview = _portal_service.get_dashboard_overview(course_id)
    students = _portal_service.get_all_students(course_id)
    alerts = _intervention_engine.get_all_alerts(course_id=course_id)

    data = TeacherDashboardResponse(
        total_students=overview.total_students,
        active_today=overview.active_students_today,
        average_mastery=overview.average_mastery,
        critical_alerts_count=overview.critical_alerts_count,
        mastery_distribution=overview.mastery_distribution,
        chapter_averages=overview.chapter_averages,
        recent_alerts=[a.to_dict() for a in alerts],
        students=students,
        students_active=overview.students_active or overview.active_students_today,
        difficult_concepts=overview.difficult_concepts,
        common_misconceptions=overview.common_misconceptions or overview.top_misconceptions,
        recent_activity=overview.recent_activity,
        intervention_alerts=overview.intervention_alerts or [a.to_dict() for a in alerts],
    )
    return ApiResponse(ok=True, data=data)


def _to_instruction_response(i: TeacherInstruction) -> TeacherInstructionResponse:
    return TeacherInstructionResponse(
        instruction_id=i.instruction_id,
        teacher_id=i.teacher_id,
        student_id=i.student_id,
        course_id=i.course_id,
        instruction_text=i.instruction_text,
        priority=i.priority,
        concept_scope=i.concept_scope or "ALL",
        scope_type=getattr(i, "scope_type", "STUDENT"),
        is_active=i.is_active,
        status=getattr(i, "status", InstructionStatus.ACTIVE.value),
        start_at=getattr(i, "start_at", None),
        expires_at=getattr(i, "expires_at", None),
        safety_status=getattr(i, "safety_status", SafetyStatus.VALIDATED.value),
        safety_reasons=getattr(i, "safety_reasons", []),
        audit_trail=getattr(i, "audit_trail", []),
        created_at=i.created_at,
        updated_at=getattr(i, "updated_at", None),
    )


@router.post("/instructions/validate", response_model=ApiResponse[TeacherInstructionValidateResponse])
async def validate_instruction(
    req: TeacherInstructionValidateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Pre-flight policy and safety validation for a teacher directive against the 5 non-overridable invariants."""
    val = TeacherInstructionValidator.validate(req.instruction)
    return ApiResponse(
        ok=True,
        data=TeacherInstructionValidateResponse(
            is_valid=val.is_valid,
            safety_status=val.safety_status,
            violations=val.violations,
            sanitized_text=val.sanitized_text,
            target_invariants=val.target_invariants,
        ),
    )


@router.post("/instructions", response_model=ApiResponse[TeacherInstructionResponse], status_code=status.HTTP_201_CREATED)
async def create_instruction(
    req: TeacherInstructionCreateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Dispatch a pedagogical directive from teacher to student(s) with policy validation and audit logging."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students cannot create teacher instructions",
            )
        if current_user.role == UserRole.TEACHER and req.student_id not in ("all", "*"):
            db = get_db()
            assigned = db.get_assigned_student_ids_for_teacher(current_user.id)
            if assigned and req.student_id not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: student '{req.student_id}' is not assigned to this teacher",
                )

    # Validate against non-overridable invariants
    val = TeacherInstructionValidator.validate(req.instruction)
    if not val.is_valid:
        raise HTTPException(
            status_code=422,
            detail=f"Policy violation: {'; '.join(val.violations)}",
        )

    inst_id = f"inst-{uuid.uuid4().hex[:6]}"
    teacher_id = current_user.id if current_user else "tchr-101"
    
    # Auto-infer scope type if not specified
    if req.scope_type:
        scope_type = req.scope_type
    elif req.student_id in ("all", "*", ""):
        scope_type = "CONCEPT" if req.concept_scope and req.concept_scope not in ("ALL", "*") else "COURSE"
    else:
        scope_type = "CONCEPT" if req.concept_scope and req.concept_scope not in ("ALL", "*") else "STUDENT"

    inst = TeacherInstruction(
        instruction_id=inst_id,
        teacher_id=teacher_id,
        student_id=req.student_id,
        course_id=req.course_id,
        instruction_text=val.sanitized_text,
        priority=req.priority,
        concept_scope=req.concept_scope,
        scope_type=scope_type,
        start_at=req.start_at or datetime.now(timezone.utc).isoformat(),
        expires_at=req.expires_at,
        status=InstructionStatus.ACTIVE.value,
        is_active=True,
        safety_status=val.safety_status,
        safety_reasons=val.violations,
    )
    _instruction_engine.add_instruction(inst, actor_id=teacher_id)

    return ApiResponse(ok=True, data=_to_instruction_response(inst))


@router.get("/instructions", response_model=ApiResponse[List[TeacherInstructionResponse]])
async def get_instructions(
    student_id: Optional[str] = Query(default=None),
    course_id: Optional[str] = Query(default="crs-chem-101"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    active_only: bool = Query(default=False),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get active instructions scoped to a student or course with optional filtering."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            # Student can only see instructions addressed to them or 'all'
            if student_id and student_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: students may only view their own instructions",
                )
            student_id = current_user.id

    if student_id:
        insts = _instruction_engine.get_instructions_for_student(
            student_id=student_id,
            course_id=course_id or "",
        )
    else:
        insts = _instruction_engine.get_all_instructions(
            course_id=course_id,
            student_id=student_id,
            status_filter=status_filter,
            active_only=active_only,
        )

    return ApiResponse(ok=True, data=[_to_instruction_response(i) for i in insts])


@router.get("/instructions/{instruction_id}", response_model=ApiResponse[TeacherInstructionResponse])
async def get_instruction_by_id(
    instruction_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get a single instruction by ID including its immutable audit trail."""
    inst = _instruction_engine.get_instruction(instruction_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")

    if current_user and current_user.role == UserRole.STUDENT:
        if inst.student_id not in (current_user.id, "all", "*"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students cannot view instructions for other students",
            )

    return ApiResponse(ok=True, data=_to_instruction_response(inst))


@router.patch("/instructions/{instruction_id}", response_model=ApiResponse[TeacherInstructionResponse])
async def update_instruction(
    instruction_id: str,
    req: TeacherInstructionUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Update priority, scope, expiration, or status of an instruction."""
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot update instructions",
        )

    actor_id = current_user.id if current_user else "teacher"
    updates = req.dict(exclude_none=True)
    try:
        updated = _instruction_engine.update_instruction(instruction_id, actor_id=actor_id, updates=updates)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")

    return ApiResponse(ok=True, data=_to_instruction_response(updated))


@router.delete("/instructions/{instruction_id}", response_model=ApiResponse[dict])
async def delete_or_revoke_instruction(
    instruction_id: str,
    reason: Optional[str] = Query(default="Revoked by teacher"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Revoke a teacher instruction and record the revocation in its audit log."""
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot revoke teacher instructions",
        )

    actor_id = current_user.id if current_user else "teacher"
    success = _instruction_engine.revoke_instruction(instruction_id, actor_id=actor_id, reason=reason)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")

    return ApiResponse(ok=True, data={"instruction_id": instruction_id, "status": "REVOKED", "revoked": True})


@router.post("/instructions/toggle", response_model=ApiResponse[dict])
async def toggle_instruction(
    req: TeacherInstructionToggleRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Enable or disable a teacher instruction."""
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot toggle teacher instructions",
        )
    success = _instruction_engine.toggle_instruction(req.instruction_id, req.active)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")
    return ApiResponse(ok=True, data={"instruction_id": req.instruction_id, "active": req.active})


@router.post("/alerts/resolve", response_model=ApiResponse[dict])
async def resolve_alert(
    req: AlertResolveRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Resolve an intervention alert."""
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot resolve intervention alerts",
        )
    success = _intervention_engine.resolve_alert(req.alert_id, req.resolution_note)
    return ApiResponse(ok=True, data={"alert_id": req.alert_id, "resolved": success})


@router.get("/copilot/briefing", response_model=ApiResponse[Dict[str, Any]])
async def get_copilot_briefing(
    student_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Generate diagnostic AI Copilot briefing for a student or cohort."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students cannot access teacher copilot briefing",
            )
        if current_user.role == UserRole.TEACHER and student_id:
            db = get_db()
            assigned = db.get_assigned_student_ids_for_teacher(current_user.id)
            if assigned and student_id not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: student '{student_id}' is not assigned to this teacher",
                )

    if student_id:
        resp = _copilot.query(f"What are the weaknesses of student {student_id}?")
    else:
        resp = _copilot.query("Summarize overall cohort progress and critical misconceptions.")
    return ApiResponse(ok=True, data=resp.to_dict())


@router.get("/students/{student_id}/slr", response_model=ApiResponse[Dict[str, Any]])
async def get_teacher_student_slr(
    student_id: str,
    course_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve Authoritative SLR for an assigned student."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students cannot use teacher endpoints",
            )
        if current_user.role == UserRole.TEACHER:
            db = get_db()
            assigned = db.get_assigned_student_ids_for_teacher(current_user.id)
            if assigned and student_id not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: student '{student_id}' is not assigned to this teacher",
                )

    slr = _slr_service.get_authoritative_slr(student_id, course_id=course_id)
    return ApiResponse(ok=True, data=slr.to_dict())


@router.get("/students", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_students(
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve cohort roster for the teacher."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students are not authorized to access teacher endpoints",
            )
        enforce_resource_boundaries(current_user)

    students = _portal_service.get_all_students(course_id)
    return ApiResponse(ok=True, data=students)


@router.get("/students/{student_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_teacher_student_detail(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve full Section 19 Student View from Authoritative SLR."""
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: students cannot use teacher endpoints",
            )
        if current_user.role == UserRole.TEACHER:
            db = get_db()
            assigned = db.get_assigned_student_ids_for_teacher(current_user.id)
            if assigned and student_id not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: student '{student_id}' is not assigned to this teacher",
                )

    detail = _portal_service.get_student_detail(student_id, course_id=course_id or "crs-chem-101")
    return ApiResponse(ok=True, data=detail)


@router.get("/students/{student_id}/timeline", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_student_timeline(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("learning_timeline", []))


@router.get("/students/{student_id}/mastery", response_model=ApiResponse[Dict[str, Any]])
async def get_teacher_student_mastery(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("mastery", {}))


@router.get("/students/{student_id}/misconceptions", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_student_misconceptions(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("misconceptions", []))


@router.get("/students/{student_id}/sessions", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_student_sessions(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("sessions", []))


@router.get("/students/{student_id}/interventions", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_student_interventions(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("interventions", []))


@router.get("/students/{student_id}/instructions", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_student_instructions(
    student_id: str,
    course_id: Optional[str] = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    detail = await get_teacher_student_detail(student_id, course_id, current_user)
    return ApiResponse(ok=True, data=detail.data.get("teacher_instructions", []))


@router.get("/assignments", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_assignments(
    course_id: str = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot access teacher assignments management",
        )
    assignments = [
        {"id": "asg-01", "title": "Thermodynamics First Law & Work", "unit": "Unit 6", "due_date": "2026-10-05", "completed_count": 8, "total_count": 12},
        {"id": "asg-02", "title": "Hess's Law Enthalpy Cycles", "unit": "Unit 6", "due_date": "2026-10-12", "completed_count": 5, "total_count": 12},
        {"id": "asg-03", "title": "Periodic Trends & Ionic Radii", "unit": "Unit 3", "due_date": "2026-10-18", "completed_count": 10, "total_count": 12},
    ]
    return ApiResponse(ok=True, data=assignments)


@router.get("/assessments", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_assessments(
    course_id: str = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot access teacher assessments management",
        )
    assessments = [
        {"id": "asm-01", "name": "Diagnostic Quiz 1: Enthalpy & Work", "course_id": course_id, "items_count": 5, "average_score": 0.78, "status": "active"},
        {"id": "asm-02", "name": "Mid-Term Assessment: Chemical Energetics", "course_id": course_id, "items_count": 10, "average_score": 0.65, "status": "draft"},
    ]
    return ApiResponse(ok=True, data=assessments)


@router.get("/alerts", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_teacher_alerts(
    course_id: str = "crs-chem-101",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user and current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: students cannot access teacher alerts",
        )
    alerts = _intervention_engine.get_all_alerts(course_id=course_id)
    return ApiResponse(ok=True, data=[a.to_dict() for a in alerts])

