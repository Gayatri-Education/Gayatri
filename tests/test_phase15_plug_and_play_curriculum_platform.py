"""Comprehensive Verification Test Suite for Phase 15: Plug-and-Play Curriculum.

Master Plan Section 24 Requirements:
1. Target Hierarchy:
   Course -> Curriculum Version -> Subject -> Module -> Topic -> Concept -> Prerequisites -> Activities -> Assessments.
2. Immutability Invariant:
   Every curriculum is versioned, validated, published, and strictly immutable after publication.
3. Rigorous DAG & Semantic Validation:
   - Cycle detection: No circular prerequisite chains (A -> B -> A).
   - No orphan prerequisites: Prerequisites must reference valid concepts within curriculum scope.
   - Stable identifier enforcement: Alphanumeric and dot/hyphen identifiers only (no free text).
4. Declarative Package Import / Export:
   Round-trip fidelity across courses.
5. Tutor Decoupling:
   Multi-subject independence (Chemistry, Math, Python running side-by-side).
6. Multi-tenant RBAC gatekeeping:
   Students blocked with 403 Forbidden on authoring/importing/publishing.
"""

from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.dependencies import get_db
from central_platform.auth.tokens import create_access_token
from central_platform.curriculum.service import (
    CurriculumService,
    CurriculumStatus,
)
from central_platform.models.schema import (
    Course,
    Organization,
    User,
    UserRole,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def super_admin_token():
    return create_access_token(user_id="super-admin-curriculum", role="SUPER_ADMIN")


@pytest.fixture
def student_token():
    return create_access_token(user_id="student-curriculum", role="STUDENT")


@pytest.fixture
def test_admin_user():
    return User(
        id="usr-admin-p15",
        email="curriculum_admin@gayatri.edu",
        full_name="Curriculum Admin",
        role=UserRole.SUPER_ADMIN,
        organization_id="org-default",
    )


@pytest.fixture
def curriculum_service():
    db = get_db()
    # Ensure default organization exists
    db.create_organization(Organization(id="org-default", name="Default Org", slug="default-org"))
    return CurriculumService(db)


# ── 1. Full Hierarchy Construction & Node Traversal ───────────────────────

def test_curriculum_full_hierarchy_construction(curriculum_service, test_admin_user):
    db = curriculum_service.db
    # Create course
    course = Course(
        id="crs-physics-101",
        organization_id="org-default",
        code="PHY-101",
        title="Class 11 Physics",
        description="Classical Mechanics",
    )
    db.create_course(course)

    # Create curriculum & initial draft version
    curr, ver = curriculum_service.create_curriculum(
        admin=test_admin_user,
        course_id=course.id,
        title="CBSE Physics Curriculum 2026",
        initial_version="v1.0.0",
    )
    assert curr.id.startswith("cur-")
    assert ver.version_num == "v1.0.0"
    assert ver.status == CurriculumStatus.DRAFT.value

    # Add Module
    mod = curriculum_service.add_module(
        admin=test_admin_user,
        version_id=ver.id,
        title="Kinematics",
        sequence_order=1,
    )
    assert mod.id.startswith("mod-")

    # Add Topic
    top = curriculum_service.add_topic(
        admin=test_admin_user,
        version_id=ver.id,
        module_id=mod.id,
        title="Motion in a Straight Line",
        sequence_order=1,
    )
    assert top.id.startswith("top-")

    # Add Concepts & Prerequisites
    c1 = curriculum_service.add_concept(
        admin=test_admin_user,
        version_id=ver.id,
        topic_id=top.id,
        concept_id="phy_kin_displacement",
        name="Displacement and Distance",
        description="Position-time coordinates",
        difficulty=0.3,
        prerequisites=[],
    )
    c2 = curriculum_service.add_concept(
        admin=test_admin_user,
        version_id=ver.id,
        topic_id=top.id,
        concept_id="phy_kin_velocity",
        name="Velocity and Speed",
        description="Rate of change of displacement",
        difficulty=0.4,
        prerequisites=["phy_kin_displacement"],
    )
    c3 = curriculum_service.add_concept(
        admin=test_admin_user,
        version_id=ver.id,
        topic_id=top.id,
        concept_id="phy_kin_acceleration",
        name="Instantaneous Acceleration",
        description="Derivative of velocity with respect to time",
        difficulty=0.5,
        prerequisites=["phy_kin_velocity"],
    )

    assert c1.id == "phy_kin_displacement"
    assert c2.id == "phy_kin_velocity"
    assert c3.id == "phy_kin_acceleration"

    # Verify hierarchy traversal
    hierarchy = curriculum_service.get_curriculum_hierarchy(curr.id)
    assert hierarchy["total_modules"] >= 1
    assert hierarchy["total_topics"] >= 1
    assert hierarchy["total_concepts"] == 3


# ── 2. Immutability Upon Publication ──────────────────────────────────────

def test_curriculum_immutability_upon_publication(curriculum_service, test_admin_user):
    db = curriculum_service.db
    course = Course(id="crs-immutable-101", organization_id="org-default", code="IMM-101", title="Immutable Course")
    db.create_course(course)

    curr, ver = curriculum_service.create_curriculum(test_admin_user, course.id, "Immutable Curriculum", "v1.0.0")
    mod = curriculum_service.add_module(test_admin_user, ver.id, "Module A")
    top = curriculum_service.add_topic(test_admin_user, ver.id, mod.id, "Topic A")
    curriculum_service.add_concept(test_admin_user, ver.id, top.id, "imm_concept_1", "Concept 1", difficulty=0.3)

    # Publish version
    pub_ver = curriculum_service.publish_curriculum_version(test_admin_user, ver.id)
    assert pub_ver.status == CurriculumStatus.PUBLISHED.value
    assert pub_ver.published_at is not None

    # Modifying published version MUST raise ValueError
    with pytest.raises(ValueError, match="is PUBLISHED and immutable"):
        curriculum_service.add_module(test_admin_user, ver.id, "Illegal Module")

    with pytest.raises(ValueError, match="is PUBLISHED and immutable"):
        curriculum_service.add_topic(test_admin_user, ver.id, mod.id, "Illegal Topic")

    with pytest.raises(ValueError, match="is PUBLISHED and immutable"):
        curriculum_service.add_concept(test_admin_user, ver.id, top.id, "imm_concept_2", "Illegal Concept")


# ── 3. Draft Versioning & Cloning ─────────────────────────────────────────

def test_curriculum_draft_cloning_and_versioning(curriculum_service, test_admin_user):
    db = curriculum_service.db
    course = Course(id="crs-versioning-101", organization_id="org-default", code="VER-101", title="Versioning Course")
    db.create_course(course)

    curr, v1 = curriculum_service.create_curriculum(test_admin_user, course.id, "Versioning Curriculum", "v1.0.0")
    mod1 = curriculum_service.add_module(test_admin_user, v1.id, "Initial Module")
    top1 = curriculum_service.add_topic(test_admin_user, v1.id, mod1.id, "Initial Topic")
    curriculum_service.add_concept(test_admin_user, v1.id, top1.id, "ver_concept_1", "Initial Concept")

    # Publish v1.0.0
    curriculum_service.publish_curriculum_version(test_admin_user, v1.id)

    # Create new draft v2.0.0 cloned from v1.0.0
    v2 = curriculum_service.create_version_draft(
        admin=test_admin_user,
        curriculum_id=curr.id,
        new_version_num="v2.0.0",
        change_log="Added advanced topics in v2.0.0",
        base_version_id=v1.id,
    )
    assert v2.version_num == "v2.0.0"
    assert v2.status == CurriculumStatus.DRAFT.value

    # v2.0.0 is mutable!
    mod2 = curriculum_service.add_module(test_admin_user, v2.id, "Advanced Module")
    assert mod2.id.startswith("mod-")

    # Duplicate version number rejected
    with pytest.raises(ValueError, match="already exists"):
        curriculum_service.create_version_draft(test_admin_user, curr.id, "v2.0.0")


# ── 4. Prerequisite Cycle Rejection (DAG Enforcement) ─────────────────────

def test_curriculum_prerequisite_cycle_rejection(curriculum_service, test_admin_user):
    # Test circular dependency: A -> B -> A
    cycle_package = {
        "title": "Cyclic Test Curriculum",
        "version": "v1.0.0",
        "concepts": [
            {"id": "cycle_a", "name": "Concept A", "difficulty": 0.3, "prerequisites": ["cycle_b"]},
            {"id": "cycle_b", "name": "Concept B", "difficulty": 0.4, "prerequisites": ["cycle_a"]},
        ],
    }
    report = curriculum_service.validate_curriculum(cycle_package)
    assert report.is_valid is False
    assert any("cycle" in err.lower() for err in report.errors)
    assert len(report.cycle_nodes) >= 1

    # Multi-hop cycle: X -> Y -> Z -> X
    multihop_package = {
        "title": "Multi-hop Cyclic Curriculum",
        "version": "v1.0.0",
        "concepts": [
            {"id": "cycle_x", "name": "Concept X", "difficulty": 0.3, "prerequisites": ["cycle_y"]},
            {"id": "cycle_y", "name": "Concept Y", "difficulty": 0.4, "prerequisites": ["cycle_z"]},
            {"id": "cycle_z", "name": "Concept Z", "difficulty": 0.5, "prerequisites": ["cycle_x"]},
        ],
    }
    report2 = curriculum_service.validate_curriculum(multihop_package)
    assert report2.is_valid is False
    assert any("cycle" in err.lower() for err in report2.errors)


# ── 5. Orphan Prerequisite & Formatting Rejection ─────────────────────────

def test_curriculum_orphan_prerequisite_rejection(curriculum_service, test_admin_user):
    # Prerequisite pointing to non-existent concept
    orphan_package = {
        "title": "Orphan Test Curriculum",
        "version": "v1.0.0",
        "concepts": [
            {"id": "valid_concept_1", "name": "Valid Concept", "difficulty": 0.3, "prerequisites": ["non_existent_ghost"]},
        ],
    }
    report = curriculum_service.validate_curriculum(orphan_package)
    assert report.is_valid is False
    assert any("Orphan prerequisite" in err for err in report.errors)
    assert "non_existent_ghost" in report.orphan_prerequisites


def test_curriculum_invalid_identifier_rejection(curriculum_service):
    # Free-text ID with spaces and punctuation must be rejected
    invalid_package = {
        "title": "Invalid ID Curriculum",
        "version": "v1.0.0",
        "concepts": [
            {"id": "invalid concept with spaces!", "name": "Bad ID", "difficulty": 0.3, "prerequisites": []},
        ],
    }
    report = curriculum_service.validate_curriculum(invalid_package)
    assert report.is_valid is False
    assert any("invalid" in err.lower() for err in report.errors)


# ── 6. Declarative Package Import & Export Round-Trip ─────────────────────

def test_curriculum_import_export_round_trip(curriculum_service, test_admin_user):
    db = curriculum_service.db
    course = Course(id="crs-roundtrip-101", organization_id="org-default", code="RND-101", title="Roundtrip Course")
    db.create_course(course)

    input_package = {
        "title": "CBSE Class 10 Trigonometry",
        "subject": "Mathematics",
        "version": "v1.0.0",
        "modules": [
            {
                "title": "Trigonometric Ratios",
                "topics": [
                    {
                        "title": "Basic Ratios",
                        "concepts": [
                            {"id": "math_trig_sine", "name": "Sine Function", "description": "Opposite over Hypotenuse", "difficulty": 0.3, "prerequisites": []},
                            {"id": "math_trig_cosine", "name": "Cosine Function", "description": "Adjacent over Hypotenuse", "difficulty": 0.3, "prerequisites": []},
                            {"id": "math_trig_tangent", "name": "Tangent Function", "description": "Sine over Cosine", "difficulty": 0.4, "prerequisites": ["math_trig_sine", "math_trig_cosine"]},
                        ],
                    }
                ],
            }
        ],
    }

    # Import package
    result = curriculum_service.import_curriculum_package(
        admin=test_admin_user,
        course_id=course.id,
        package=input_package,
        publish=True,
    )
    assert result["status"] == "published"
    version_id = result["version_id"]

    # Export package
    exported = curriculum_service.export_curriculum_package(version_id)
    assert exported["title"] == "CBSE Class 10 Trigonometry"
    assert exported["version"] == "v1.0.0"
    assert exported["status"] == "published"

    # Verify concept fidelity
    concept_ids = [c["id"] for c in exported.get("concepts", [])]
    if not concept_ids:
        # Check inside nested modules
        for m in exported.get("modules", []):
            for t in m.get("topics", []):
                for c in t.get("concepts", []):
                    concept_ids.append(c["id"])

    assert "math_trig_sine" in concept_ids
    assert "math_trig_cosine" in concept_ids
    assert "math_trig_tangent" in concept_ids


# ── 7. Multi-Subject Independence & Decoupling ───────────────────────────

def test_curriculum_multi_subject_coexistence(curriculum_service, test_admin_user):
    db = curriculum_service.db

    # Course 1: Python Beginner
    py_course = Course(id="crs-py-01", organization_id="org-default", code="PY-101", title="Python 101")
    db.create_course(py_course)
    py_pkg = {
        "title": "Python Basics",
        "subject": "Computer Science",
        "version": "v1.0.0",
        "concepts": [
            {"id": "py_variables", "name": "Variables", "difficulty": 0.2, "prerequisites": []},
            {"id": "py_loops", "name": "Loops", "difficulty": 0.4, "prerequisites": ["py_variables"]},
        ],
    }
    curriculum_service.import_curriculum_package(test_admin_user, py_course.id, py_pkg, publish=True)

    # Course 2: Grade 9 Math
    math_course = Course(id="crs-math-01", organization_id="org-default", code="MTH-101", title="Math 101")
    db.create_course(math_course)
    math_pkg = {
        "title": "Grade 9 Geometry",
        "subject": "Mathematics",
        "version": "v1.0.0",
        "concepts": [
            {"id": "math_points", "name": "Points and Lines", "difficulty": 0.2, "prerequisites": []},
            {"id": "math_triangles", "name": "Triangles", "difficulty": 0.5, "prerequisites": ["math_points"]},
        ],
    }
    curriculum_service.import_curriculum_package(test_admin_user, math_course.id, math_pkg, publish=True)

    # Verify independent retrieval
    py_hierarchy = curriculum_service.get_curriculum_hierarchy(py_course.id)
    assert any("py_variables" in str(m) for m in py_hierarchy["modules"])
    assert not any("math_points" in str(m) for m in py_hierarchy["modules"])

    math_hierarchy = curriculum_service.get_curriculum_hierarchy(math_course.id)
    assert any("math_points" in str(m) for m in math_hierarchy["modules"])
    assert not any("py_variables" in str(m) for m in math_hierarchy["modules"])


# ── 8. REST API Endpoints Lifecycle ───────────────────────────────────────

def test_curriculum_rest_api_full_lifecycle(client, super_admin_token):
    # 1. Create a course first via Admin API
    res_course = client.post(
        "/api/v1/admin/courses",
        json={"code": "API-CURR-101", "title": "API Curriculum Course"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_course.status_code == 201
    course_id = res_course.json()["data"]["id"]

    # 2. Import curriculum package via POST /curricula/import
    package_data = {
        "title": "Class 12 Electrodynamics",
        "subject": "Physics",
        "version": "v1.0.0",
        "concepts": [
            {"id": "phys_coulomb_law", "name": "Coulomb Law", "difficulty": 0.3, "prerequisites": []},
            {"id": "phys_electric_field", "name": "Electric Field", "difficulty": 0.4, "prerequisites": ["phys_coulomb_law"]},
        ],
    }
    res_import = client.post(
        "/api/v1/curricula/import",
        json={"course_id": course_id, "package": package_data, "publish": False},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_import.status_code == 201
    import_data = res_import.json()["data"]
    curriculum_id = import_data["curriculum_id"]
    version_id = import_data["version_id"]
    assert import_data["status"] == "draft"

    # 3. Validate curriculum version via POST /curricula/versions/{id}/validate
    res_val = client.post(f"/api/v1/curricula/versions/{version_id}/validate")
    assert res_val.status_code == 200
    assert res_val.json()["data"]["is_valid"] is True

    # 4. Publish curriculum version via POST /curricula/versions/{id}/publish
    res_pub = client.post(
        f"/api/v1/curricula/versions/{version_id}/publish",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "published"

    # 5. Retrieve dynamic hierarchy via GET /curricula/{course_id}
    res_curr = client.get(f"/api/v1/curricula/{course_id}")
    assert res_curr.status_code == 200
    data = res_curr.json()["data"]
    assert data["course_id"] == course_id
    assert data["total_concepts"] >= 2

    # 6. Retrieve detailed hierarchy via GET /curricula/versions/{id}/hierarchy
    res_hier = client.get(f"/api/v1/curricula/versions/{version_id}/hierarchy")
    assert res_hier.status_code == 200
    assert res_hier.json()["data"]["version"] == "v1.0.0"

    # 7. List versions via GET /curricula/{curriculum_id}/versions
    res_vers = client.get(f"/api/v1/curricula/{curriculum_id}/versions")
    assert res_vers.status_code == 200
    assert len(res_vers.json()["data"]) >= 1

    # 8. Create draft v1.1.0 via POST /curricula/{curriculum_id}/versions
    res_new_ver = client.post(
        f"/api/v1/curricula/{curriculum_id}/versions",
        json={"version_num": "v1.1.0", "change_log": "Added Gauss Law", "base_version_id": version_id},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_new_ver.status_code == 201
    assert res_new_ver.json()["data"]["version_num"] == "v1.1.0"

    # 9. Export package via GET /curricula/versions/{version_id}/export
    res_exp = client.get(f"/api/v1/curricula/versions/{version_id}/export")
    assert res_exp.status_code == 200
    assert res_exp.json()["data"]["title"] == "Class 12 Electrodynamics"


# ── 9. RBAC Security Rejection for Students ───────────────────────────────

def test_curriculum_authoring_strictly_rejects_students(client, student_token):
    # Student attempts to import curriculum package (403)
    r_import = client.post(
        "/api/v1/curricula/import",
        json={"course_id": "crs-chem-101", "package": {"title": "Hacked", "concepts": []}},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_import.status_code == 403

    # Student attempts to create version draft (403)
    r_ver = client.post(
        "/api/v1/curricula/cur-test-123/versions",
        json={"version_num": "v9.9.9"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_ver.status_code == 403

    # Student attempts to publish version (403)
    r_pub = client.post(
        "/api/v1/curricula/versions/cv-test-123/publish",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_pub.status_code == 403
