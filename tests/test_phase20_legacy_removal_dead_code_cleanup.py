"""Phase 20: Legacy Removal & Dead-Code Cleanup Test Suite.

Master Plan Section 12.20 Requirements:
1. Architecture import guard: zero legacy imports across the entire codebase.
2. Deletion proof: legacy/ directory and stale scratch files eliminated.
3. Dead configuration removal: dead feature flags removed from core.config.
4. Clean imports: core, central_platform, app, and local_runtime import cleanly.
5. Service execution: inference service and context builder function with zero legacy dependencies.
6. Platform startup: FastAPI application boots cleanly and serves health probes.
7. Packaging cleanliness: sys.modules and package distributions have no legacy modules.
8. End-to-end tutor turn: generic tutor orchestrator completes turns without legacy shims.
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    Organization,
    User,
    UserRole,
)
from central_platform.tutor.orchestrator import GenericTutorOrchestrator, TutorTurnRequest, TutorTurnResult
from core import config

ROOT = Path(__file__).resolve().parent.parent


# ── Test 1: legacy/ Directory Removed from Filesystem ─────────────────────────

def test_legacy_directory_removed_from_filesystem():
    """Assert that legacy/ directory has been completely deleted from the project."""
    legacy_path = ROOT / "legacy"
    assert not legacy_path.exists(), f"Found legacy directory still present: {legacy_path}"


# ── Test 2: Zero Legacy Imports Across Entire Codebase ────────────────────────

def test_zero_legacy_imports_in_entire_codebase():
    """Assert that no Python file in core/, central_platform/, app/, local_runtime/, or scripts/ imports from legacy."""
    regex = re.compile(r"^\s*(?:from\s+legacy\b|import\s+legacy\b)", re.MULTILINE)
    violating_files = []

    scan_dirs = ["core", "central_platform", "app", "local_runtime", "scripts"]
    for d in scan_dirs:
        dir_path = ROOT / d
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if regex.search(content):
                violating_files.append(str(py_file.relative_to(ROOT)))

    assert not violating_files, f"Forbidden legacy imports discovered: {violating_files}"


# ── Test 3: Dead Feature Flags Cleaned from core.config ───────────────────────

def test_dead_feature_flags_cleaned_from_config():
    """Assert that enable_legacy_agents is removed from core.config.FEATURE_FLAGS."""
    assert hasattr(config, "FEATURE_FLAGS")
    assert "enable_legacy_agents" not in config.FEATURE_FLAGS


# ── Test 4: Stale Scratch Files Cleaned ───────────────────────────────────────

def test_scratch_stale_files_cleaned():
    """Assert that stale scratch analysis scripts and temp sqlite DBs are removed."""
    scratch_dir = ROOT / "scratch"
    if scratch_dir.exists():
        py_files = list(scratch_dir.glob("*.py"))
        db_files = list(scratch_dir.glob("*.db"))
        assert len(py_files) == 0, f"Found stale scratch Python files: {py_files}"
        assert len(db_files) == 0, f"Found stale scratch DB files: {db_files}"


# ── Test 5: Clean Import of Core Modules ──────────────────────────────────────

def test_clean_import_core_modules():
    """Verify primary core modules import cleanly without legacy errors."""
    core_modules = [
        "core.config",
        "core.session",
        "core.mode",
        "core.orchestrator",
        "core.inference.service",
        "core.inference.context",
        "core.providers.local",
        "core.security.prompt",
    ]
    for mod_name in core_modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None


# ── Test 6: Clean Import of Central Platform Modules ─────────────────────────

def test_clean_import_central_platform_modules():
    """Verify primary central platform modules import cleanly without legacy errors."""
    platform_modules = [
        "central_platform.db",
        "central_platform.courses.service",
        "central_platform.curriculum.service",
        "central_platform.rag.service",
        "central_platform.ai.gateway",
        "central_platform.ai.context_builder",
        "central_platform.tools.registry",
        "central_platform.assessment.evaluators.registry",
        "central_platform.tutor.orchestrator",
        "central_platform.adapters.chemistry.adapter",
    ]
    for mod_name in platform_modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None


# ── Test 7: Clean Import of App and Local Runtime Modules ────────────────────

def test_clean_import_app_and_runtime_modules():
    """Verify app controllers and local runtime modules import cleanly."""
    runtime_modules = [
        "local_runtime.engine",
        "local_runtime.course_cache",
        "local_runtime.rag_cache",
        "local_runtime.session",
        "local_runtime.sync_outbox",
        "app.portals.student.controller",
        "app.portals.teacher.controller",
        "app.portals.admin.controller",
    ]
    for mod_name in runtime_modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None


# ── Test 8: Inference Service Functions Without Legacy ────────────────────────

def test_inference_service_functions_without_legacy():
    """Verify core inference service instantiates and provides active providers without legacy agents."""
    from core.inference.service import get_inference_service
    service = get_inference_service()
    assert service is not None
    # Ensure legacy is not in sys.modules
    assert not any(k.startswith("legacy") for k in sys.modules)


# ── Test 9: Context Builder Functions Without Legacy ──────────────────────────

def test_context_builder_functions_without_legacy():
    """Verify context message assembly operates without legacy agent dependencies."""
    from core.inference.context import _build_messages
    history = [
        {"role": "user", "content": "What is friction?"},
        {"role": "assistant", "content": "Friction is a resistive force."},
    ]
    messages = _build_messages(
        user_message="Give an example",
        history=history,
        system_prompt="You are a helpful science tutor.",
    )
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "Give an example"


# ── Test 10: Platform Startup and Health Check Probes ─────────────────────────

def test_platform_startup_and_health_probes():
    """Verify FastAPI platform starts up and passes live, ready, and healthz probes."""
    client = TestClient(app)

    res_healthz = client.get("/healthz")
    assert res_healthz.status_code == 200
    assert res_healthz.json().get("status") in ("ok", "healthy", "ONLINE")

    res_livez = client.get("/livez")
    assert res_livez.status_code == 200

    res_readyz = client.get("/readyz")
    assert res_readyz.status_code == 200


# ── Test 11: Packaging Discovery Clean of Legacy ─────────────────────────────

def test_packaging_clean_of_legacy():
    """Verify sys.modules and top-level packages contains zero legacy modules."""
    for mod in list(sys.modules.keys()):
        assert not mod.startswith("legacy."), f"Found loaded legacy module: {mod}"
    assert "legacy" not in sys.modules


from central_platform.api.app import app


# ── Test 12: End-to-End Tutor Turn Operates Without Legacy Paths ──────────────

def test_end_to_end_tutor_turn_cleanly():
    """Verify GenericTutorOrchestrator turn execution succeeds without any legacy path invocation."""
    db = PlatformDatabase(":memory:")
    db.create_organization(Organization(id="org-clean", name="Clean Academy", slug="clean-acad"))
    db.create_user(User(id="admin-clean", organization_id="org-clean", email="admin@clean.edu", full_name="Admin Clean", role=UserRole.SUPER_ADMIN))
    db.create_user(User(id="stu-clean-01", organization_id="org-clean", email="stu@clean.edu", full_name="Student Clean", role=UserRole.STUDENT))
    db.create_course(Course(id="crs-clean-phys", organization_id="org-clean", code="PHYS101", title="Physics", visibility=CourseVisibility.PUBLIC))
    db.create_course_version(CourseVersion(id="ver-phys-1.0", course_id="crs-clean-phys", version_number="1.0", status=CourseStatus.PUBLISHED, created_by="admin-clean"))
    db.create_enrollment(Enrollment(id="enr-clean-01", student_id="stu-clean-01", course_id="crs-clean-phys", is_active=True))

    orchestrator = GenericTutorOrchestrator(db=db)
    req = TutorTurnRequest(
        student_id="stu-clean-01",
        session_id="ses-clean-20-01",
        course_id="crs-clean-phys",
        message="Explain Newton's third law of motion.",
    )

    result = orchestrator.execute_turn(req)
    assert result is not None
    assert result.status == "SUCCESS"
    assert result.validation_passed is True
    assert result.state_committed is True
    assert len(result.response_text) > 0
    assert result.student_id == "stu-clean-01"
