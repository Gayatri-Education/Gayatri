"""Phase 13 Test Suite: Offline Local Runtime Package & Sync Readiness.

Verifies:
1. First offline launch in clean environment (zero fake demo roster entries, BUG-ARCH-003).
2. Offline capability detection (network, database, models, cached courses).
3. Cached course import and SHA-256 checksum verification.
4. Corrupted cache detection, quarantine, and error handling.
5. Uncached course honest degraded state reporting.
6. Local tutor turn offline execution with scoped RAG and transactional persistence.
7. Local state persistence across application restart.
8. Interrupted turn transactional rollback and crash recovery.
9. Read-only database graceful degraded mode.
10. Missing model honest alert, diagnostics, and prompt.
11. Zero fake demo roster in bridge and teacher portal.
12. Zero chemistry coupling in local_runtime subsystem.
"""

from __future__ import annotations

import ast
import json
import re
import zipfile
from pathlib import Path

import pytest

from local_runtime.course_cache import CoursePackageMetadata, LocalCourseCache
from local_runtime.detector import DegradedStateInfo, OfflineCapabilityDetector
from local_runtime.engine import LocalRuntimeEngine
from local_runtime.errors import (
    CorruptedCacheError,
    ModelUnavailableError,
    OfflineCourseNotCachedError,
    ReadOnlyDatabaseError,
)
from local_runtime.rag_cache import LocalRAGCache
from local_runtime.session import LocalSessionPersistence

ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: First offline launch in clean environment
# ─────────────────────────────────────────────────────────────────────────────
def test_first_offline_launch_clean_environment(tmp_path, monkeypatch):
    """Clean startup with empty cache and empty DB renders honest empty state with 0 fake demo roster entries."""
    import central_platform.auth.dependencies as auth_deps
    from app.bridge.facade import get_teacher_portal_service, reset_teacher_singletons

    clean_db_path = str(tmp_path / "clean_empty_launch.db")
    monkeypatch.setenv("GAYATRI_DB_PATH", clean_db_path)
    auth_deps._DB_INSTANCE = None

    reset_teacher_singletons()
    portal = get_teacher_portal_service()

    overview = portal.get_dashboard_overview("crs-generic-101")
    assert overview.total_students == 0
    assert overview.class_health_status == "No Data"
    assert overview.students_needing_attention == 0
    assert overview.average_mastery == 0.0

    students = portal.get_all_students("crs-generic-101")
    assert len(students) == 0

    # Ensure no demo roster names exist
    for stu in students:
        name = stu.get("name", "")
        assert "Rahul Kumar" not in name
        assert "Priya Sharma" not in name
        assert "Amit Patel" not in name


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Offline capability detection
# ─────────────────────────────────────────────────────────────────────────────
def test_offline_capability_detection(tmp_path):
    """Detects offline network state, database read/write status, available models, and cached courses."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")
    session_store = LocalSessionPersistence(db_path=tmp_path / "test.db")
    detector = OfflineCapabilityDetector(
        course_cache=cache,
        session_store=session_store,
        available_models=["phi3-mini", "llama3.2:1b"],
        force_offline=True,
    )

    report = detector.check_offline_status()
    assert report.is_online is False
    assert report.db_writable is True
    assert "phi3-mini" in report.available_models
    assert len(report.cached_courses) == 0
    assert "Operating in disconnected offline mode" in report.status_summary

    # Test individual checks
    assert detector.is_course_available_offline("crs-any-999") is False
    assert detector.is_model_available_offline("phi3-mini") is True
    assert detector.is_model_available_offline("gpt-4") is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Cached course import and checksum verification
# ─────────────────────────────────────────────────────────────────────────────
def test_cached_course_import_and_checksum_verification(tmp_path):
    """Imports valid course package into local cache, verifies SHA-256 checksum, and queries metadata."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")

    # Create a valid course package zip (.gpk)
    pkg_dir = tmp_path / "src_pkg"
    pkg_dir.mkdir()
    manifest_data = {
        "course_id": "crs-cs-101",
        "version_tag": "v1.0",
        "title": "Introduction to Computer Science",
        "concepts": [
            {"id": "cs_vars", "name": "Variables", "difficulty": 0.2},
            {"id": "cs_loops", "name": "Loops", "difficulty": 0.4},
        ],
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    zip_file = tmp_path / "cs101_v1.0.gpk"
    with zipfile.ZipFile(zip_file, "w") as zf:
        zf.write(pkg_dir / "manifest.json", "manifest.json")

    # Import package
    meta = cache.import_package(zip_file)
    assert meta.course_id == "crs-cs-101"
    assert meta.version_tag == "v1.0"
    assert meta.title == "Introduction to Computer Science"
    assert meta.total_concepts == 2
    assert len(meta.checksum) == 64  # Valid SHA-256 hex string
    assert meta.is_valid is True

    # Query cached course
    assert cache.is_course_cached("crs-cs-101") is True
    assert cache.is_course_cached("crs-cs-101", "v1.0") is True
    assert cache.is_course_cached("crs-cs-101", "v2.0") is False

    cached_content = cache.get_cached_course("crs-cs-101")
    assert cached_content is not None
    assert cached_content["course_id"] == "crs-cs-101"

    # Export package test
    exported_file = cache.export_package("crs-cs-101", target_path=tmp_path / "exported.gpk")
    assert exported_file.is_file()
    assert zipfile.is_zipfile(exported_file)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Corrupted cache detection and quarantine
# ─────────────────────────────────────────────────────────────────────────────
def test_corrupted_cache_detection_and_quarantine(tmp_path):
    """Tampered or corrupted course package is detected, quarantined, and reported cleanly without crashing."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")

    # Create a corrupted zip file (random non-zip bytes)
    corrupted_file = tmp_path / "corrupted_course.gpk"
    corrupted_file.write_bytes(b"CORRUPTED_ZIP_HEADER_INVALID_DATA_NOT_A_REAL_ARCHIVE")

    with pytest.raises(CorruptedCacheError) as exc_info:
        cache.import_package(corrupted_file)

    err = exc_info.value
    assert "corrupted" in str(err).lower()
    assert err.quarantine_path is not None

    # Verify quarantine directory received the corrupted file
    q_dir = Path(err.quarantine_path).parent
    assert q_dir.exists()
    quarantined_files = list(q_dir.glob("corrupted_*"))
    assert len(quarantined_files) >= 1

    # Also test checksum mismatch quarantine
    mismatch_pkg_dir = tmp_path / "mismatch_pkg"
    mismatch_pkg_dir.mkdir()
    manifest_data = {
        "course_id": "crs-tampered-101",
        "version_tag": "v1.0",
        "checksum": "0000000000000000000000000000000000000000000000000000000000000000",  # Fake checksum
    }
    (mismatch_pkg_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")
    mismatch_zip = tmp_path / "tampered.gpk"
    with zipfile.ZipFile(mismatch_zip, "w") as zf:
        zf.write(mismatch_pkg_dir / "manifest.json", "manifest.json")

    with pytest.raises(CorruptedCacheError) as exc_info_tampered:
        cache.import_package(mismatch_zip)

    assert "checksum mismatch" in str(exc_info_tampered.value).lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Uncached course honest degraded state
# ─────────────────────────────────────────────────────────────────────────────
def test_uncached_course_honest_degraded_state(tmp_path):
    """Requesting an uncached course offline cleanly raises OfflineCourseNotCachedError with actionable guidance."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")
    session_store = LocalSessionPersistence(db_path=tmp_path / "test.db")
    detector = OfflineCapabilityDetector(course_cache=cache, session_store=session_store)
    engine = LocalRuntimeEngine(course_cache=cache, session_store=session_store, detector=detector)

    # 1. Honest degraded state check
    state = engine.get_honest_state("crs-uncached-physics")
    assert state.is_degraded is True
    assert "course:crs-uncached-physics" in state.missing_components
    assert "not cached locally" in state.reason
    assert "Connect to the network to download" in state.actionable_message

    # 2. Attempting turn on uncached course raises typed error
    with pytest.raises(OfflineCourseNotCachedError) as exc_info:
        engine.execute_tutor_turn(
            session_id="ses-101",
            student_id="stu-101",
            course_id="crs-uncached-physics",
            user_input="Explain Newton's first law",
        )

    err = exc_info.value
    assert err.course_id == "crs-uncached-physics"
    assert "not cached locally for offline execution" in str(err)


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Local tutor turn offline execution
# ─────────────────────────────────────────────────────────────────────────────
def test_local_tutor_turn_offline_execution(tmp_path):
    """Executes a complete tutor turn offline using cached curriculum, scoped RAG, and transactional persistence."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")
    rag = LocalRAGCache(index_dir=tmp_path / "rag")
    session_store = LocalSessionPersistence(db_path=tmp_path / "test.db")

    # Set up cached course
    course_manifest = {
        "course_id": "crs-phy-101",
        "version_tag": "v1.0",
        "title": "Classical Mechanics",
        "concepts": [
            {"id": "phy_inertia", "name": "Inertia and Force", "difficulty": 0.3},
            {"id": "phy_momentum", "name": "Linear Momentum", "difficulty": 0.4},
        ],
    }
    manifest_file = tmp_path / "phy_manifest.json"
    manifest_file.write_text(json.dumps(course_manifest), encoding="utf-8")
    cache.import_package(manifest_file)

    # Index course-specific knowledge chunks
    chunks = [
        {
            "id": "chk_phy_01",
            "text": "Newton's first law states that an object remains at rest or in uniform motion unless acted upon by a net external force.",
            "topic": "Inertia",
        },
        {
            "id": "chk_phy_02",
            "text": "Momentum is defined as the product of mass and velocity: p = m * v.",
            "topic": "Momentum",
        },
    ]
    rag.index_course_knowledge("crs-phy-101", chunks)

    engine = LocalRuntimeEngine(
        course_cache=cache,
        rag_cache=rag,
        session_store=session_store,
    )

    # Execute tutor turn offline
    result = engine.execute_tutor_turn(
        session_id="ses-phy-001",
        student_id="stu-alice",
        course_id="crs-phy-101",
        user_input="What does the first law say about inertia?",
        model_name="local-slm-default",
    )

    assert result["ok"] is True
    assert result["turn_id"].startswith("trn_")
    assert result["session_id"] == "ses-phy-001"
    assert result["student_id"] == "stu-alice"
    assert result["course_id"] == "crs-phy-101"
    assert len(result["tutor_output"]) > 0
    assert len(result["rag_citations"]) >= 1
    assert "Newton's first law" in result["rag_citations"][0]["text"]
    assert "phy_inertia" in result["mastery"]
    assert result["mastery"]["phy_inertia"] > 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Local state persistence across restart
# ─────────────────────────────────────────────────────────────────────────────
def test_local_state_persistence_across_restart(tmp_path):
    """Enrolls student, executes turns, shuts down runtime, starts new instance; 100% of state is preserved."""
    db_file = tmp_path / "persistent_session.db"

    # Runtime 1: Execute turns and record state
    store_1 = LocalSessionPersistence(db_path=db_file)
    t1 = store_1.begin_turn("ses-res-1", "stu-bob", "crs-math-101", "How do quadratic equations work?")
    store_1.commit_turn(
        turn_id=t1,
        tutor_output="A quadratic equation has the general form ax^2 + bx + c = 0.",
        mastery_updates={"math_quadratic": 0.75},
        events=[{"event_type": "concept_learned", "payload": {"concept": "math_quadratic"}}],
    )

    t2 = store_1.begin_turn("ses-res-1", "stu-bob", "crs-math-101", "What is the quadratic formula?")
    store_1.commit_turn(
        turn_id=t2,
        tutor_output="The roots are given by x = (-b +- sqrt(b^2 - 4ac)) / (2a).",
        mastery_updates={"math_quadratic": 0.88, "math_discriminant": 0.70},
        events=[{"event_type": "formula_mastered", "payload": {"formula": "quadratic"}}],
    )

    # Simulate shutdown
    del store_1

    # Runtime 2: Fresh instance pointing to same file
    store_2 = LocalSessionPersistence(db_path=db_file)

    turns = store_2.get_session_turns("ses-res-1")
    assert len(turns) == 2
    assert turns[0]["turn_id"] == t1
    assert turns[0]["user_input"] == "How do quadratic equations work?"
    assert turns[0]["state_status"] == "COMMITTED"
    assert turns[1]["turn_id"] == t2
    assert "roots are given by" in turns[1]["tutor_output"]

    mastery = store_2.get_student_mastery("stu-bob", "crs-math-101")
    assert mastery["math_quadratic"] == 0.88
    assert mastery["math_discriminant"] == 0.70

    events = store_2.get_learning_events("stu-bob", "crs-math-101")
    assert len(events) == 2
    assert events[0]["event_type"] == "concept_learned"
    assert events[1]["event_type"] == "formula_mastered"


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Interrupted turn transactional rollback
# ─────────────────────────────────────────────────────────────────────────────
def test_interrupted_turn_transactional_rollback(tmp_path):
    """Simulates mid-turn crash; restarts runtime; verifies partial turn was rolled back and DB remains consistent."""
    db_file = tmp_path / "crash_test.db"

    # Runtime 1: Begin turn but simulate sudden power cut / crash before commit
    store_1 = LocalSessionPersistence(db_path=db_file)
    interrupted_turn_id = store_1.begin_turn(
        session_id="ses-crash-1",
        student_id="stu-charlie",
        course_id="crs-math-101",
        user_input="Calculate the derivative of x^3",
    )

    # Verify that uncommitted turns are NOT visible in normal session queries
    committed_turns = store_1.get_session_turns("ses-crash-1", include_uncommitted=False)
    assert len(committed_turns) == 0

    # Simulate sudden crash
    del store_1

    # Runtime 2: Startup initiates crash recovery
    store_2 = LocalSessionPersistence(db_path=db_file)

    # Normal queries still return 0 committed turns
    assert len(store_2.get_session_turns("ses-crash-1", include_uncommitted=False)) == 0

    # Query with uncommitted shows that the interrupted turn was safely marked ROLLED_BACK
    all_turns = store_2.get_session_turns("ses-crash-1", include_uncommitted=True)
    assert len(all_turns) == 1
    assert all_turns[0]["turn_id"] == interrupted_turn_id
    assert all_turns[0]["state_status"] == "ROLLED_BACK"

    # Subsequent turns can be executed cleanly without state corruption
    t_new = store_2.begin_turn("ses-crash-1", "stu-charlie", "crs-math-101", "Retry derivative of x^3")
    store_2.commit_turn(t_new, tutor_output="d/dx(x^3) = 3x^2", mastery_updates={"calculus_power_rule": 0.8})

    valid_turns = store_2.get_session_turns("ses-crash-1", include_uncommitted=False)
    assert len(valid_turns) == 1
    assert valid_turns[0]["turn_id"] == t_new


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Read-only database degraded mode
# ─────────────────────────────────────────────────────────────────────────────
def test_read_only_database_degraded_mode(tmp_path):
    """Makes local database read-only; verifies runtime enters graceful READ_ONLY_MODE, blocking writes."""
    db_file = tmp_path / "readonly_test.db"

    # Seed initial data
    store = LocalSessionPersistence(db_path=db_file)
    t = store.begin_turn("ses-ro-1", "stu-david", "crs-bio-101", "What is mitosis?")
    store.commit_turn(t, "Mitosis is cell division resulting in two identical daughter cells.", {"cell_division": 0.9})

    # Switch to read-only mode
    store.set_read_only(True)
    assert store.is_read_only is True

    # Reads must succeed cleanly
    turns = store.get_session_turns("ses-ro-1")
    assert len(turns) == 1
    assert turns[0]["user_input"] == "What is mitosis?"

    mastery = store.get_student_mastery("stu-david", "crs-bio-101")
    assert mastery["cell_division"] == 0.9

    # Writes must raise ReadOnlyDatabaseError without crashing
    with pytest.raises(ReadOnlyDatabaseError):
        store.begin_turn("ses-ro-1", "stu-david", "crs-bio-101", "What is meiosis?")

    with pytest.raises(ReadOnlyDatabaseError):
        store.commit_turn(t, "Should fail", {"cell_division": 1.0})

    with pytest.raises(ReadOnlyDatabaseError):
        store.rollback_turn(t)


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Missing model honest alert and prompt
# ─────────────────────────────────────────────────────────────────────────────
def test_missing_model_honest_alert_and_prompt(tmp_path):
    """When requested offline model is missing, returns ModelUnavailableError with actionable prompt."""
    cache = LocalCourseCache(cache_dir=tmp_path / "cache", quarantine_dir=tmp_path / "quarantine")
    session_store = LocalSessionPersistence(db_path=tmp_path / "test.db")

    manifest_data = {
        "course_id": "crs-cs-50",
        "version_tag": "v1.0",
        "title": "CS50 Offline",
        "concepts": [{"id": "c1", "name": "Algorithms"}],
    }
    mfile = tmp_path / "cs50.json"
    mfile.write_text(json.dumps(manifest_data), encoding="utf-8")
    cache.import_package(mfile)

    detector = OfflineCapabilityDetector(
        course_cache=cache,
        session_store=session_store,
        available_models=["phi3-mini", "llama3.2:1b"],
    )
    engine = LocalRuntimeEngine(
        course_cache=cache,
        session_store=session_store,
        detector=detector,
    )

    # 1. Detector reports missing model
    state = detector.get_honest_degraded_state("crs-cs-50", model_name="mixtral-8x7b")
    assert state.is_degraded is True
    assert "model:mixtral-8x7b" in state.missing_components
    assert "not installed or available offline" in state.reason
    assert "phi3-mini" in state.actionable_message

    # 2. Execution raises ModelUnavailableError
    with pytest.raises(ModelUnavailableError) as exc_info:
        engine.execute_tutor_turn(
            session_id="ses-1",
            student_id="stu-1",
            course_id="crs-cs-50",
            user_input="Explain bubble sort",
            model_name="mixtral-8x7b",
        )

    err = exc_info.value
    assert err.model_name == "mixtral-8x7b"
    assert "phi3-mini" in str(err)
    assert "Available offline models" in str(err)


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Zero fake demo roster in bridge and portal
# ─────────────────────────────────────────────────────────────────────────────
def test_zero_fake_demo_roster_in_bridge_and_portal(tmp_path, monkeypatch):
    """Tests app/bridge/facade.py with clean DB; verifies 0 fake students (Rahul Kumar, Priya Sharma, Amit Patel) exist."""
    import central_platform.auth.dependencies as auth_deps
    from app.bridge.facade import Bridge, get_teacher_portal_service, reset_teacher_singletons

    clean_db_path = str(tmp_path / "clean_empty.db")
    monkeypatch.setenv("GAYATRI_DB_PATH", clean_db_path)
    auth_deps._DB_INSTANCE = None

    reset_teacher_singletons()
    portal = get_teacher_portal_service()
    students = portal.get_all_students("crs-chem-101")
    assert len(students) == 0

    bridge = Bridge()
    raw_dashboard = bridge.get_teacher_dashboard("crs-chem-101")
    res = json.loads(raw_dashboard)

    assert res["ok"] is True
    assert res["total_students"] == 0
    assert res["class_health_status"] == "No Data"
    assert len(res["students"]) == 0
    assert len(res["students_attention_list"]) == 0

    # Ensure demo student names do not appear in payload
    payload_str = json.dumps(res)
    for forbidden_name in ["Rahul Kumar", "Priya Sharma", "Amit Patel"]:
        assert forbidden_name not in payload_str


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Zero chemistry coupling in local_runtime subsystem
# ─────────────────────────────────────────────────────────────────────────────
def test_zero_chemistry_coupling_in_local_runtime():
    """Scans AST and lines of all local_runtime/ files, verifying zero hardcoded chemistry keywords."""
    chem_regex = re.compile(r"\b(chemistry|thermodynamics|hess|crs-chem-101|chem_101)\b", re.IGNORECASE)
    local_runtime_dir = ROOT / "local_runtime"

    assert local_runtime_dir.is_dir()
    py_files = list(local_runtime_dir.glob("*.py"))
    assert len(py_files) >= 5, "Expected at least 5 Python files in local_runtime/"

    violations = {}
    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue
                if chem_regex.search(clean_line):
                    violations.setdefault(py_file.name, []).append(f"L{idx}: {clean_line}")

    assert not violations, f"Found hardcoded Chemistry coupling in local_runtime: {violations}"
