"""End-to-End System Validator executing complete multi-role user journeys."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from central_platform.admin import AdminService
from central_platform.assessment.builder import AssessmentBuilder, AssessmentSubmission, QuestionItem
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, Enrollment, Organization, User, UserRole
from central_platform.slr.record import StudentLearningRecord
from central_platform.sync.manager import SyncEvent, SyncManager
from central_platform.teacher.copilot import TeacherCopilot
from central_platform.teacher.instruction import TeacherInstruction, TeacherInstructionEngine
from central_platform.teacher.intervention import AlertSeverity, AlertStatus, TeacherAlert, TeacherInterventionEngine
from central_platform.teacher.portal import TeacherPortalService
from core.tutor.adaptive_2 import AdaptiveAction, AdaptiveEngineV2, MasteryDimensions


@dataclass
class E2EValidationResult:
    scenario: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class E2EValidator:
    """End-to-end integration validator running full user lifecycle workflows."""

    def __init__(self, db_path: str = ":memory:"):
        self.db = PlatformDatabase(db_path)
        self.admin_service = AdminService(self.db)
        self.sync_manager = SyncManager()
        self.instruction_engine = TeacherInstructionEngine()
        self.intervention_engine = TeacherInterventionEngine()
        self.portal_service = TeacherPortalService()
        self.copilot_service = TeacherCopilot()
        self.assessment_builder = AssessmentBuilder()
        self.adaptive_engine = AdaptiveEngineV2()

    def run_student_lifecycle(self) -> E2EValidationResult:
        # 1. Register & Provision
        org = Organization(id="org-e2e-stu", name="E2E Student Academy", slug="e2e-stu")
        self.db.create_organization(org)

        student = User(
            id="stu-e2e-1",
            email="e2e.student@gayatri.edu",
            full_name="E2E Student",
            role=UserRole.STUDENT,
            organization_id=org.id,
        )
        self.db.create_user(student)

        course = Course(id="crs-chem-101", organization_id=org.id, code="CHEM101", title="Chemistry 101")
        self.db.create_course(course)

        enrollment = Enrollment(id="enr-e2e-1", student_id=student.id, course_id=course.id)
        self.db.create_enrollment(enrollment)

        # 2. Adaptive Learning Session & SLR Recording
        slr = StudentLearningRecord(student.id)
        slr.add_event("evt-1", "concept_attempt", "Completed Hess Law attempt score=0.95", "2026-09-26T10:00:00")

        # 3. Misconception & Adaptation
        initial_mastery = MasteryDimensions(knowledge=0.5, application=0.5)
        new_mastery, action = self.adaptive_engine.evaluate_turn(
            current_mastery=initial_mastery,
            correct=True,
            hints_used=0,
            response_time_ms=12000,
        )

        # 4. Assessment Submission
        q1 = QuestionItem(item_id="q1", concept_id="chem_thermo_hess_law", prompt="State Hess's Law", correct_answer="Independent of pathway")
        self.assessment_builder.add_question(q1)
        self.assessment_builder.create_assessment("midterm-1", ["q1"])

        sub = AssessmentSubmission(
            submission_id="sub-1",
            assessment_id="midterm-1",
            student_id=student.id,
            answers={"q1": "Independent of pathway"},
        )
        submission = self.assessment_builder.submit_assessment(sub)

        # 5. Offline Event Sync
        self.sync_manager.bind_device("dev-e2e-phone", student.id)
        sync_evt = SyncEvent(
            event_id="sync-1",
            student_id=student.id,
            device_id="dev-e2e-phone",
            event_type="offline_quiz_complete",
            payload={"score": 100},
        )
        self.sync_manager.queue_offline_event(sync_evt)
        sync_res = self.sync_manager.process_sync()

        return E2EValidationResult(
            scenario="student_lifecycle",
            passed=submission.ai_score > 0 and sync_res["synced"] == 1,
            details={
                "student_id": student.id,
                "adaptation_action": action.value,
                "assessment_score": submission.ai_score,
                "synced_count": sync_res["synced"],
            },
        )

    def run_teacher_lifecycle(self) -> E2EValidationResult:
        # Provision Teacher and Class
        org = Organization(id="org-e2e-tchr", name="E2E Teacher Academy", slug="e2e-tchr")
        self.db.create_organization(org)

        teacher = User(id="tchr-1", email="teacher@gayatri.edu", full_name="Prof Teacher", role=UserRole.TEACHER, organization_id=org.id)
        student = User(id="stu-2", email="student@gayatri.edu", full_name="Student Two", role=UserRole.STUDENT, organization_id=org.id)
        self.db.create_user(teacher)
        self.db.create_user(student)

        # Register Student Snapshot in Portal
        self.portal_service.register_student_snapshot(student.id, student.full_name, "crs-chem-101", 0.45, needs_attention=True)

        # Dashboard Overview
        dashboard = self.portal_service.get_dashboard_overview("crs-chem-101")

        # Raise Intervention Alert
        alert = TeacherAlert(
            alert_id="alt-1",
            student_id=student.id,
            course_id="crs-chem-101",
            alert_type="repeated_failure",
            severity=AlertSeverity.WARNING,
            message="Student struggling with equilibrium constants",
        )
        self.intervention_engine.raise_alert(alert)

        # Instruction Injection
        instruction = TeacherInstruction(
            instruction_id="inst-1",
            teacher_id=teacher.id,
            student_id=student.id,
            course_id="crs-chem-101",
            instruction_text="Provide step-by-step scaffolding for equilibrium constants",
        )
        self.instruction_engine.add_instruction(instruction)

        # Copilot Query over SLR
        slr = StudentLearningRecord(student.id)
        slr.add_event("evt-struggle", "mistake", "Struggled with Equilibrium constants calculation", "2026-09-26T11:00:00")
        self.copilot_service.register_learning_record(slr)
        copilot_reply = self.copilot_service.summarize_student_sessions(student.id)

        return E2EValidationResult(
            scenario="teacher_lifecycle",
            passed=dashboard.total_students == 1 and len(copilot_reply.citations) > 0,
            details={
                "dashboard_status": dashboard.class_health_status,
                "alert_id": alert.alert_id,
                "instruction_id": instruction.instruction_id,
                "citations_count": len(copilot_reply.citations),
            },
        )
