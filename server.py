"""Standalone HTTP Web Server for Teacher Portal and Central Platform API.

Comprehensive Teacher Command Center & Cohort Learning Analytics Engine.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole
from central_platform.sync.manager import SyncEvent, SyncManager
from central_platform.teacher.copilot import CopilotCitation, CopilotResponse, TeacherCopilot
from central_platform.teacher.instruction import TeacherInstruction, TeacherInstructionEngine
from central_platform.teacher.intervention import (
    AlertSeverity,
    AlertStatus,
    TeacherAlert,
    TeacherInterventionEngine,
)
from central_platform.teacher.portal import TeacherPortalService

# Persistent or configurable database path
DB_PATH = os.environ.get("GAYATRI_DB_PATH", ":memory:")
db = PlatformDatabase(DB_PATH)

# Seed default organization and demo roles
org = Organization(id="org-dsa", name="Delhi Science Academy", slug="dsa")
db.create_organization(org)

teacher_user = User(
    id="tchr-101",
    email="teacher@dsa.edu",
    full_name="Dr. Sunita Sharma",
    role=UserRole.TEACHER,
    organization_id=org.id,
)
db.create_user(teacher_user)

# Central Services
portal = TeacherPortalService()
instruction_engine = TeacherInstructionEngine()
intervention_engine = TeacherInterventionEngine()
copilot = TeacherCopilot()
sync_manager = SyncManager()

# Seed Cohort Students in Chemistry 101
cohort = [
    {
        "id": "stu-202",
        "name": "Rahul Kumar",
        "mastery": 0.85,
        "needs_attention": False,
        "misconceptions": [],
        "hints": 2,
        "retention": 0.90,
        "recent": "Solved Hess's Law formation enthalpy",
        "chapters": {"Thermodynamics": 0.88, "Chemical Bonding": 0.84, "Coordination Chemistry": 0.80, "Periodic Trends": 0.90},
    },
    {
        "id": "stu-203",
        "name": "Priya Sharma",
        "mastery": 0.94,
        "needs_attention": False,
        "misconceptions": [],
        "hints": 0,
        "retention": 0.96,
        "recent": "Calculated Gibbs free energy at non-standard T",
        "chapters": {"Thermodynamics": 0.95, "Chemical Bonding": 0.92, "Coordination Chemistry": 0.94, "Periodic Trends": 0.95},
    },
    {
        "id": "stu-204",
        "name": "Amit Patel",
        "mastery": 0.42,
        "needs_attention": True,
        "misconceptions": ["THERMO_SIGN_CONVENTION"],
        "hints": 7,
        "retention": 0.60,
        "recent": "Failed sign convention in expansion work (ΔU)",
        "chapters": {"Thermodynamics": 0.36, "Chemical Bonding": 0.52, "Coordination Chemistry": 0.38, "Periodic Trends": 0.58},
    },
    {
        "id": "stu-205",
        "name": "Ananya Roy",
        "mastery": 0.67,
        "needs_attention": False,
        "misconceptions": ["BOND_ORBITAL_HYBRIDIZATION"],
        "hints": 4,
        "retention": 0.78,
        "recent": "Struggled with sp3d axial/equatorial bond angles",
        "chapters": {"Thermodynamics": 0.70, "Chemical Bonding": 0.62, "Coordination Chemistry": 0.65, "Periodic Trends": 0.76},
    },
    {
        "id": "stu-206",
        "name": "Vikram Seth",
        "mastery": 0.52,
        "needs_attention": True,
        "misconceptions": ["THERMO_REVERSIBLE_WORK"],
        "hints": 5,
        "retention": 0.68,
        "recent": "Confused isothermal reversible with adiabatic work",
        "chapters": {"Thermodynamics": 0.46, "Chemical Bonding": 0.58, "Coordination Chemistry": 0.50, "Periodic Trends": 0.64},
    },
]

for s in cohort:
    user = User(
        id=s["id"],
        email=f"{s['id']}@dsa.edu",
        full_name=s["name"],
        role=UserRole.STUDENT,
        organization_id=org.id,
    )
    db.create_user(user)
    sync_manager.bind_device(f"device-{s['id']}", s["id"])
    portal.register_student_snapshot(
        student_id=s["id"],
        name=s["name"],
        course_id="crs-chem-101",
        mastery=s["mastery"],
        needs_attention=s["needs_attention"],
        misconceptions=s["misconceptions"],
        hint_count=s["hints"],
        retention_rate=s["retention"],
        chapter_mastery=s["chapters"],
        recent_activity=s["recent"],
    )

# Seed Active Alerts
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-001",
        student_id="stu-204",
        course_id="crs-chem-101",
        alert_type="repeated_failure",
        severity=AlertSeverity.CRITICAL,
        message="Amit Patel failed thermodynamic expansion work sign convention 3 times consecutively.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-002",
        student_id="stu-205",
        course_id="crs-chem-101",
        alert_type="prerequisite_weakness",
        severity=AlertSeverity.WARNING,
        message="Ananya Roy requested Tier 4 hint twice for VSEPR orbital geometry in PCl5.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-003",
        student_id="stu-206",
        course_id="crs-chem-101",
        alert_type="mastery_regression",
        severity=AlertSeverity.WARNING,
        message="Vikram Seth experienced a 15% mastery drop in Reversible Expansion Work.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-004",
        student_id="stu-203",
        course_id="crs-chem-101",
        alert_type="advancement_ready",
        severity=AlertSeverity.INFO,
        message="Priya Sharma exceeded 90% mastery across all topics. Ready for JEE Advanced problem set.",
    )
)

# Seed Initial Pedagogical Instructions
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-001",
        teacher_id=teacher_user.id,
        student_id="all",
        course_id="crs-chem-101",
        concept_scope="THERMODYNAMICS",
        instruction_text="Emphasize IUPAC sign conventions: expansion work done BY the system must always be taken as -w.",
        priority=2,
    )
)
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-002",
        teacher_id=teacher_user.id,
        student_id="stu-204",
        course_id="crs-chem-101",
        concept_scope="THERMO_SIGN_CONVENTION",
        instruction_text="Guide Amit through the microscopic piston cylinder model before asking for numerical calculation of ΔU.",
        priority=3,
    )
)
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-003",
        teacher_id=teacher_user.id,
        student_id="stu-205",
        course_id="crs-chem-101",
        concept_scope="BOND_ORBITAL_HYBRIDIZATION",
        instruction_text="Have Ananya compare axial vs equatorial bond repulsions in trigonal bipyramidal molecules.",
        priority=2,
    )
)

from central_platform.teacher.views import (
    HTML_TEMPLATE,
    render_teacher_dashboard_html as _render_teacher_dashboard_html,
)


def render_teacher_dashboard_html(course_id: str = "crs-chem-101") -> str:
    """Render the responsive Teacher Command Center HTML with live cohort data."""
    return _render_teacher_dashboard_html(
        course_id=course_id,
        portal_service=portal,
        instruction_engine=instruction_engine,
        intervention_engine=intervention_engine,
    )



class TeacherPortalHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Teacher Dashboard and Central Sync API."""

    def log_message(self, format: str, *args) -> None:
        """Suppress noisy default logging."""
        return

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path in ("/", "/teacher", "/dashboard"):
                content = render_teacher_dashboard_html("crs-chem-101")
                payload = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            elif path == "/api/health":
                overview = portal.get_dashboard_overview("crs-chem-101")
                self._send_json({
                    "status": "HEALTHY",
                    "service": "TeacherPortalServer",
                    "students_monitored": overview.total_students,
                    "active_instructions": len(instruction_engine.get_all_instructions()),
                    "active_alerts": len([a for a in intervention_engine.get_all_alerts("crs-chem-101") if a.status != AlertStatus.RESOLVED]),
                })

            elif path == "/api/teacher/dashboard":
                query = parse_qs(parsed.query)
                course_id = query.get("course_id", ["crs-chem-101"])[0]
                overview = portal.get_dashboard_overview(course_id)
                students = portal.get_all_students(course_id)
                alerts = [
                    {
                        "alert_id": a.alert_id,
                        "student_id": a.student_id,
                        "severity": a.severity.value,
                        "alert_type": a.alert_type,
                        "message": a.message,
                        "status": a.status.value,
                        "created_at": a.created_at,
                    }
                    for a in intervention_engine.get_all_alerts(course_id)
                ]
                self._send_json({
                    "ok": True,
                    "course_id": course_id,
                    "total_students": overview.total_students,
                    "students_needing_attention": overview.students_needing_attention,
                    "average_mastery": overview.average_mastery,
                    "active_alerts_count": overview.active_alerts_count,
                    "class_health_status": overview.class_health_status,
                    "mastered_count": overview.mastered_count,
                    "progressing_count": overview.progressing_count,
                    "critical_count": overview.critical_count,
                    "chapter_averages": overview.chapter_averages,
                    "top_misconceptions": overview.top_misconceptions,
                    "students": students,
                    "alerts": alerts,
                })

            elif path == "/api/teacher/instructions":
                query = parse_qs(parsed.query)
                student_id = query.get("student_id", [None])[0]
                course_id = query.get("course_id", ["crs-chem-101"])[0]

                if student_id:
                    active = instruction_engine.get_instructions_for_student(student_id, course_id)
                else:
                    active = [i for i in instruction_engine.get_all_instructions() if i.is_active]

                serialized = [
                    {
                        "instruction_id": i.instruction_id,
                        "teacher_id": i.teacher_id,
                        "student_id": i.student_id,
                        "course_id": i.course_id,
                        "concept_scope": i.concept_scope,
                        "instruction_text": i.instruction_text,
                        "priority": i.priority,
                        "created_at": i.created_at,
                    }
                    for i in active
                ]
                self._send_json({"ok": True, "instructions": serialized})

            else:
                self.send_error(404, "Page Not Found")
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else ""

            if path == "/instruction":
                params = parse_qs(body)
                inst_text = params.get("instruction", [""])[0].strip()
                student_id = params.get("student_id", ["all"])[0]
                scope = params.get("concept_scope", ["ALL"])[0]
                priority = int(params.get("priority", [2])[0])

                if inst_text:
                    new_inst = TeacherInstruction(
                        instruction_id=f"inst-{uuid.uuid4().hex[:6]}",
                        teacher_id=teacher_user.id,
                        student_id=student_id,
                        course_id="crs-chem-101",
                        concept_scope=scope if scope != "ALL" else None,
                        instruction_text=inst_text,
                        priority=priority,
                    )
                    instruction_engine.add_instruction(new_inst)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/instruction/toggle":
                params = parse_qs(body)
                inst_id = params.get("instruction_id", [""])[0]
                if inst_id:
                    instruction_engine.toggle_instruction(inst_id)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/alert/resolve":
                params = parse_qs(body)
                alert_id = params.get("alert_id", [""])[0]
                if alert_id:
                    intervention_engine.resolve_alert(alert_id)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/api/teacher/instruction":
                data = json.loads(body)
                text = data.get("instruction", "").strip()
                if not text:
                    self._send_json({"ok": False, "error": "Instruction text is required"}, status=400)
                    return

                new_inst = TeacherInstruction(
                    instruction_id=data.get("instruction_id", f"inst-{uuid.uuid4().hex[:6]}"),
                    teacher_id=data.get("teacher_id", teacher_user.id),
                    student_id=data.get("student_id", "all"),
                    course_id=data.get("course_id", "crs-chem-101"),
                    concept_scope=data.get("concept_scope"),
                    instruction_text=text,
                    priority=int(data.get("priority", 2)),
                )
                instruction_engine.add_instruction(new_inst)
                self._send_json({"ok": True, "instruction_id": new_inst.instruction_id})

            elif path == "/api/teacher/alert/resolve":
                data = json.loads(body)
                aid = data.get("alert_id")
                if aid and intervention_engine.resolve_alert(aid):
                    self._send_json({"ok": True, "message": "Alert resolved"})
                else:
                    self._send_json({"ok": False, "error": "Alert not found"}, status=404)

            elif path == "/api/student/snapshot":
                data = json.loads(body)
                sid = data.get("student_id", "stu-202")
                name = data.get("student_name", "Student")
                course_id = data.get("course_id", "crs-chem-101")
                mastery = float(data.get("mastery", 0.75))
                needs_attention = bool(data.get("needs_attention", False))

                portal.register_student_snapshot(
                    student_id=sid,
                    name=name,
                    course_id=course_id,
                    mastery=mastery,
                    needs_attention=needs_attention,
                    misconceptions=data.get("misconceptions", []),
                    hint_count=int(data.get("hint_count", 0)),
                    retention_rate=float(data.get("retention_rate", 0.85)),
                )
                self._send_json({"ok": True, "message": "Snapshot updated"})

            elif path == "/api/sync/events":
                data = json.loads(body)
                events_data = data.get("events", [])
                for ev in events_data:
                    event = SyncEvent(
                        event_id=ev["event_id"],
                        student_id=ev["student_id"],
                        device_id=ev["device_id"],
                        event_type=ev["event_type"],
                        payload=ev.get("payload", {}),
                    )
                    sync_manager.queue_offline_event(event)

                result = sync_manager.process_sync()
                self._send_json({"ok": True, "sync_result": result})

            else:
                self.send_error(404, "Endpoint Not Found")
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)


def run_server(port: int = 8000) -> None:
    try:
        from central_platform.api.server import run_server as _canonical_run_server
        _canonical_run_server(port=port)
    except Exception as exc:
        print(f"[FALLBACK] Uvicorn launch ({exc}), falling back to HTTPServer...")
        server_address = ("0.0.0.0", port)
        httpd = HTTPServer(server_address, TeacherPortalHTTPHandler)
        print(f"[ONLINE] Gayatri Teacher Portal HTTP Server running at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)

