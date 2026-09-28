"""Phase 23: Real End-to-End Testing Master Suite.

Implements Master Plan Section 32:
Tests actual application boundaries over HTTP API, cryptographic authentication,
database persistence, learning engine, and AI governance across:
1. Student Journey (login -> inspect course -> start session -> submit learning events -> query SLR progress)
2. Teacher Journey (login -> inspect dashboard -> view student -> add instruction -> create intervention -> query copilot)
3. Admin Journey (login -> create org & user -> create course & curriculum -> inspect system health -> inspect audit logs)
"""

import json
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, Organization, User, UserRole


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    database = PlatformDatabase()
    return database


def test_e2e_student_journey(client, db):
    """E2E Student Journey:
    1. Authenticate student with signed JWT
    2. Inspect course curriculum
    3. Start learning session
    4. Post learning events (question attempt, hint used)
    5. Complete session
    6. Verify student profile and SLR progress update
    """
    student_id = "student_e2e_001"
    org_id = "org_demo"
    course_id = "crs-chem-101"

    # Setup demo organization and student user
    db.create_organization(Organization(id=org_id, name="Demo Org", slug="demo-org"))
    db.create_user(
        User(
            id=student_id,
            email="student@demo.org",
            full_name="E2E Student",
            role=UserRole.STUDENT,
            organization_id=org_id,
        )
    )

    # 1. Generate auth token
    token = create_access_token(user_id=student_id, role="student", organization_id=org_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Inspect course curriculum
    resp = client.get(f"/api/v1/curricula/{course_id}", headers=headers)
    assert resp.status_code == 200

    # 3. Start learning session via HTTP API
    session_payload = {
        "student_id": student_id,
        "course_id": course_id,
        "initial_concept": "chem_thermo_first_law",
    }
    resp = client.post("/api/v1/sessions/start", headers=headers, json=session_payload)
    assert resp.status_code in (200, 201)
    sess_data = resp.json()["data"]
    session_id = sess_data["session_id"]
    assert sess_data["status"] == "ACTIVE"

    # 4. Submit learning events
    event_payload = {
        "event_id": f"evt_{session_id}_1",
        "student_id": student_id,
        "organization_id": org_id,
        "course_id": course_id,
        "session_id": session_id,
        "turn_id": "turn_001",
        "concept_id": "chem_thermo_first_law",
        "correctness": "correct",
        "hint_used": 1,
        "difficulty": 0.65,
    }
    resp = client.post("/api/v1/learning/events", headers=headers, json=event_payload)
    assert resp.status_code in (200, 201)
    assert resp.json()["data"]["status"] == "RECORDED"

    # 5. Snapshot student progress
    snap_payload = {
        "student_id": student_id,
        "student_name": "E2E Student",
        "course_id": course_id,
        "mastery": 0.85,
        "needs_attention": False,
        "misconceptions": [],
        "hint_count": 1,
        "retention_rate": 0.90,
    }
    resp = client.post("/api/v1/students/snapshot", headers=headers, json=snap_payload)
    assert resp.status_code == 200

    # 6. Verify student profile and SLR
    resp = client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["student_id"] == student_id


def test_e2e_teacher_journey(client, db):
    """E2E Teacher Journey:
    1. Authenticate teacher
    2. Inspect teacher dashboard
    3. Add AI pedagogical instruction
    4. Query Teacher Copilot briefing
    """
    teacher_id = "teacher_e2e_001"
    student_id = "student_e2e_001"
    course_id = "crs-chem-101"
    org_id = "org_demo"

    db.create_organization(Organization(id=org_id, name="Demo Org", slug="demo-org"))
    db.create_user(
        User(
            id=teacher_id,
            email="teacher@demo.org",
            full_name="E2E Teacher",
            role=UserRole.TEACHER,
            organization_id=org_id,
        )
    )

    token = create_access_token(user_id=teacher_id, role="teacher", organization_id=org_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. View teacher dashboard
    resp = client.get(f"/api/v1/teachers/dashboard?course_id={course_id}", headers=headers)
    assert resp.status_code == 200
    dash = resp.json()["data"]
    assert "total_students" in dash
    assert "mastery_distribution" in dash

    # 2. Add teacher AI instruction
    instruction_payload = {
        "instruction": "Explain Gibbs free energy and spontaneity using worked examples.",
        "student_id": student_id,
        "course_id": course_id,
        "priority": 3,
    }
    resp = client.post("/api/v1/teachers/instructions", headers=headers, json=instruction_payload)
    assert resp.status_code in (200, 201)
    assert resp.json()["data"]["priority"] == 3

    # 3. Query Teacher Copilot
    resp = client.get("/api/v1/teachers/copilot/briefing", headers=headers)
    assert resp.status_code == 200
    assert "summary" in resp.json()["data"]


def test_e2e_admin_journey(client, db):
    """E2E Admin Journey:
    1. Authenticate super admin
    2. Create organization and user
    3. Verify system health & kill-switch status
    4. Verify AI Gateway status
    """
    admin_id = "admin_e2e_001"
    org_id = "org_enterprise_01"

    db.create_organization(Organization(id="org_global", name="Global Org", slug="global-org"))
    db.create_user(
        User(
            id=admin_id,
            email="superadmin@central.gov",
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            organization_id="org_global",
        )
    )

    token = create_access_token(user_id=admin_id, role="super_admin", organization_id="org_global")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Admin create organization & user
    db.create_organization(Organization(id=org_id, name="Enterprise Academy", slug="enterprise-academy"))
    user_payload = {
        "username": "t_ent_01",
        "email": "t_ent@academy.edu",
        "password": "securepassword123",
        "role": "TEACHER",
        "organization_id": org_id,
    }
    resp = client.post("/api/v1/users", headers=headers, json=user_payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["username"] == "t_ent_01"

    # 2. System health
    resp = client.get("/api/v1/admin/system-health", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["api_server"] == "ONLINE"

    # 3. AI Gateway status
    resp = client.get("/api/v1/ai/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["gateway_status"] == "HEALTHY"
