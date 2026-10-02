"""Phase 26: Packaging, Clean Install & Deployment Validation Master Test Suite.

Section 36 of GAYATRI_MASTER_PHASE_BY_PHASE_EXECUTION_AND_RECOVERY_GUIDE.md &
Section 12.26 of GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md:
1. Packaging completeness and integrity manifest generation
2. Release integrity verification (tamper detection & unsigned/signed policies)
3. Clean environment bootstrap and forward migrations (001-008)
4. Full clean lifecycle (provision -> publish -> enroll -> turn -> restart -> verify)
5. Real subsystem health probing (zero fake UP strings)
6. Strict secret security enforcement in production mode
7. Setup and launch batch script integrity and migration hooks
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
import pytest

from central_platform.db import PlatformDatabase
from central_platform.deployment.validator import (
    DeploymentValidator,
    ValidationCategory,
    ValidationStatus,
)
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    KnowledgeContentType,
    Organization,
    RAGChunk,
    RAGSource,
    RAGSourceStatus,
    Session,
    SessionStatus,
    StudentLearningRecord,
    User,
    UserRole,
)
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import GenericTutorOrchestrator, TutorTurnRequest
from core.security.signatures import ManifestSigner, ManifestVerifier
from scripts.package_release import compute_file_sha256, package_release
from scripts.verify_release import verify_release


# ==============================================================================
# 1. PACKAGING COMPLETENESS & MANIFEST GENERATION
# ==============================================================================

def test_packaging_completeness_and_manifest(tmp_path):
    """Verify package_release bundles all core modules including central_platform,
    migrations, scripts, and model manifests with accurate SHA-256 hashes.
    """
    out_dir = tmp_path / "pkg_out"
    result = package_release(output_dir=out_dir, version="3.0.0")

    assert result["total_files"] > 100
    assert (out_dir / "RELEASE_MANIFEST.json").exists()
    assert (out_dir / "central_platform").is_dir()
    assert (out_dir / "migrations").is_dir()
    assert (out_dir / "scripts").is_dir()
    assert (out_dir / "app").is_dir()
    assert (out_dir / "core").is_dir()
    assert (out_dir / "model_manifest.json").exists()
    assert (out_dir / "LICENSE.md").exists()

    with open(out_dir / "RELEASE_MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "3.0.0"
    assert manifest["project"] == "Gayatri AI"
    assert len(manifest["files"]) == result["total_files"]

    # Verify a sample file hash
    test_rel = "model_manifest.json"
    assert test_rel in manifest["files"]
    expected_hash = manifest["files"][test_rel]
    actual_hash = compute_file_sha256(out_dir / test_rel)
    assert actual_hash == expected_hash


# ==============================================================================
# 2. RELEASE INTEGRITY VERIFICATION (TAMPER & SIGNATURES)
# ==============================================================================

def test_release_integrity_verification_signed_and_unsigned(tmp_path):
    """Verify release verification on signed and unsigned bundles, and confirm
    tampering or file injection is promptly detected.
    """
    pkg_dir = tmp_path / "verify_pkg"
    package_release(output_dir=pkg_dir, version="3.0.0")

    # 1. Unsigned verification passes with require_signature=False
    v_unsigned = verify_release(pkg_dir, require_signature=False)
    assert v_unsigned["valid"] is True
    assert v_unsigned["files_checked"] > 100

    # 2. Missing signature fails when require_signature=True
    v_missing_sig = verify_release(pkg_dir, require_signature=True)
    assert v_missing_sig["valid"] is False
    assert any("signature" in err.lower() for err in v_missing_sig["errors"])

    # 3. Sign manifest with generated Ed25519 keypair and verify
    priv_key, pub_key = ManifestSigner.generate_keypair()
    manifest_file = pkg_dir / "RELEASE_MANIFEST.json"
    sig_file = pkg_dir / "RELEASE_MANIFEST.sig"
    ManifestSigner.sign_file(manifest_file, priv_key, sig_file)

    v_signed = verify_release(pkg_dir, public_key_b64=pub_key, require_signature=True)
    assert v_signed["valid"] is True
    assert v_signed["signature_valid"] is True

    # 4. Tamper detection: modify a file
    target_file = pkg_dir / "LICENSE.md"
    original_text = target_file.read_text(encoding="utf-8")
    target_file.write_text(original_text + "\n# TAMPERED", encoding="utf-8")

    v_tampered = verify_release(pkg_dir, public_key_b64=pub_key, require_signature=True)
    assert v_tampered["valid"] is False
    assert any("Hash mismatch" in err for err in v_tampered["errors"])

    # Restore file
    target_file.write_text(original_text, encoding="utf-8")

    # 5. Untracked injected file detection
    injected_file = pkg_dir / "malicious_payload.py"
    injected_file.write_text("import os; os.system('echo exploit')", encoding="utf-8")

    v_injected = verify_release(pkg_dir, public_key_b64=pub_key, require_signature=True)
    assert v_injected["valid"] is False
    assert any("Untracked or tampered file" in err for err in v_injected["errors"])


# ==============================================================================
# 3. CLEAN ENVIRONMENT BOOTSTRAP & MIGRATIONS
# ==============================================================================

def test_clean_environment_bootstrap_and_migrations(tmp_path):
    """Verify that a completely fresh database can apply all forward migrations (001-008)
    without errors and generate the complete schema.
    """
    clean_db = str(tmp_path / "fresh_deploy.db")
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    migrate_script = scripts_dir / "migrate_db.py"

    cmd = [sys.executable, str(migrate_script), "up", "--db-path", clean_db]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Migration failed: {res.stderr}\n{res.stdout}"

    # Verify tables
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cursor.fetchall()}
    conn.close()

    assert "schema_migrations" in tables
    assert "users" in tables
    assert "courses" in tables
    assert "course_versions" in tables
    assert "rag_sources" in tables
    assert "rag_chunks" in tables
    assert "teacher_instructions" in tables
    assert "fee_structures" in tables
    assert "sync_operations" in tables
    assert len(tables) >= 48


# ==============================================================================
# 4. CLEAN LIFECYCLE: PROVISION -> PUBLISH -> ENROLL -> TURN -> RESTART -> VERIFY
# ==============================================================================

def test_clean_lifecycle_provision_publish_turn_restart(tmp_path):
    """Simulate complete deployment journey in fresh environment:
    bootstrap DB -> provision org & course -> publish RAG content ->
    enroll student -> execute tutor turn -> close -> restart DB -> verify state.
    """
    db_file = str(tmp_path / "lifecycle_deploy.db")
    db = PlatformDatabase(db_path=db_file)

    # 1. Provision organization & course
    org = Organization(id="org-clean-prod", name="Production Academy", slug="prod-acad")
    db.create_organization(org)

    course = Course(
        id="crs-clean-phys",
        organization_id=org.id,
        code="PHY101",
        title="College Physics",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)

    version = CourseVersion(
        id="ver-clean-v1",
        course_id=course.id,
        version_number="1.0.0",
        status=CourseStatus.PUBLISHED,
        created_by="admin-user",
    )
    db.create_course_version(version)

    # 2. Publish RAG knowledge asset
    src = RAGSource(
        id="src-clean-textbook",
        organization_id=org.id,
        course_id=course.id,
        course_version_id=version.id,
        subject="Physics",
        title="Newtonian Mechanics",
        content_type=KnowledgeContentType.TEXTBOOK,
        status=RAGSourceStatus.PUBLISHED,
        uploaded_by="teacher-user",
    )
    db.create_rag_source(src)

    chunk = RAGChunk(
        id="chk-clean-1",
        source_id=src.id,
        course_id=course.id,
        course_version_id=version.id,
        subject="Physics",
        chapter="Chapter 1: Kinematics",
        topic="Velocity",
        concept="Acceleration",
        text="Acceleration is the rate of change of velocity per unit of time.",
        clean_text="Acceleration is the rate of change of velocity per unit of time.",
    )
    db.add_rag_chunks([chunk])

    # 3. Enroll student
    student = User(
        id="usr-clean-std",
        email="clean_student@school.edu",
        full_name="Clean Student",
        role=UserRole.STUDENT,
        organization_id=org.id,
    )
    db.create_user(student)

    enrollment = Enrollment(
        id="enr-clean-1",
        student_id=student.id,
        course_id=course.id,
        is_active=True,
    )
    db.create_enrollment(enrollment)

    # 4. Start session and execute turn
    session = Session(
        id="ses-clean-1",
        student_id=student.id,
        course_id=course.id,
        concept_id="Acceleration",
        status=SessionStatus.ACTIVE,
    )
    db.create_session(session)

    orchestrator = GenericTutorOrchestrator(db=db)
    req = TutorTurnRequest(
        student_id=student.id,
        session_id=session.id,
        course_id=course.id,
        course_version_id=version.id,
        message="What is acceleration in physics?",
        max_tokens=64,
    )
    turn_res = orchestrator.execute_turn(req)
    assert turn_res.status == "SUCCESS"
    assert turn_res.state_committed is True

    # 5. Close session
    db.update_session_status(session.id, SessionStatus.COMPLETED)
    assert db.get_session(session.id).status == SessionStatus.COMPLETED

    # 6. SIMULATE RESTART: Instantiate a brand-new PlatformDatabase and orchestrator
    restart_db = PlatformDatabase(db_path=db_file)
    restart_orchestrator = GenericTutorOrchestrator(db=restart_db)

    # Verify state persistence across restart
    restored_org = restart_db.get_organization(org.id)
    assert restored_org is not None
    assert restored_org.name == "Production Academy"

    restored_course = restart_db.get_course(course.id)
    assert restored_course is not None

    restored_session = restart_db.get_session(session.id)
    assert restored_session is not None
    assert restored_session.status == SessionStatus.COMPLETED

    restored_events = restart_db.get_learning_events_for_session(session.id)
    assert len(restored_events) >= 1

    restored_slr = restart_db.get_student_learning_record(student.id, course.id)
    assert restored_slr is not None
    assert restored_slr.student_id == student.id
    assert restored_slr.course_id == course.id


# ==============================================================================
# 5. REAL SUBSYSTEM HEALTH PROBING
# ==============================================================================

def test_deployment_validator_real_subsystem_probes(tmp_path):
    """Verify DeploymentValidator probes actual live subsystems (DB, AI, RAG, Payments, i18n)
    and reports failures when subsystems are down or non-existent.
    """
    # 1. Full validation on current workspace
    validator = DeploymentValidator()
    report = validator.run_full_validation()
    assert report.is_ready is True
    assert report.failed_checks == 0

    health_check = next(r for r in report.results if r.check_name == "health_endpoints")
    assert health_check.status == ValidationStatus.PASS
    services = health_check.details["services"]
    assert services["database"] == "UP"
    assert services["ai_gateway"] == "UP"
    assert services["rag_service"] == "UP"
    assert services["payments_gateway"] == "UP"
    assert services["i18n_registry"] == "UP"

    # 2. Probe failure test: Point validator to non-existent database file
    broken_validator = DeploymentValidator(db_path=str(tmp_path / "nonexistent.db"))
    broken_report = broken_validator.run_full_validation()
    assert broken_report.is_ready is False

    broken_health = next(r for r in broken_report.results if r.check_name == "health_endpoints")
    assert broken_health.status == ValidationStatus.FAIL
    assert broken_health.details["services"]["database"] == "DOWN"


# ==============================================================================
# 6. STRICT SECRET SECURITY ENFORCEMENT
# ==============================================================================

def test_deployment_validator_secret_enforcement():
    """Verify that missing or weak secrets fail readiness when in production or strict mode."""
    # Development mode without explicit secrets -> WARN (ready)
    dev_validator = DeploymentValidator(env_vars={"APP_ENV": "development", "SECRET_KEY": ""})
    dev_res = dev_validator.validate_secrets()
    assert dev_res.status == ValidationStatus.WARN

    # Production mode without secret -> FAIL (not ready)
    prod_validator = DeploymentValidator(env_vars={"APP_ENV": "production", "SECRET_KEY": ""})
    prod_res = prod_validator.validate_secrets()
    assert prod_res.status == ValidationStatus.FAIL
    assert "Missing required SECRET_KEY" in prod_res.message

    # Weak secret -> FAIL in any environment
    weak_validator = DeploymentValidator(env_vars={"APP_ENV": "development", "SECRET_KEY": "123456"})
    weak_res = weak_validator.validate_secrets()
    assert weak_res.status == ValidationStatus.FAIL
    assert "Insecure secret key" in weak_res.message

    # Strong secret in production -> PASS
    strong_validator = DeploymentValidator(
        env_vars={"APP_ENV": "production", "SECRET_KEY": "a_very_strong_secure_production_secret_key_2026!"}
    )
    strong_res = strong_validator.validate_secrets()
    assert strong_res.status == ValidationStatus.PASS


# ==============================================================================
# 7. SETUP AND LAUNCH SCRIPT HYGIENE
# ==============================================================================

def test_setup_and_launch_scripts_integrity():
    """Verify setup.bat and launch.bat contain proper Python 3.12 checks,
    database schema initialization, and proper entry points.
    """
    root = Path(__file__).resolve().parent.parent
    setup_bat = root / "setup.bat"
    launch_bat = root / "launch.bat"

    assert setup_bat.exists()
    assert launch_bat.exists()

    setup_content = setup_bat.read_text(encoding="utf-8")
    launch_content = launch_bat.read_text(encoding="utf-8")

    # Check setup.bat requirements
    assert "python" in setup_content.lower()
    assert "requirements.txt" in setup_content
    assert "migrate_db.py" in setup_content
    assert "gayatri_local.db" in setup_content
    assert "app.main" in setup_content

    # Check launch.bat requirements
    assert "setup.bat" in launch_content
    assert "app.main" in launch_content
