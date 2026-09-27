"""Phase 04 Test Suite — Production Authentication, Token Lifecycle, and RBAC Security Verification.

Master Plan Section 13:
1. PBKDF2-HMAC-SHA256 password hashing with unique random salts and constant-time digest verification.
2. Cryptographic JWT session and token lifecycle (access tokens, refresh tokens, expiration, revocation blacklist).
3. Database credentials storage, suspension states, and password reset workflows.
4. /api/v1/auth/* endpoints (login, /me, refresh, logout, password-reset).
5. All 8 Section 13 Mandatory Negative Security Tests:
   - student -> another student (403 Forbidden)
   - student -> teacher (403 Forbidden)
   - teacher -> unrelated student (403 Forbidden)
   - teacher -> admin (403 Forbidden)
   - org admin -> another organization (403 Forbidden)
   - modified student_id in body (403 Forbidden)
   - modified session_id belonging to another user (403 Forbidden)
   - modified organization_id mismatching tenant scope (403 Forbidden)
"""

import time
import uuid
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.dependencies import enforce_resource_boundaries
from central_platform.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_and_verify_token,
    is_token_revoked,
    revoke_token,
)
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    ClassGroup,
    Course,
    Enrollment,
    Organization,
    User,
    UserRole,
)
from central_platform.rbac.engine import (
    Permission,
    check_resource_access,
    has_permission,
    hash_password,
    normalize_role,
    verify_password,
)


@pytest.fixture(scope="module")
def client():
    """Create test client for FastAPI platform application."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_db(tmp_path):
    """Provide a fresh isolated database for auth testing."""
    db_file = str(tmp_path / "auth_test.db")
    db = PlatformDatabase(db_file)
    yield db
    db.close()


# ── 1. Cryptographic Password Hashing & Verification ─────────────────────

def test_password_hashing_pbkdf2_entropy():
    """Verify PBKDF2 hashing uses 16-byte random salts and constant-time verification."""
    password = "SuperSecretPassword#2026"
    hash1, salt1 = hash_password(password)
    hash2, salt2 = hash_password(password)

    # Hashes and salts must be unique due to random salt generation
    assert salt1 != salt2
    assert hash1 != hash2
    assert len(salt1) == 32  # 16 bytes in hex = 32 chars
    assert len(hash1) == 64  # SHA-256 = 64 hex chars

    # Verification must succeed with correct password
    assert verify_password(password, hash1, salt1) is True
    assert verify_password(password, hash2, salt2) is True

    # Verification must fail with wrong password
    assert verify_password("WrongPassword#9999", hash1, salt1) is False
    assert verify_password("", hash1, salt1) is False


def test_password_verification_tamper_resilience():
    """Verify corrupted hashes or invalid salts fail safely without unhandled exceptions."""
    password = "CorrectPassword123"
    p_hash, salt = hash_password(password)

    # Tampered hash
    tampered_hash = "a" * 64
    assert verify_password(password, tampered_hash, salt) is False

    # Corrupted salt hex
    assert verify_password(password, p_hash, "invalid_non_hex_salt") is False


# ── 2. Cryptographic JWT Lifecycle, Expiration, & Revocation ──────────────

def test_jwt_token_minting_and_decoding():
    """Verify JWT access and refresh token generation and claim extraction."""
    user_id = "usr-test-student-01"
    role = "student"
    org_id = "org-central-01"

    access_token = create_access_token(
        user_id=user_id,
        role=role,
        organization_id=org_id,
        expires_minutes=30,
        custom_claims={"name": "Arya"},
    )
    assert isinstance(access_token, str)
    assert access_token.count(".") == 2  # Standard 3-segment JWT

    payload = decode_and_verify_token(access_token, expected_type="access")
    assert payload["user_id"] == user_id
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["organization_id"] == org_id
    assert payload["type"] == "access"
    assert payload["name"] == "Arya"
    assert payload["exp"] > payload["iat"]


def test_jwt_refresh_token_lifecycle():
    """Verify refresh tokens cannot be used as access tokens and vice-versa."""
    user_id = "usr-refresh-user"
    refresh_tok = create_refresh_token(user_id=user_id, organization_id="org-test")

    # Decoding with expected_type="refresh" must succeed
    payload = decode_and_verify_token(refresh_tok, expected_type="refresh")
    assert payload["type"] == "refresh"
    assert payload["user_id"] == user_id

    # Decoding refresh token as access token must be rejected
    with pytest.raises(PermissionError, match="Expected token type 'access'"):
        decode_and_verify_token(refresh_tok, expected_type="access")


def test_jwt_token_expiration():
    """Verify expired JWT tokens raise PermissionError."""
    # Mint token that expired 10 minutes ago
    now_ts = int(time.time()) - 600
    expired_token = create_access_token(
        user_id="usr-expired",
        role="student",
        expires_minutes=-10,
    )
    with pytest.raises(PermissionError, match="Token has expired"):
        decode_and_verify_token(expired_token, expected_type="access")


def test_jwt_token_revocation_blacklist():
    """Verify revoked tokens cannot be verified."""
    token = create_access_token(user_id="usr-to-revoke", role="teacher")
    assert is_token_revoked(token) is False

    # Valid before revocation
    payload = decode_and_verify_token(token)
    assert payload["user_id"] == "usr-to-revoke"

    # Revoke
    ok = revoke_token(token)
    assert ok is True
    assert is_token_revoked(token) is True

    # Verification must now raise PermissionError
    with pytest.raises(PermissionError, match="Token has been revoked"):
        decode_and_verify_token(token)


# ── 3. Database Credentials Storage & Account State ───────────────────────

def test_db_user_credentials_lifecycle(auth_db):
    """Test user credential storage, authentication, suspension, and reset."""
    org = Organization(id="org-auth-1", name="Auth Academy", slug="auth-academy")
    auth_db.create_organization(org)

    user = User(
        id="usr-cred-01",
        email="cred_user@gayatri.edu",
        full_name="Cred Test User",
        role=UserRole.TEACHER,
        organization_id=org.id,
    )
    auth_db.create_user(user)

    # Set password
    auth_db.set_user_password(user.id, "CorrectPassword#123")

    # Verify authentication success
    authenticated = auth_db.authenticate_user(user.email, "CorrectPassword#123")
    assert authenticated is not None
    assert authenticated.id == user.id

    # Verify authentication failure with wrong password
    bad_auth = auth_db.authenticate_user(user.email, "BadPassword")
    assert bad_auth is None

    creds = auth_db.get_user_credentials(user.id)
    assert creds["failed_login_attempts"] >= 1

    # Suspend user
    auth_db.suspend_user(user.id)
    creds_suspended = auth_db.get_user_credentials(user.id)
    assert creds_suspended["is_suspended"] == 1

    # Suspended user cannot authenticate even with correct password
    assert auth_db.authenticate_user(user.email, "CorrectPassword#123") is None

    # Unsuspend user
    auth_db.unsuspend_user(user.id)
    assert auth_db.authenticate_user(user.email, "CorrectPassword#123") is not None

    # Password reset with token
    token = "reset-tok-xyz-987"
    assert auth_db.set_password_reset_token(user.email, token) is True
    assert auth_db.reset_password_with_token(token, "BrandNewPassword#456") is True

    # Old password fails, new password succeeds
    assert auth_db.authenticate_user(user.email, "CorrectPassword#123") is None
    assert auth_db.authenticate_user(user.email, "BrandNewPassword#456") is not None


# ── 4. API Endpoints: Login, /me, Refresh, Logout, Password-Reset ─────────

def test_api_auth_login_me_logout_flow(client):
    """Test full login, profile lookup, and logout cycle through API."""
    # 1. Login
    login_resp = client.post("/api/v1/auth/login", json={"username": "teacher_1", "password": "password"})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["ok"] is True
    access_token = body["data"]["access_token"]
    refresh_token = body["data"]["refresh_token"]
    assert access_token.count(".") == 2
    assert refresh_token.count(".") == 2

    # 2. GET /me with Bearer token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()["data"]
    assert me_data["role"] == "TEACHER"
    assert me_data["user_id"] == "usr-teacher-01"

    # 3. Refresh token exchange
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["data"]["access_token"]
    assert new_access_token != access_token

    # 4. Logout invalidates access token
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout_resp.status_code == 200
    assert logout_resp.json()["data"]["logged_out"] is True

    # 5. Accessing /me with revoked token returns 401
    me_revoked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_revoked.status_code == 401


def test_api_auth_unauthorized_missing_token(client):
    """Test GET /me without token returns 401 Unauthorized."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── 5. Master Plan Section 13: Mandatory 8 Negative Security Tests ─────────

def test_security_01_student_to_another_student(client):
    """Negative Test 1: Student attempting to access another student's profile or SLR must return 403 Forbidden."""
    # Student A token
    student_a_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )

    # Alice accesses her own profile: allowed
    r_own = client.get(
        "/api/v1/students/student_alice",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert r_own.status_code == 200

    # Alice attempts to access Bob's profile: MUST FAIL 403
    r_other = client.get(
        "/api/v1/students/student_bob",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert r_other.status_code == 403
    assert "Forbidden" in r_other.json()["detail"]

    # Alice attempts to access Bob's SLR: MUST FAIL 403
    r_slr = client.get(
        "/api/v1/students/student_bob/slr",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert r_slr.status_code == 403


def test_security_02_student_to_teacher(client):
    """Negative Test 2: Student attempting teacher dashboard or instruction creation must return 403 Forbidden."""
    student_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )

    # 1. Attempt teacher dashboard
    r_dash = client.get(
        "/api/v1/teachers/dashboard",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_dash.status_code == 403
    assert "Forbidden" in r_dash.json()["detail"]

    # 2. Attempt to create teacher instruction
    r_inst = client.post(
        "/api/v1/teachers/instructions",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "instruction": "Unauthorized directive from student",
            "student_id": "student_bob",
            "course_id": "crs-chem-101",
            "priority": 1,
        },
    )
    assert r_inst.status_code == 403

    # 3. Attempt to resolve teacher alert
    r_alert = client.post(
        "/api/v1/teachers/alerts/resolve",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"alert_id": "alrt-001", "resolution_note": "Hacked"},
    )
    assert r_alert.status_code == 403


def test_security_03_teacher_to_unrelated_student(client):
    """Negative Test 3: Teacher attempting to direct or manage unrelated student outside assigned domain must fail 403."""
    teacher_token = create_access_token(
        user_id="teacher_sharma",
        role="teacher",
        organization_id="org-central",
    )

    # Teacher checks RBAC resource access directly
    # Teacher is assigned to std_01, but attempts to access std_external
    permitted = check_resource_access(
        actor_role=UserRole.TEACHER,
        actor_org_id="org-central",
        actor_user_id="teacher_sharma",
        target_org_id="org-central",
        target_student_id="std_external_unassigned",
        assigned_student_ids={"std_01", "std_02"},
    )
    assert permitted is False

    # Attempting cross-organization student access
    cross_org_permitted = check_resource_access(
        actor_role=UserRole.TEACHER,
        actor_org_id="org-central",
        actor_user_id="teacher_sharma",
        target_org_id="org-different-district",
        target_student_id="std_01",
    )
    assert cross_org_permitted is False


def test_security_04_teacher_to_admin(client):
    """Negative Test 4: Teacher attempting administrative endpoints or kill switch must return 403 Forbidden."""
    teacher_token = create_access_token(
        user_id="teacher_sharma",
        role="teacher",
        organization_id="org-central",
    )

    # 1. Attempt admin organizations endpoint
    r_orgs = client.get(
        "/api/v1/admin/organizations",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r_orgs.status_code == 403

    # 2. Attempt admin system health
    r_health = client.get(
        "/api/v1/admin/system-health",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r_health.status_code == 403

    # 3. Attempt emergency kill switch
    r_kill = client.post(
        "/api/v1/admin/kill-switch?active=true&reason=teacher_attempt",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r_kill.status_code == 403


def test_security_05_org_admin_to_another_organization(client):
    """Negative Test 5: Org Admin querying or creating resources in another organization must return 403 Forbidden."""
    org_admin_token = create_access_token(
        user_id="org_admin_alpha",
        role="org_admin",
        organization_id="org-alpha",
    )

    # Attempt to query another organization's data
    r_cross_org = client.get(
        "/api/v1/admin/organizations?organization_id=org-beta",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r_cross_org.status_code == 403
    assert "Forbidden" in r_cross_org.json()["detail"]

    # Attempt to create user in another organization
    r_create_cross = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={
            "username": "intruder_user",
            "email": "intruder@beta.edu",
            "password": "pass",
            "role": "TEACHER",
            "organization_id": "org-beta",  # Mismatched organization
        },
    )
    assert r_create_cross.status_code == 403


def test_security_06_modified_student_id(client):
    """Negative Test 6: Request body containing tampered student_id mismatching JWT caller must return 403 Forbidden."""
    student_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )

    # Alice starts a session but claims student_id is "student_bob"
    tampered_start = client.post(
        "/api/v1/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "student_id": "student_bob",  # Spoofed identity
            "course_id": "crs-chem-101",
            "initial_concept": "chem_thermo_first_law",
        },
    )
    assert tampered_start.status_code == 403
    assert "student_id in request body does not match" in tampered_start.json()["detail"]

    # Alice pushes snapshot telemetry claiming student_id is "student_bob"
    tampered_snap = client.post(
        "/api/v1/students/snapshot",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "student_id": "student_bob",  # Spoofed identity
            "student_name": "Bob",
            "mastery": 0.99,
        },
    )
    assert tampered_snap.status_code == 403


def test_security_07_modified_session_id(client):
    """Negative Test 7: Student attempting to access a session belonging to another user must return 403 Forbidden."""
    # 1. Student Bob starts a session
    bob_token = create_access_token(
        user_id="student_bob",
        role="student",
        organization_id="org-central",
    )
    r_sess = client.post(
        "/api/v1/sessions/start",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"student_id": "student_bob", "course_id": "crs-chem-101"},
    )
    assert r_sess.status_code == 201
    bob_session_id = r_sess.json()["data"]["session_id"]

    # 2. Student Alice attempts to query Bob's session
    alice_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )
    r_tampered = client.get(
        f"/api/v1/sessions/{bob_session_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r_tampered.status_code == 403
    assert "Forbidden" in r_tampered.json()["detail"]


def test_security_08_modified_organization_id(client):
    """Negative Test 8: Modified organization_id in request body or query parameter mismatching tenant must return 403 Forbidden."""
    org_admin_token = create_access_token(
        user_id="admin_campus_a",
        role="org_admin",
        organization_id="org-campus-a",
    )

    # Org Admin attempts to provision user claiming organization_id is "org-campus-b"
    r_tampered_org = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={
            "username": "spoofed_teacher",
            "email": "spoof@campus.edu",
            "password": "password123",
            "role": "TEACHER",
            "organization_id": "org-campus-b",  # Mismatched organization_id
        },
    )
    assert r_tampered_org.status_code == 403
    assert "outside your tenant" in r_tampered_org.json()["detail"]
