"""
scripts/seed_local_environment.py
Deterministic Local Environment Seeding Engine for Gayatri AI Platform.

Provisions a comprehensive, realistic demo environment across Student, Teacher,
and Admin personas for immediate local browser and desktop testing.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure root directory in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    AlertSeverity,
    AlertStatus,
    ClassGroup,
    Cohort,
    Concept,
    Course,
    Curriculum,
    CurriculumVersion,
    Enrollment,
    InterventionRecord,
    LearningEvent,
    Module,
    Organization,
    Prerequisite,
    Session,
    SessionStatus,
    Subject,
    TeacherInstructionRecord,
    Topic,
    User,
    UserRole,
)


def seed_local_environment(db_path: str = "gayatri_local.db") -> dict:
    """Seed comprehensive local demo data into the SQLite database."""
    print(f"\n[+] Initializing & Seeding Local Environment Database: {db_path}...")
    db = PlatformDatabase(db_path=db_path)

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Seed Organizations
    org_global = Organization(id="org_global", name="Gayatri Central Network", slug="gayatri-central")
    org_dps = Organization(id="org_dps", name="Delhi Public School (R.K. Puram)", slug="dps-rkp")
    org_kv = Organization(id="org_kv", name="Kendriya Vidyalaya (IIT Campus)", slug="kv-iit")
    
    for org in [org_global, org_dps, org_kv]:
        db.create_organization(org)
    print("  [OK] Seeded 3 Organizations (Global, DPS, KV)")

    # 2. Seed Users & Generate Auth Tokens
    users_data = [
        {
            "id": "usr_superadmin",
            "email": "superadmin@gayatri.edu",
            "name": "Dr. Gayatri Admin (Super Admin)",
            "role": UserRole.SUPER_ADMIN,
            "org_id": "org_global",
        },
        {
            "id": "usr_dps_admin",
            "email": "admin@dps.edu",
            "name": "Principal Ramesh Gupta (Org Admin)",
            "role": UserRole.ORG_ADMIN,
            "org_id": "org_dps",
        },
        {
            "id": "usr_teacher_sharma",
            "email": "teacher.sharma@dps.edu",
            "name": "Prof. Anita Sharma (Chemistry Lead)",
            "role": UserRole.TEACHER,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_arjun",
            "email": "student.arjun@dps.edu",
            "name": "Arjun Patel (Grade 11 Student - Needs Support)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_priya",
            "email": "student.priya@dps.edu",
            "name": "Priya Sen (Grade 11 Student - Advanced)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
    ]

    tokens = {}
    for u in users_data:
        usr_obj = User(
            id=u["id"],
            organization_id=u["org_id"],
            email=u["email"],
            full_name=u["name"],
            role=u["role"],
        )
        db.create_user(usr_obj)
        tok = create_access_token(
            user_id=u["id"],
            role=u["role"].value if isinstance(u["role"], UserRole) else str(u["role"]),
            organization_id=u["org_id"],
        )
        tokens[u["id"]] = {
            "name": u["name"],
            "email": u["email"],
            "role": u["role"].value,
            "organization_id": u["org_id"],
            "token": tok,
        }
    print(f"  [OK] Seeded {len(users_data)} Multi-Role Users with JWT Tokens")

    # 3. Seed Course & Subject
    course = Course(
        id="crs_chem_101",
        organization_id="org_dps",
        code="CHEM-101",
        title="Class 11 Chemistry - Equilibrium & Thermodynamics",
        description="Core foundational chemistry covering dynamic chemical equilibrium, Le Chatelier's principle, and ionic solutions.",
    )
    db.create_course(course)

    subject = Subject(
        id="subj_chem",
        course_id="crs_chem_101",
        name="Physical Chemistry",
        code="PHYS_CHEM",
    )
    db.create_subject(subject)
    print("  [OK] Seeded Course & Physical Chemistry Subject")

    # 4. Seed Published Curriculum DAG
    curriculum = Curriculum(
        id="cur_chem_101",
        course_id="crs_chem_101",
        title="NCERT / CBSE Class 11 Chemistry Standard Curriculum",
        version="1.0.0",
    )
    db.create_curriculum(curriculum)

    cur_version = CurriculumVersion(
        id="ver_chem_101_v1",
        curriculum_id="cur_chem_101",
        version_num="1.0.0",
        change_log="Initial official published release",
        status="published",
        published_at=now_iso,
    )
    db.create_curriculum_version(cur_version)

    # Modules
    mod_eq = Module(
        id="mod_equilibrium",
        curriculum_id="cur_chem_101",
        title="Module 1: Chemical Equilibrium",
        sequence_order=1,
        subject_id="subj_chem",
    )
    mod_thermo = Module(
        id="mod_thermo",
        curriculum_id="cur_chem_101",
        title="Module 2: Thermodynamics",
        sequence_order=2,
        subject_id="subj_chem",
    )
    db.create_module(mod_eq)
    db.create_module(mod_thermo)

    # Topics
    top_dyn = Topic(
        id="top_dynamic_eq",
        module_id="mod_equilibrium",
        title="Topic 1.1: Dynamic Nature of Equilibrium",
        sequence_order=1,
    )
    top_le_chat = Topic(
        id="top_le_chatelier",
        module_id="mod_equilibrium",
        title="Topic 1.2: Le Chatelier's Principle & Applications",
        sequence_order=2,
    )
    db.create_topic(top_dyn)
    db.create_topic(top_le_chat)

    # Concepts
    c1 = Concept(
        id="c_equilibrium_const",
        topic_id="top_dynamic_eq",
        name="Equilibrium Constant (Kc and Kp)",
        description="Mathematical formulation and physical interpretation of reaction quotients and equilibrium constants.",
        difficulty=0.4,
    )
    c2 = Concept(
        id="c_le_chatelier",
        topic_id="top_le_chatelier",
        name="Le Chatelier's Principle (Concentration, Pressure, Temperature)",
        description="Qualitative prediction of equilibrium response to external perturbations in closed gaseous and aqueous systems.",
        difficulty=0.6,
    )
    c3 = Concept(
        id="c_haber_process",
        topic_id="top_le_chatelier",
        name="Industrial Haber Process Synthesis",
        description="Optimal temperature, pressure, and catalyst conditions for ammonia synthesis using Le Chatelier's principles.",
        difficulty=0.7,
    )
    db.create_concept(c1)
    db.create_concept(c2)
    db.create_concept(c3)

    # Prerequisites: c_equilibrium_const -> c_le_chatelier -> c_haber_process
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_equilibrium_const", dependent_concept_id="c_le_chatelier"))
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_le_chatelier", dependent_concept_id="c_haber_process"))
    print("  [OK] Seeded Immutably Published Curriculum DAG with 3 Concepts & Prerequisites")

    # 5. Seed Class Group, Cohort & Enrollments
    class_group = ClassGroup(
        id="cls_grade11_a",
        organization_id="org_dps",
        course_id="crs_chem_101",
        name="Grade 11 Section A",
        section="A",
    )
    db.create_class_group(class_group)

    cohort = Cohort(
        id="coh_2026_a",
        class_group_id="cls_grade11_a",
        name="Batch 2026-2027",
        academic_year="2026-2027",
    )
    db.create_cohort(cohort)

    enr_arjun = Enrollment(
        id="enr_arjun_01",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        cohort_id="coh_2026_a",
        enrolled_at=now_iso,
    )
    enr_priya = Enrollment(
        id="enr_priya_01",
        student_id="usr_student_priya",
        course_id="crs_chem_101",
        cohort_id="coh_2026_a",
        enrolled_at=now_iso,
    )
    db.create_enrollment(enr_arjun)
    db.create_enrollment(enr_priya)
    print("  [OK] Seeded Class Group, Cohort, and 2 Student Enrollments")

    # 6. Seed Tutoring Sessions & Learning Events
    sess_arjun = Session(
        id="ses_arjun_chem_01",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        concept_id="c_le_chatelier",
        status=SessionStatus.ACTIVE,
        started_at=now_iso,
    )
    sess_priya = Session(
        id="ses_priya_chem_01",
        student_id="usr_student_priya",
        course_id="crs_chem_101",
        concept_id="c_haber_process",
        status=SessionStatus.COMPLETED,
        started_at=now_iso,
    )
    db.create_session(sess_arjun)
    db.create_session(sess_priya)

    # Arjun's interaction events (Misconception & Hints)
    events = [
        LearningEvent(
            id="evt_arjun_01",
            session_id="ses_arjun_chem_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_equilibrium_const",
            event_type="question_answered",
            payload={"question_id": "q_eq_01", "is_correct": True, "score": 1.0, "time_spent_sec": 45},
            score=1.0,
        ),
        LearningEvent(
            id="evt_arjun_02",
            session_id="ses_arjun_chem_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_le_chatelier",
            event_type="misconception_triggered",
            payload={
                "misconception_code": "EQUILIBRIUM_CONC_EQUALITY",
                "diagnosis": "Student incorrectly assumes reactant and product concentrations must be equal at equilibrium.",
                "remediation_hint": "Remember: Dynamic equilibrium means equal forward and backward rates, NOT necessarily equal amounts.",
            },
            score=0.0,
        ),
        LearningEvent(
            id="evt_arjun_03",
            session_id="ses_arjun_chem_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_le_chatelier",
            event_type="hint_requested",
            payload={"hint_level": 2, "topic": "Pressure effects on gaseous equilibrium"},
            score=0.5,
        ),
        # Priya's interaction events (High Mastery)
        LearningEvent(
            id="evt_priya_01",
            session_id="ses_priya_chem_01",
            student_id="usr_student_priya",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_haber_process",
            event_type="question_answered",
            payload={"question_id": "q_haber_01", "is_correct": True, "score": 1.0, "time_spent_sec": 28},
            score=1.0,
        ),
    ]

    for ev in events:
        db.record_learning_event(ev)
    print("  [OK] Seeded Sessions & 4 Learning Events (demonstrating misconception diagnosis and hint usage)")

    # 7. Seed Teacher AI Instructions & Interventions
    instruction = TeacherInstructionRecord(
        id="inst_sharma_01",
        teacher_id="usr_teacher_sharma",
        student_id="all",
        course_id="crs_chem_101",
        instruction_text="Emphasize the difference between reaction rates and equilibrium concentrations. Ask socratic questions when students confuse moles with volume.",
        priority=1,
        is_active=True,
    )
    db.create_teacher_instruction(instruction)

    alert = InterventionRecord(
        id="alt_arjun_le_chatelier",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        severity=AlertSeverity.WARNING,
        alert_type="misconception_repetition",
        message="Arjun Patel has triggered the Equilibrium Concentration Equality misconception twice in the current session.",
        status=AlertStatus.ACTIVE,
        assigned_teacher="usr_teacher_sharma",
    )
    db.create_intervention(alert)
    print("  [OK] Seeded Active Teacher Directive & Pending At-Risk Intervention Alert")

    # 8. Save local tokens to JSON file for easy copy-paste
    token_file = PROJECT_ROOT / "local_auth_tokens.json"
    token_file.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"\n[KEY] Generated Test Auth Tokens written to: {token_file.name}")

    print("\n[SUCCESS] Local Environment Seeding Complete! Ready for Testing.\n")
    return tokens


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "gayatri_local.db"
    seed_local_environment(db_file)
