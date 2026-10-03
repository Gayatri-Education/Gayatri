"""Phase 01 Forensic Remediation Test Suite — Authentication and Identity Binding.

Audit Basis:
- Finding F-001 (P0): Protected APIs can operate without authentication.
- Finding F-002 (P0): Caller-supplied student_id is not bound to authenticated identity.
- Finding F-004 (P1): Production fallback to hardcoded default user and insecure default secrets.

Invariants Verified:
- I1: Protected route means authenticated (401 for unauthenticated/malformed/expired tokens).
- I2: Student identity is server-derived; body student_id must match authenticated principal (403 for spoofing).
- I3: Never authenticate by request body.
- I4: Fail closed in production when authenticated user does not exist in DB directory.
- I5: JWT secret must be explicitly provided in production mode (raises RuntimeError on insecure defaults).
- I6: Token revocation is strictly checked and rejected.
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.dependencies import get_db
from central_platform.auth.tokens import (
    create_access_token,
    decode_and_verify_token,
    get_jwt_secret_key,
    revoke_token,
)
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVisibility,
    Enrollment,
    Organization,
    User,
    UserRole,
)


@pytest.fixture
def auth_test_env(tmp_path):
    """Isolated test environment with test database and seeded entities."""
    db_path = str(tmp_path / "auth_test.db")
    db = PlatformDatabase(db_path)

    # Seed Organization
    org = Organization(id="org-auth-test", name="Auth Test Org", slug="auth-test")
    db.create_organization(org)

    # Seed Students
    student_a = User(
        id="student-alpha-01",
        email="alpha@test.internal",
        full_name="Student Alpha",
        role=UserRole.STUDENT,
        organization_id="org-auth-test",
    )
    student_b = User(
        id="student-beta-02",
        email="beta@test.internal",
        full_name="Student Beta",
        role=UserRole.STUDENT,
        organization_id="org-auth-test",
    )
    db.create_user(student_a)
    db.create_user(student_b)

    # Seed Course & Enrollments
    course = Course(
        id="crs-auth-101",
        organization_id="org-auth-test",
        code="AUTH101",
        title="Authentication Systems",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)
    db.create_enrollment(Enrollment(id="enr-alpha-1", student_id="student-alpha-01", course_id="crs-auth-101", is_active=True))
    db.create_enrollment(Enrollment(id="enr-beta-1", student_id="student-beta-02", course_id="crs-auth-101", is_active=True))

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    token_a = create_access_token(user_id="student-alpha-01", role="STUDENT", organization_id="org-auth-test")
    token_b = create_access_token(user_id="student-beta-02", role="STUDENT", organization_id="org-auth-test")

    yield {
        "db": db,
        "client": client,
        "student_a": student_a,
        "student_b": student_b,
        "token_a": token_a,
        "token_b": token_b,
        "course": course,
    }

    app.dependency_overrides.pop(get_db, None)


def test_F001_unauthenticated_tutor_request_returns_401(auth_test_env):
    """F-001 Invariant: Request without Authorization header must be rejected with 401."""
    client = auth_test_env["client"]
    payload = {
        "student_id": "student-alpha-01",
        "session_id": "sess-auth-01",
        "course_id": "crs-auth-101",
        "message": "Explain symmetric vs asymmetric encryption.",
    }
    resp = client.post("/api/v1/tutor/turn", json=payload)
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    assert "detail" in resp.json()


def test_F001_malformed_bearer_token_returns_401(auth_test_env):
    """F-001 Invariant: Malformed or unparseable Bearer token must return 401."""
    client = auth_test_env["client"]
    payload = {
        "student_id": "student-alpha-01",
        "session_id": "sess-auth-01",
        "course_id": "crs-auth-101",
        "message": "Explain symmetric vs asymmetric encryption.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": "Bearer not-a-valid-jwt-token-garbage"},
        json=payload,
    )
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"


def test_F001_expired_token_returns_401(auth_test_env):
    """F-001 Invariant: Expired JWT token must return 401."""
    client = auth_test_env["client"]
    expired_token = create_access_token(
        user_id="student-alpha-01",
        role="STUDENT",
        organization_id="org-auth-test",
        expires_minutes=-10,  # Expired in past
    )
    payload = {
        "student_id": "student-alpha-01",
        "session_id": "sess-auth-01",
        "course_id": "crs-auth-101",
        "message": "Explain symmetric vs asymmetric encryption.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": f"Bearer {expired_token}"},
        json=payload,
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_F002_student_cannot_spoof_other_student_id_returns_403(auth_test_env):
    """F-002 Invariant: Student A cannot submit a turn claiming student B's ID."""
    client = auth_test_env["client"]
    token_a = auth_test_env["token_a"]

    # Student A authenticated, but body claims student B
    payload = {
        "student_id": "student-beta-02",  # Spoofed identity
        "session_id": "sess-auth-02",
        "course_id": "crs-auth-101",
        "message": "Attempting cross-student identity spoofing turn.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": f"Bearer {token_a}"},
        json=payload,
    )
    assert resp.status_code == 403, f"Expected 403 Forbidden on student identity spoofing, got {resp.status_code}"
    assert "forbidden" in resp.json()["detail"].lower()


def test_F002_valid_student_accesses_own_turn_succeeds(auth_test_env):
    """F-002 Invariant: Student authenticated with matching student_id succeeds."""
    client = auth_test_env["client"]
    token_a = auth_test_env["token_a"]

    payload = {
        "student_id": "student-alpha-01",
        "session_id": "sess-auth-01",
        "course_id": "crs-auth-101",
        "message": "Explain symmetric vs asymmetric encryption.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": f"Bearer {token_a}"},
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "student-alpha-01"
    assert data["status"] == "SUCCESS"
    assert data["ok"] is True


def test_F004_nonexistent_user_fails_closed_in_production(auth_test_env, monkeypatch):
    """F-004 Invariant: In production mode, token minted for missing DB user must fail closed (401)."""
    client = auth_test_env["client"]
    monkeypatch.setenv("GAYATRI_ENV", "production")
    monkeypatch.setenv("GAYATRI_JWT_SECRET", "super-secret-production-entropy-key-999")

    # Mint token for user that does NOT exist in database
    ghost_token = create_access_token(
        user_id="ghost-user-999",
        role="STUDENT",
        organization_id="org-auth-test",
    )
    payload = {
        "student_id": "ghost-user-999",
        "session_id": "sess-ghost-01",
        "course_id": "crs-auth-101",
        "message": "Ghost user turn.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": f"Bearer {ghost_token}"},
        json=payload,
    )
    assert resp.status_code == 401
    assert "not found" in resp.json()["detail"].lower()


def test_F004_production_startup_without_jwt_secret_fails_safely(monkeypatch):
    """Invariant I5: Startup/token creation in production mode must fail if secret is default or unset."""
    monkeypatch.setenv("GAYATRI_ENV", "production")
    monkeypatch.delenv("GAYATRI_JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        get_jwt_secret_key()
    assert "GAYATRI_JWT_SECRET" in str(exc_info.value)
    assert "production" in str(exc_info.value).lower()


def test_F004_revoked_token_returns_401(auth_test_env):
    """Invariant I6: Revoked token must immediately return 401."""
    client = auth_test_env["client"]
    token_a = auth_test_env["token_a"]

    # Revoke token A
    revoke_token(token_a)

    payload = {
        "student_id": "student-alpha-01",
        "session_id": "sess-auth-01",
        "course_id": "crs-auth-101",
        "message": "Explain symmetric vs asymmetric encryption.",
    }
    resp = client.post(
        "/api/v1/tutor/turn",
        headers={"Authorization": f"Bearer {token_a}"},
        json=payload,
    )
    assert resp.status_code == 401
    assert "revoked" in resp.json()["detail"].lower()
