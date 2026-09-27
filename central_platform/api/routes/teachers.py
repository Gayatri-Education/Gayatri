"""Gayatri AI Platform — Teachers API Endpoints (Phase 04).

Master Plan Section 13:
- Role-based gatekeeping (TEACHER, ORG_ADMIN, SUPER_ADMIN)
- Student access blocked (student -> teacher 403 Forbidden)
- Teacher cohort and assignment resource scoping (teacher -> unrelated student 403 Forbidden)
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from central_platform.api.schemas import (
    AlertResolveRequest,
    ApiResponse,
    TeacherDashboardResponse,
    TeacherInstructionCreateRequest,
    TeacherInstructionResponse,
    TeacherInstructionToggleRequest,
)
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
    get_db,
)
from central_platform.models.schema import User, UserRole
from central_platform.teacher.portal import TeacherPortalService
from central_platform.teacher.instruction import (
    TeacherInstruction,
    TeacherInstructionEngine,
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
    )
    return ApiResponse(ok=True, data=data)


@router.post("/instructions", response_model=ApiResponse[TeacherInstructionResponse], status_code=status.HTTP_201_CREATED)
async def create_instruction(
    req: TeacherInstructionCreateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Dispatch a pedagogical directive from teacher to student(s)."""
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

    inst_id = f"inst-{uuid.uuid4().hex[:6]}"
    teacher_id = current_user.id if current_user else "tchr-101"
    inst = TeacherInstruction(
        instruction_id=inst_id,
        teacher_id=teacher_id,
        student_id=req.student_id,
        course_id=req.course_id,
        instruction_text=req.instruction,
        priority=req.priority,
        concept_scope=req.concept_scope,
        is_active=True,
    )
    _instruction_engine.add_instruction(inst)

    data = TeacherInstructionResponse(
        instruction_id=inst.instruction_id,
        teacher_id=inst.teacher_id,
        student_id=inst.student_id,
        course_id=inst.course_id,
        instruction_text=inst.instruction_text,
        priority=inst.priority,
        concept_scope=inst.concept_scope,
        is_active=inst.is_active,
        created_at=inst.created_at,
    )
    return ApiResponse(ok=True, data=data)


@router.get("/instructions", response_model=ApiResponse[List[TeacherInstructionResponse]])
async def get_instructions(
    student_id: Optional[str] = Query(default=None),
    course_id: Optional[str] = Query(default="crs-chem-101"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get active instructions scoped to a student or course."""
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
        insts = [
            i for i in _instruction_engine._instructions.values()
            if not course_id or i.course_id == course_id or i.course_id in ("all", "*")
        ]

    data = [
        TeacherInstructionResponse(
            instruction_id=i.instruction_id,
            teacher_id=i.teacher_id,
            student_id=i.student_id,
            course_id=i.course_id,
            instruction_text=i.instruction_text,
            priority=i.priority,
            concept_scope=i.concept_scope,
            is_active=i.is_active,
            created_at=i.created_at,
        )
        for i in insts
    ]
    return ApiResponse(ok=True, data=data)


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
