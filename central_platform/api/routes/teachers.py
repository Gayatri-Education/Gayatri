"""Gayatri AI Platform — Teachers API Endpoints (Phase 02)."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from central_platform.api.schemas import (
    AlertResolveRequest,
    ApiResponse,
    TeacherDashboardResponse,
    TeacherInstructionCreateRequest,
    TeacherInstructionResponse,
    TeacherInstructionToggleRequest,
)
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

router = APIRouter(prefix="/teachers", tags=["Teachers"])

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
async def get_teacher_dashboard(course_id: str = "crs-chem-101"):
    """Retrieve full teacher dashboard analytics, alerts, and student roster."""
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
async def create_instruction(req: TeacherInstructionCreateRequest):
    """Dispatch a pedagogical directive from teacher to student(s)."""
    inst_id = f"inst-{uuid.uuid4().hex[:6]}"
    inst = TeacherInstruction(
        instruction_id=inst_id,
        teacher_id="tchr-101",
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
):
    """Get active instructions scoped to a student or course."""
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
async def toggle_instruction(req: TeacherInstructionToggleRequest):
    """Enable or disable a teacher instruction."""
    success = _instruction_engine.toggle_instruction(req.instruction_id, req.active)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")
    return ApiResponse(ok=True, data={"instruction_id": req.instruction_id, "active": req.active})


@router.post("/alerts/resolve", response_model=ApiResponse[dict])
async def resolve_alert(req: AlertResolveRequest):
    """Resolve an intervention alert."""
    success = _intervention_engine.resolve_alert(req.alert_id, req.resolution_note)
    return ApiResponse(ok=True, data={"alert_id": req.alert_id, "resolved": success})


@router.get("/copilot/briefing", response_model=ApiResponse[Dict[str, Any]])
async def get_copilot_briefing(student_id: Optional[str] = None):
    """Generate diagnostic AI Copilot briefing for a student or cohort."""
    if student_id:
        resp = _copilot.query(f"What are the weaknesses of student {student_id}?")
    else:
        resp = _copilot.query("Summarize overall cohort progress and critical misconceptions.")
    return ApiResponse(ok=True, data=resp.to_dict())
