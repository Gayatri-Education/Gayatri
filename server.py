"""Standalone HTTP Web Server for Teacher Portal and Central Platform API.

Supports cross-device synchronization between Student devices (e.g. USA)
and Teacher Portal (e.g. India) via HTTP REST APIs.
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
from central_platform.teacher.copilot import TeacherCopilot
from central_platform.teacher.instruction import TeacherInstruction, TeacherInstructionEngine
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
    full_name="Dr. Sharma",
    role=UserRole.TEACHER,
    organization_id=org.id,
)
student_user = User(
    id="stu-202",
    email="student@dsa.edu",
    full_name="Rahul Kumar",
    role=UserRole.STUDENT,
    organization_id=org.id,
)
db.create_user(teacher_user)
db.create_user(student_user)

# Central Services
portal = TeacherPortalService()
instruction_engine = TeacherInstructionEngine()
sync_manager = SyncManager()

# Bind demo student device
sync_manager.bind_device("device-usa-student", student_user.id)
portal.register_student_snapshot(
    student_user.id,
    student_user.full_name,
    "crs-chem-101",
    mastery=0.85,
    needs_attention=False,
)

# Seed initial pedagogical instruction
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-seed-01",
        teacher_id=teacher_user.id,
        student_id=student_user.id,
        course_id="crs-chem-101",
        instruction_text="Emphasize IUPAC nomenclature rules for stereoisomers and sign conventions in Thermodynamics.",
        priority=2,
    )
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gayatri AI — Teacher Portal & Live Synchronizer</title>
    <style>
        :root {
            --bg: #0c0d1e;
            --card-bg: #14162e;
            --card-border: #23274c;
            --accent: #9b59b6;
            --accent-hover: #8e44ad;
            --text-main: #f0f2f8;
            --text-sub: #9ca3af;
            --green: #27c93f;
            --yellow: #f5a623;
            --red: #ff5f56;
            --cyan: #00d2d3;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 32px 24px;
            line-height: 1.6;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        .header-card {
            background: linear-gradient(135deg, #181a3a 0%, #2b1f48 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .title-group h1 { margin: 0 0 6px 0; font-size: 26px; color: #fff; }
        .title-group p { margin: 0; color: var(--text-sub); font-size: 14px; }
        .badge {
            background: rgba(155, 89, 182, 0.2);
            color: #d8b4e2;
            border: 1px solid var(--accent);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .badge-dot {
            width: 8px; height: 8px; border-radius: 50%; background: var(--green);
            box-shadow: 0 0 8px var(--green);
        }
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px;
        }
        .metric-label { font-size: 13px; font-weight: 600; color: var(--text-sub); text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-val { font-size: 34px; font-weight: 700; margin: 8px 0; }
        .metric-sub { font-size: 13px; color: var(--text-sub); }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .card h2 { margin-top: 0; font-size: 19px; color: #fff; display: flex; align-items: center; gap: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 14px; }
        th { text-align: left; padding: 12px 14px; background: #1c1f40; color: #adb5bd; border-bottom: 2px solid var(--card-border); font-weight: 600; }
        td { padding: 12px 14px; border-bottom: 1px solid var(--card-border); }
        tr:hover td { background: rgba(255,255,255,0.02); }
        .status-pill {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }
        .pill-good { background: rgba(39, 201, 63, 0.15); color: #27c93f; }
        .pill-warn { background: rgba(245, 166, 35, 0.15); color: #f5a623; }
        .pill-crit { background: rgba(255, 95, 86, 0.15); color: #ff5f56; }
        .form-row { display: flex; gap: 12px; margin-top: 14px; flex-wrap: wrap; }
        input[type="text"], select {
            background: #0d0f22;
            border: 1px solid #2e3360;
            border-radius: 8px;
            padding: 12px 16px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        input[type="text"]:focus, select:focus { border-color: var(--accent); }
        button, input[type="submit"] {
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 22px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover, input[type="submit"]:hover { background: var(--accent-hover); }
        .instructions-list { margin-top: 16px; display: flex; flex-direction: column; gap: 10px; }
        .instruction-item {
            background: #1a1c3b;
            border-left: 4px solid var(--accent);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }
        .sync-guide {
            background: #111429;
            border: 1px dashed #3a3f75;
            border-radius: 12px;
            padding: 20px;
            margin-top: 12px;
            font-size: 13px;
        }
        .code-snippet {
            background: #080914;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: Consolas, monospace;
            color: #61afef;
            display: inline-block;
            margin: 4px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header-card">
            <div class="title-group">
                <h1>👩‍🏫 Gayatri AI — Teacher Portal & Live Sync Hub</h1>
                <p>Central Platform Synchronizer • Real-Time Pedagogical Orchestration</p>
            </div>
            <div class="badge">
                <span class="badge-dot"></span>
                Server Online & Listening (Port 8000)
            </div>
        </div>

        <!-- Metric Cards -->
        <div class="grid-3">
            <div class="metric-card">
                <div class="metric-label">Class Health Status</div>
                <div class="metric-val" style="color: __HEALTH_COLOR__;">__HEALTH_STATUS__</div>
                <div class="metric-sub">Class 11 & 12 Chemistry Cohort</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average Class Mastery</div>
                <div class="metric-val" style="color: var(--cyan);">__AVG_MASTERY__%</div>
                <div class="metric-sub">Across __TOTAL_STUDENTS__ registered students</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Active Pedagogical Directives</div>
                <div class="metric-val" style="color: var(--accent);">__TOTAL_INSTRUCTIONS__</div>
                <div class="metric-sub">Guiding local AI tutors in real time</div>
            </div>
        </div>

        <!-- Student Roster & Live Snapshot -->
        <div class="card">
            <h2><span>📊</span> Monitored Students Roster & Live Mastery</h2>
            <table>
                <thead>
                    <tr>
                        <th>Student Name</th>
                        <th>Student ID</th>
                        <th>Course</th>
                        <th>Mastery Level</th>
                        <th>Attention Status</th>
                    </tr>
                </thead>
                <tbody>
                    __STUDENT_ROWS__
                </tbody>
            </table>
        </div>

        <!-- Teacher Instruction Injection Box -->
        <div class="card">
            <h2><span>📝</span> Inject Targeted Teacher Instruction</h2>
            <p style="color: var(--text-sub); font-size: 14px; margin-top: 0;">
                Inject priority instructions directly into your student's local AI tutor session. The student's Gayatri AI will prioritize your directives during conversations and explanations.
            </p>
            <form method="POST" action="/instruction">
                <div class="form-row">
                    <select name="student_id" style="min-width: 180px;">
                        __STUDENT_OPTIONS__
                    </select>
                    <input type="text" name="instruction" placeholder="e.g. Focus on Hess's Law and emphasize sign conventions..." style="flex: 1; min-width: 280px;" required>
                    <select name="priority" style="min-width: 120px;">
                        <option value="1">Normal (1)</option>
                        <option value="2" selected>High (2)</option>
                        <option value="3">Urgent (3)</option>
                    </select>
                    <input type="submit" value="Inject Directive">
                </div>
            </form>

            <h3 style="margin-top: 24px; font-size: 16px; color: #fff;">Active Pedagogical Instructions</h3>
            <div class="instructions-list">
                __INSTRUCTION_ITEMS__
            </div>
        </div>

        <!-- Cross-Device Sync Setup Guide -->
        <div class="card">
            <h2><span>🌐</span> Cross-Device & International Sync Guide (USA ⇄ India)</h2>
            <div class="sync-guide">
                <strong style="color: #fff; font-size: 14px;">How Student in USA & Teacher in India Sync Data:</strong>
                <ol style="padding-left: 20px; margin: 10px 0;">
                    <li><strong>Direct Local / Same Network:</strong> Both laptops on the same Wi-Fi can sync using the host machine's Local IP address: <span class="code-snippet">http://&lt;HOST_IP&gt;:8000</span>.</li>
                    <li><strong>International / Separate Networks (USA & India):</strong>
                        To connect across the globe with zero firewall hassle, use a free secure tunnel:
                        <br>Run on the server machine: <span class="code-snippet">npx localtunnel --port 8000</span> or <span class="code-snippet">ngrok http 8000</span>
                        <br>Share the generated public HTTPS URL with the student's laptop in USA.
                    </li>
                    <li><strong>Zero-Config GitHub / Sync Endpoint:</strong> Student's desktop app automatically POSTs progress snapshots to <span class="code-snippet">/api/student/snapshot</span> and receives teacher instructions via <span class="code-snippet">/api/teacher/instructions</span>.</li>
                </ol>
            </div>
        </div>
    </div>
</body>
</html>
"""


class TeacherPortalHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Teacher Dashboard and Central Sync API."""

    def log_message(self, format: str, *args) -> None:
        """Suppress noisy default logging, keep concise output."""
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
                overview = portal.get_dashboard_overview("crs-chem-101")
                students = portal.get_all_students("crs-chem-101")
                instructions = instruction_engine.get_all_instructions()

                # Health Color
                health_color = "var(--green)"
                if overview.class_health_status == "Attention Needed":
                    health_color = "var(--yellow)"
                elif overview.class_health_status == "Critical":
                    health_color = "var(--red)"

                # Build Student Rows & Options
                student_rows = []
                student_options = []
                for s in students:
                    status_pill = (
                        '<span class="status-pill pill-warn">Attention Needed</span>'
                        if s["needs_attention"]
                        else '<span class="status-pill pill-good">On Track</span>'
                    )
                    student_rows.append(
                        f"<tr>"
                        f"<td><strong>{s['name']}</strong></td>"
                        f"<td><code>{s['id']}</code></td>"
                        f"<td>{s['course_id']}</td>"
                        f"<td><strong>{int(s['mastery'] * 100)}%</strong></td>"
                        f"<td>{status_pill}</td>"
                        f"</tr>"
                    )
                    student_options.append(f"<option value='{s['id']}'>{s['name']} ({s['id']})</option>")

                # Build Instruction Items
                instruction_items = []
                for inst in instructions:
                    status_badge = (
                        "<span style='color: var(--green); font-weight: 600;'>● Active</span>"
                        if inst.is_active
                        else "<span style='color: var(--text-sub);'>Inactive</span>"
                    )
                    instruction_items.append(
                        f"<div class='instruction-item'>"
                        f"  <div>"
                        f"    <div style='font-size: 14px; font-weight: 600; color: #fff;'>\"{inst.instruction_text}\"</div>"
                        f"    <div style='font-size: 12px; color: var(--text-sub); margin-top: 4px;'>"
                        f"      Target: <code>{inst.student_id}</code> | Priority: {inst.priority} | Created: {inst.created_at[:19]}"
                        f"    </div>"
                        f"  </div>"
                        f"  <div>{status_badge}</div>"
                        f"</div>"
                    )

                content = (
                    HTML_TEMPLATE
                    .replace("__HEALTH_STATUS__", overview.class_health_status)
                    .replace("__HEALTH_COLOR__", health_color)
                    .replace("__AVG_MASTERY__", str(int(overview.average_mastery * 100)))
                    .replace("__TOTAL_STUDENTS__", str(overview.total_students))
                    .replace("__TOTAL_INSTRUCTIONS__", str(len([i for i in instructions if i.is_active])))
                    .replace("__STUDENT_ROWS__", "\n".join(student_rows) if student_rows else "<tr><td colspan='5'>No students registered yet</td></tr>")
                    .replace("__STUDENT_OPTIONS__", "\n".join(student_options) if student_options else "<option value='stu-202'>Rahul Kumar (stu-202)</option>")
                    .replace("__INSTRUCTION_ITEMS__", "\n".join(instruction_items) if instruction_items else "<div style='color: var(--text-sub);'>No active teacher instructions.</div>")
                )

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
                })

            elif path == "/api/teacher/dashboard":
                query = parse_qs(parsed.query)
                course_id = query.get("course_id", ["crs-chem-101"])[0]
                overview = portal.get_dashboard_overview(course_id)
                students = portal.get_all_students(course_id)
                self._send_json({
                    "ok": True,
                    "course_id": course_id,
                    "total_students": overview.total_students,
                    "students_needing_attention": overview.students_needing_attention,
                    "average_mastery": overview.average_mastery,
                    "active_alerts_count": overview.active_alerts_count,
                    "class_health_status": overview.class_health_status,
                    "students": students,
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
                # Form submission from Web UI
                params = parse_qs(body)
                inst_text = params.get("instruction", [""])[0].strip()
                student_id = params.get("student_id", [student_user.id])[0]
                priority = int(params.get("priority", [2])[0])

                if inst_text:
                    new_inst = TeacherInstruction(
                        instruction_id=f"inst-{uuid.uuid4().hex[:6]}",
                        teacher_id=teacher_user.id,
                        student_id=student_id,
                        course_id="crs-chem-101",
                        instruction_text=inst_text,
                        priority=priority,
                    )
                    instruction_engine.add_instruction(new_inst)

                # 303 See Other redirect back to dashboard
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/api/teacher/instruction":
                # JSON API to inject instruction
                data = json.loads(body)
                text = data.get("instruction", "").strip()
                if not text:
                    self._send_json({"ok": False, "error": "Instruction text is required"}, status=400)
                    return

                new_inst = TeacherInstruction(
                    instruction_id=data.get("instruction_id", f"inst-{uuid.uuid4().hex[:6]}"),
                    teacher_id=data.get("teacher_id", teacher_user.id),
                    student_id=data.get("student_id", student_user.id),
                    course_id=data.get("course_id", "crs-chem-101"),
                    instruction_text=text,
                    priority=int(data.get("priority", 2)),
                )
                instruction_engine.add_instruction(new_inst)
                self._send_json({"ok": True, "instruction_id": new_inst.instruction_id})

            elif path == "/api/student/snapshot":
                # JSON API for student client app to upload live progress snapshot
                data = json.loads(body)
                sid = data.get("student_id", "stu-202")
                name = data.get("student_name", "Student")
                course_id = data.get("course_id", "crs-chem-101")
                mastery = float(data.get("mastery", 0.75))
                needs_attention = bool(data.get("needs_attention", False))

                portal.register_student_snapshot(sid, name, course_id, mastery, needs_attention)
                self._send_json({"ok": True, "message": "Snapshot updated"})

            elif path == "/api/sync/events":
                # JSON API for offline event queue sync
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
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, TeacherPortalHTTPHandler)
    print(f"[ONLINE] Gayatri Teacher Portal HTTP Server running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
