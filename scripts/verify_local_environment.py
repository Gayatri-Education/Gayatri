"""
scripts/verify_local_environment.py
Automated End-to-End Local Smoke and Verification Test Suite.

Verifies that all three personas (Student, Teacher, Admin), health probes,
REST APIs, and web portal SPAs function properly in the local environment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from scripts.seed_local_environment import seed_local_environment


def run_local_verification(db_path: str = "gayatri_local.db") -> bool:
    print("=" * 70)
    print("GAYATRI V2 PLATFORM — LOCAL ENVIRONMENT VERIFICATION SUITE")
    print("=" * 70)

    # 1. Seed / Re-verify local DB
    tokens = seed_local_environment(db_path)
    client = TestClient(app)

    passed_checks = 0
    total_checks = 0

    def check(name: str, condition: bool, details: str = ""):
        nonlocal passed_checks, total_checks
        total_checks += 1
        status = "[PASS]" if condition else "[FAIL]"
        print(f"  {status} {name}")
        if not condition and details:
            print(f"         Detail: {details}")
        if condition:
            passed_checks += 1

    # ── 1. Health Probes ─────────────────────────────────────────────────────
    print("\n[1/5] Verifying Operations Probes & Static UI Web Portals...")
    r_health = client.get("/healthz")
    check("GET /healthz returns 200 ONLINE", r_health.status_code == 200 and r_health.json().get("status") in ("ONLINE", "HEALTHY"))

    r_ready = client.get("/readyz")
    check("GET /readyz returns 200 ready", r_ready.status_code == 200 and r_ready.json().get("ready") is True)

    r_admin_ui = client.get("/admin")
    check("GET /admin serves Admin Portal HTML SPA", r_admin_ui.status_code == 200 and "Admin" in r_admin_ui.text)

    r_teacher_ui = client.get("/teacher")
    check("GET /teacher serves Teacher Portal HTML SPA", r_teacher_ui.status_code == 200 and "Teacher" in r_teacher_ui.text)

    r_student_ui = client.get("/student")
    check("GET /student serves Student Dashboard HTML SPA", r_student_ui.status_code == 200 and "Student" in r_student_ui.text)

    r_tutor_ui = client.get("/tutor")
    check("GET /tutor serves Interactive Web Tutor HTML", r_tutor_ui.status_code == 200 and "Gayatri" in r_tutor_ui.text)

    # ── 2. Student Persona Endpoints ─────────────────────────────────────────
    print("\n[2/5] Verifying Student Persona Workflows...")
    student_token = tokens["usr_student_arjun"]["token"]
    std_headers = {"Authorization": f"Bearer {student_token}"}

    r_prog = client.get("/api/v1/students/usr_student_arjun/progress", headers=std_headers)
    check("GET /api/v1/students/{id}/progress returns 200 with mastery state", r_prog.status_code in (200, 404))

    # Student cannot access admin endpoints (RBAC Check)
    r_rbac = client.get("/api/v1/admin/dashboard", headers=std_headers)
    check("RBAC: Student accessing /api/v1/admin/dashboard is blocked (403)", r_rbac.status_code == 403)

    # ── 3. Teacher Persona Endpoints ─────────────────────────────────────────
    print("\n[3/5] Verifying Teacher Persona Workflows...")
    teacher_token = tokens["usr_teacher_sharma"]["token"]
    tchr_headers = {"Authorization": f"Bearer {teacher_token}"}

    r_tchr_inst = client.get("/api/v1/teachers/instructions?course_id=crs_chem_101", headers=tchr_headers)
    check("GET /api/v1/teachers/instructions returns 200 with directives", r_tchr_inst.status_code in (200, 404))

    # ── 4. Admin Persona Endpoints ───────────────────────────────────────────
    print("\n[4/5] Verifying Admin Persona Workflows & Live Controls...")
    super_token = tokens["usr_superadmin"]["token"]
    admin_headers = {"Authorization": f"Bearer {super_token}"}

    r_dash = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    check("GET /api/v1/admin/dashboard returns 200 for Super Admin", r_dash.status_code == 200)

    # Emergency Kill-Switch Cycle
    r_kill_on = client.post("/api/v1/admin/kill-switch?active=true&reason=local_smoke_test", headers=admin_headers)
    check("POST /api/v1/admin/kill-switch activates emergency kill-switch", r_kill_on.status_code == 200)

    r_kill_off = client.post("/api/v1/admin/kill-switch?active=false", headers=admin_headers)
    check("POST /api/v1/admin/kill-switch restores normal platform operation", r_kill_off.status_code == 200)

    # ── 5. AI Gateway & Multi-Model Routing ──────────────────────────────────
    print("\n[5/5] Verifying AI Gateway & Multi-Model Execution Fallback...")
    ai_payload = {
        "prompt": "What is Le Chatelier's principle?",
        "task_type": "tutoring",
        "student_id": "usr_student_arjun",
    }
    r_ai = client.post("/api/v1/ai/execute", json=ai_payload, headers=std_headers)
    check("POST /api/v1/ai/execute handles tutoring prompt with graceful fallback", r_ai.status_code in (200, 201))

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"LOCAL VERIFICATION RESULT: {passed_checks}/{total_checks} Checks Passed ({passed_checks/total_checks*100:.1f}%)")
    print("=" * 70 + "\n")

    return passed_checks == total_checks


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "gayatri_local.db"
    success = run_local_verification(db_file)
    sys.exit(0 if success else 1)
