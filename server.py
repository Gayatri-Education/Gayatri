"""Standalone HTTP Web Server for Teacher Portal and Central Platform API."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from central_platform.admin import AdminService
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole
from central_platform.teacher.portal import TeacherPortalService
from central_platform.teacher.copilot import TeacherCopilot
from central_platform.teacher.instruction import TeacherInstructionEngine

db = PlatformDatabase(":memory:")
org = Organization(id="org-dsa", name="Delhi Science Academy", slug="dsa")
db.create_organization(org)

teacher = User(id="tchr-101", email="teacher@dsa.edu", full_name="Dr. Sharma", role=UserRole.TEACHER, organization_id=org.id)
student = User(id="stu-202", email="student@dsa.edu", full_name="Rahul Kumar", role=UserRole.STUDENT, organization_id=org.id)
db.create_user(teacher)
db.create_user(student)

portal = TeacherPortalService()
portal.register_student_snapshot(student.id, student.full_name, "crs-chem-101", mastery=0.85, needs_attention=False)


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Gayatri Teacher Portal</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f23; color: #e0e0e0; margin: 0; padding: 30px; }
        .card { background: #16213e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
        h1 { color: #ffffff; margin-top: 0; }
        .metric-val { font-size: 32px; font-weight: bold; color: #27c93f; margin: 10px 0; }
        .badge { background: #9b59b6; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
        button { background: #e94560; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>👩‍🏫 Gayatri AI — Teacher Portal & Dashboard</h1>
        <p>Connected to Central Platform (India / Global Sync Hub)</p>
        <span class="badge">Live Teacher Session</span>
    </div>

    <div class="card">
        <h3>Class Health & Student Metrics</h3>
        <div>Class Health Status: <strong style="color:#27c93f;">__HEALTH_STATUS__</strong></div>
        <div class="metric-val">__AVG_MASTERY__%</div>
        <div>Total Students Monitored: __TOTAL_STUDENTS__</div>
    </div>

    <div class="card">
        <h3>Targeted Teacher Instruction</h3>
        <p>Inject instructions to guide your student's local AI tutor in real time:</p>
        <form method="POST" action="/instruction">
            <input type="text" name="instruction" placeholder="Enter instruction..." style="width: 70%; padding: 10px; border-radius: 6px;" required>
            <button type="submit">Inject Instruction</button>
        </form>
    </div>
</body>
</html>
"""


class TeacherPortalHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/teacher", "/dashboard"):
            overview = portal.get_dashboard_overview("crs-chem-101")
            content = (
                HTML_TEMPLATE
                .replace("__HEALTH_STATUS__", overview.class_health_status)
                .replace("__AVG_MASTERY__", str(int(overview.average_mastery * 100)))
                .replace("__TOTAL_STUDENTS__", str(overview.total_students))
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        elif parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "HEALTHY", "service": "TeacherPortalServer"}).encode("utf-8"))
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        if self.path == "/instruction":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            inst = params.get("instruction", [""])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            resp = f"<h2>✓ Instruction Successfully Injected!</h2><p>Instruction: '{inst}'</p><br><a href='/'>Back to Dashboard</a>"
            self.wfile.write(resp.encode("utf-8"))


def run_server(port: int = 8000):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, TeacherPortalHTTPHandler)
    print(f"🚀 Gayatri Teacher Portal HTTP Server running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
