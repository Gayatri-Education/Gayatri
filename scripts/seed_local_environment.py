"""
scripts/seed_local_environment.py
Deterministic Local Demo Environment Seeding Engine for Gayatri AI Platform.

Provisions a comprehensive, realistic demo environment across Student, Teacher,
and Admin personas for immediate local browser showcase, demo video recording,
and cross-portal verification.
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
    AIModel,
    AIProvider,
    AlertSeverity,
    AlertStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentType,
    AuditLog,
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
    print(f"\n[+] Initializing & Seeding Local Demo Database: {db_path}...")
    db = PlatformDatabase(db_path=db_path)

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Seed Organizations
    orgs = [
        Organization(id="org_global", name="Gayatri Central Network", slug="gayatri-central"),
        Organization(id="org_dps", name="Delhi Public School (R.K. Puram)", slug="dps-rkp"),
        Organization(id="org_kv", name="Kendriya Vidyalaya (IIT Campus)", slug="kv-iit"),
        Organization(id="org_mumbai", name="Mumbai Institute of Science", slug="mis-mumbai"),
        Organization(id="org_bangalore", name="Bangalore STEM Academy", slug="bsa-blr"),
        Organization(id="org_hyderabad", name="Hyderabad Excellence College", slug="hec-hyd"),
    ]
    for org in orgs:
        db.create_organization(org)
    print(f"  [OK] Seeded {len(orgs)} Educational Organizations")

    # 2. Seed Users & Generate Auth Tokens
    users_data = [
        # Super Admin
        {
            "id": "usr_superadmin",
            "email": "superadmin@gayatri.edu",
            "name": "Dr. Gayatri Admin (Super Admin)",
            "role": UserRole.SUPER_ADMIN,
            "org_id": "org_global",
        },
        # Org Admins
        {
            "id": "usr_dps_admin",
            "email": "admin@dps.edu",
            "name": "Principal Ramesh Gupta (DPS Admin)",
            "role": UserRole.ORG_ADMIN,
            "org_id": "org_dps",
        },
        {
            "id": "usr_kv_admin",
            "email": "admin@kv.edu",
            "name": "Vice-Principal Sunita Rao (KV Admin)",
            "role": UserRole.ORG_ADMIN,
            "org_id": "org_kv",
        },
        # Teachers
        {
            "id": "usr_teacher_sharma",
            "email": "teacher.sharma@dps.edu",
            "name": "Prof. Anita Sharma (Chemistry Lead)",
            "role": UserRole.TEACHER,
            "org_id": "org_dps",
        },
        {
            "id": "usr_teacher_verma",
            "email": "teacher.verma@dps.edu",
            "name": "Dr. Rajesh Verma (Physics Faculty)",
            "role": UserRole.TEACHER,
            "org_id": "org_dps",
        },
        {
            "id": "usr_teacher_sundaram",
            "email": "teacher.sundaram@dps.edu",
            "name": "Mrs. Meenakshi Sundaram (Mathematics Lead)",
            "role": UserRole.TEACHER,
            "org_id": "org_dps",
        },
        {
            "id": "usr_teacher_swaminathan",
            "email": "teacher.swami@kv.edu",
            "name": "Dr. Arvind Swaminathan (Biology Faculty)",
            "role": UserRole.TEACHER,
            "org_id": "org_kv",
        },
        # Students (Rich Cohort)
        {
            "id": "usr_student_arjun",
            "email": "student.arjun@dps.edu",
            "name": "Arjun Patel (Grade 11 - Focus Persona / Needs Support)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_priya",
            "email": "student.priya@dps.edu",
            "name": "Priya Sen (Grade 11 - Advanced Mastery)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_rahul",
            "email": "student.rahul@dps.edu",
            "name": "Rahul Sharma (Grade 11 - Steady Progress)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_ananya",
            "email": "student.ananya@dps.edu",
            "name": "Ananya Verma (Grade 11 - Moderate Support)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_rohan",
            "email": "student.rohan@dps.edu",
            "name": "Rohan Gupta (Grade 11 - Misconception Trapped)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_tanvi",
            "email": "student.tanvi@dps.edu",
            "name": "Tanvi Deshmukh (Grade 11 - Visual Learner)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_aditya",
            "email": "student.aditya@dps.edu",
            "name": "Aditya Kulkarni (Grade 11 - High Aptitude)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_sneha",
            "email": "student.sneha@dps.edu",
            "name": "Sneha Nair (Grade 11 - Chemistry Enthusiast)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_vikram",
            "email": "student.vikram@kv.edu",
            "name": "Vikramaditya Roy (Grade 11 KV - Physics Specialist)",
            "role": UserRole.STUDENT,
            "org_id": "org_kv",
        },
        {
            "id": "usr_student_kavya",
            "email": "student.kavya@kv.edu",
            "name": "Kavya Iyer (Grade 11 KV - Biology Lead)",
            "role": UserRole.STUDENT,
            "org_id": "org_kv",
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
    print(f"  [OK] Seeded {len(users_data)} Multi-Tiered Users (Admins, Faculty, Students)")

    # 3. Seed Courses & Subjects
    courses_data = [
        Course(
            id="crs_chem_101",
            organization_id="org_dps",
            code="CHEM-101",
            title="Class 11 Chemistry - Equilibrium & Thermodynamics",
            description="Core foundational chemistry covering dynamic chemical equilibrium, Le Chatelier's principle, and thermodynamics.",
        ),
        Course(
            id="crs_chem_102",
            organization_id="org_dps",
            code="CHEM-102",
            title="Class 12 Chemistry - Electrochemistry & Organic Mechanisms",
            description="Advanced reaction mechanisms, Galvanic cells, Nernst equation, and coordination complexes.",
        ),
        Course(
            id="crs_phys_101",
            organization_id="org_dps",
            code="PHYS-101",
            title="Class 11 Physics - Mechanics & Waves",
            description="Comprehensive Newtonian mechanics, work-energy theorem, gravitation, and oscillations.",
        ),
        Course(
            id="crs_math_101",
            organization_id="org_dps",
            code="MATH-101",
            title="Class 11 Mathematics - Calculus & Vectors",
            description="Differential calculus, limits, continuity, rate of change, and vector algebra.",
        ),
        Course(
            id="crs_bio_101",
            organization_id="org_kv",
            code="BIO-101",
            title="Class 11 Biology - Cell Dynamics & Genetics",
            description="Cellular ultrastructure, biomolecules, cell cycle, and Mendelian principles of inheritance.",
        ),
    ]
    for c in courses_data:
        db.create_course(c)

    subjects_data = [
        Subject(id="subj_chem", course_id="crs_chem_101", name="Physical Chemistry", code="PHYS_CHEM"),
        Subject(id="subj_org_chem", course_id="crs_chem_102", name="Organic Chemistry", code="ORG_CHEM"),
        Subject(id="subj_phys", course_id="crs_phys_101", name="Classical Mechanics", code="CLASS_MECH"),
        Subject(id="subj_math", course_id="crs_math_101", name="Calculus & Analysis", code="CALC_ANALYSIS"),
        Subject(id="subj_bio", course_id="crs_bio_101", name="Cell Biology", code="CELL_BIO"),
    ]
    for s in subjects_data:
        db.create_subject(s)
    print(f"  [OK] Seeded {len(courses_data)} Comprehensive Courses & Subjects")

    # 4. Seed Published Curricula DAGs across Disciplines
    curricula_data = [
        Curriculum(id="cur_chem_101", course_id="crs_chem_101", title="NCERT / CBSE Class 11 Chemistry Standard Curriculum", version="1.0.0"),
        Curriculum(id="cur_phys_101", course_id="crs_phys_101", title="CBSE Class 11 Physics Standard Curriculum", version="1.0.0"),
        Curriculum(id="cur_math_101", course_id="crs_math_101", title="CBSE Class 11 Mathematics Standard Curriculum", version="1.0.0"),
    ]
    for cur in curricula_data:
        db.create_curriculum(cur)
        ver = CurriculumVersion(
            id=f"ver_{cur.id}_v1",
            curriculum_id=cur.id,
            version_num="1.0.0",
            change_log="Official published release for academic session 2026-2027",
            status="published",
            published_at=now_iso,
        )
        db.create_curriculum_version(ver)

    # Modules
    modules_data = [
        Module(id="mod_equilibrium", curriculum_id="cur_chem_101", title="Module 1: Chemical Equilibrium", sequence_order=1, subject_id="subj_chem"),
        Module(id="mod_thermo", curriculum_id="cur_chem_101", title="Module 2: Chemical Thermodynamics", sequence_order=2, subject_id="subj_chem"),
        Module(id="mod_mechanics", curriculum_id="cur_phys_101", title="Module 1: Laws of Motion", sequence_order=1, subject_id="subj_phys"),
        Module(id="mod_calculus", curriculum_id="cur_math_101", title="Module 1: Differential Calculus", sequence_order=1, subject_id="subj_math"),
    ]
    for m in modules_data:
        db.create_module(m)

    # Topics
    topics_data = [
        Topic(id="top_dynamic_eq", module_id="mod_equilibrium", title="Topic 1.1: Dynamic Nature of Equilibrium", sequence_order=1),
        Topic(id="top_le_chatelier", module_id="mod_equilibrium", title="Topic 1.2: Le Chatelier's Principle & Applications", sequence_order=2),
        Topic(id="top_ionic_eq", module_id="mod_equilibrium", title="Topic 1.3: Ionic Equilibrium & Buffer Solutions", sequence_order=3),
        Topic(id="top_thermo_laws", module_id="mod_thermo", title="Topic 2.1: First & Second Laws of Thermodynamics", sequence_order=1),
        Topic(id="top_gibbs", module_id="mod_thermo", title="Topic 2.2: Gibbs Free Energy & Spontaneity", sequence_order=2),
        Topic(id="top_newton_laws", module_id="mod_mechanics", title="Topic 1.1: Newton's Laws of Motion", sequence_order=1),
        Topic(id="top_diff_derivatives", module_id="mod_calculus", title="Topic 1.1: Derivatives & Chain Rule", sequence_order=1),
    ]
    for t in topics_data:
        db.create_topic(t)

    # Concepts
    concepts_data = [
        Concept(
            id="c_equilibrium_const",
            topic_id="top_dynamic_eq",
            name="Equilibrium Constant (Kc and Kp)",
            description="Mathematical formulation and physical interpretation of reaction quotients and equilibrium constants.",
            difficulty=0.4,
        ),
        Concept(
            id="c_le_chatelier",
            topic_id="top_le_chatelier",
            name="Le Chatelier's Principle (Concentration, Pressure, Temperature)",
            description="Qualitative prediction of equilibrium response to external perturbations in closed gaseous and aqueous systems.",
            difficulty=0.6,
        ),
        Concept(
            id="c_haber_process",
            topic_id="top_le_chatelier",
            name="Industrial Haber Process Synthesis",
            description="Optimal temperature, pressure, and catalyst conditions for ammonia synthesis using Le Chatelier's principles.",
            difficulty=0.7,
        ),
        Concept(
            id="c_buffer_solutions",
            topic_id="top_ionic_eq",
            name="Buffer Solutions & Henderson-Hasselbalch Equation",
            description="pH resistance mechanisms in weak acid/conjugate base systems and buffer capacity calculations.",
            difficulty=0.75,
        ),
        Concept(
            id="c_first_law_thermo",
            topic_id="top_thermo_laws",
            name="First Law of Thermodynamics (Internal Energy & Work)",
            description="Conservation of energy applied to closed and open thermodynamic systems (Delta U = q + w).",
            difficulty=0.5,
        ),
        Concept(
            id="c_enthalpy_hess",
            topic_id="top_thermo_laws",
            name="Enthalpy of Reaction & Hess's Law",
            description="State function properties of enthalpy, thermochemical equations, and cyclical reaction paths.",
            difficulty=0.65,
        ),
        Concept(
            id="c_gibbs_spontaneity",
            topic_id="top_gibbs",
            name="Gibbs Free Energy & Reaction Spontaneity",
            description="Delta G = Delta H - T*Delta S criteria for spontaneous physical and chemical transformations.",
            difficulty=0.8,
        ),
        Concept(
            id="c_newton_second_law",
            topic_id="top_newton_laws",
            name="Newton's Second Law & Momentum Conservation",
            description="Force as rate of change of momentum (F = dp/dt) and impulse analysis in collisions.",
            difficulty=0.55,
        ),
        Concept(
            id="c_calculus_chain_rule",
            topic_id="top_diff_derivatives",
            name="Differential Calculus & The Chain Rule",
            description="Differentiation of composite functions: (f o g)'(x) = f'(g(x)) * g'(x).",
            difficulty=0.65,
        ),
    ]
    for c in concepts_data:
        db.create_concept(c)

    # Prerequisites DAG
    prereqs = [
        ("c_equilibrium_const", "c_le_chatelier"),
        ("c_le_chatelier", "c_haber_process"),
        ("c_equilibrium_const", "c_buffer_solutions"),
        ("c_first_law_thermo", "c_enthalpy_hess"),
        ("c_enthalpy_hess", "c_gibbs_spontaneity"),
    ]
    for p_src, p_dst in prereqs:
        db.add_prerequisite(Prerequisite(prerequisite_concept_id=p_src, dependent_concept_id=p_dst))
    print(f"  [OK] Seeded {len(concepts_data)} Concepts with Authoritative Prerequisite DAGs")

    # 5. Seed Class Groups, Cohorts & Enrollments
    class_groups = [
        ClassGroup(id="cls_grade11_a", organization_id="org_dps", course_id="crs_chem_101", name="Grade 11 Section A (Science)", section="A"),
        ClassGroup(id="cls_grade11_b", organization_id="org_dps", course_id="crs_chem_101", name="Grade 11 Section B (Science)", section="B"),
        ClassGroup(id="cls_grade11_phys_a", organization_id="org_dps", course_id="crs_phys_101", name="Grade 11 Physics Batch A", section="A"),
        ClassGroup(id="cls_kv_grade11", organization_id="org_kv", course_id="crs_bio_101", name="KV IIT Grade 11 Bio Batch", section="A"),
    ]
    for cg in class_groups:
        db.create_class_group(cg)

    cohort_a = Cohort(id="coh_2026_a", class_group_id="cls_grade11_a", name="Class 11-A Chemistry (Batch 2026-2027)", academic_year="2026-2027")
    cohort_b = Cohort(id="coh_2026_b", class_group_id="cls_grade11_b", name="Class 11-B Chemistry (Batch 2026-2027)", academic_year="2026-2027")
    cohort_phys = Cohort(id="coh_phys_2026", class_group_id="cls_grade11_phys_a", name="Class 11-A Physics (Batch 2026-2027)", academic_year="2026-2027")
    cohort_kv = Cohort(id="coh_kv_2026", class_group_id="cls_kv_grade11", name="KV IIT Bio Cohort (Batch 2026-2027)", academic_year="2026-2027")

    for coh in [cohort_a, cohort_b, cohort_phys, cohort_kv]:
        db.create_cohort(coh)

    # Student Enrollments
    student_roster_chem_a = [
        "usr_student_arjun",
        "usr_student_priya",
        "usr_student_rahul",
        "usr_student_ananya",
        "usr_student_rohan",
        "usr_student_tanvi",
        "usr_student_aditya",
        "usr_student_sneha",
    ]
    for idx, sid in enumerate(student_roster_chem_a, start=1):
        db.create_enrollment(Enrollment(
            id=f"enr_chem_a_{idx:02d}",
            student_id=sid,
            course_id="crs_chem_101",
            cohort_id="coh_2026_a",
            enrolled_at=now_iso,
            is_active=True,
        ))

    # Cross-enroll in Physics
    for idx, sid in enumerate(student_roster_chem_a[:4], start=1):
        db.create_enrollment(Enrollment(
            id=f"enr_phys_{idx:02d}",
            student_id=sid,
            course_id="crs_phys_101",
            cohort_id="coh_phys_2026",
            enrolled_at=now_iso,
            is_active=True,
        ))

    # KV Bio Enrollments
    db.create_enrollment(Enrollment(id="enr_kv_01", student_id="usr_student_vikram", course_id="crs_bio_101", cohort_id="coh_kv_2026", enrolled_at=now_iso, is_active=True))
    db.create_enrollment(Enrollment(id="enr_kv_02", student_id="usr_student_kavya", course_id="crs_bio_101", cohort_id="coh_kv_2026", enrolled_at=now_iso, is_active=True))
    print(f"  [OK] Seeded Class Groups, Cohorts, and {len(student_roster_chem_a) + 6} Student Enrollments")

    # 6. Seed Tutoring Sessions & Rich Learning Events
    sessions = [
        Session(id="ses_arjun_01", student_id="usr_student_arjun", course_id="crs_chem_101", concept_id="c_le_chatelier", status=SessionStatus.ACTIVE, started_at=now_iso),
        Session(id="ses_priya_01", student_id="usr_student_priya", course_id="crs_chem_101", concept_id="c_gibbs_spontaneity", status=SessionStatus.COMPLETED, started_at=now_iso),
        Session(id="ses_rahul_01", student_id="usr_student_rahul", course_id="crs_chem_101", concept_id="c_first_law_thermo", status=SessionStatus.COMPLETED, started_at=now_iso),
        Session(id="ses_rohan_01", student_id="usr_student_rohan", course_id="crs_chem_101", concept_id="c_equilibrium_const", status=SessionStatus.ACTIVE, started_at=now_iso),
        Session(id="ses_tanvi_01", student_id="usr_student_tanvi", course_id="crs_chem_101", concept_id="c_haber_process", status=SessionStatus.COMPLETED, started_at=now_iso),
    ]
    for ses in sessions:
        db.create_session(ses)

    learning_events = [
        # Arjun Events (Misconception & Guidance)
        LearningEvent(
            id="evt_arjun_01",
            session_id="ses_arjun_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_equilibrium_const",
            event_type="question_answered",
            payload={"question_id": "q_eq_01", "is_correct": True, "score": 1.0, "time_spent_sec": 42},
            score=1.0,
        ),
        LearningEvent(
            id="evt_arjun_02",
            session_id="ses_arjun_01",
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
            session_id="ses_arjun_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_le_chatelier",
            event_type="hint_requested",
            payload={"hint_level": 2, "topic": "Pressure effects on gaseous equilibrium"},
            score=0.5,
        ),
        LearningEvent(
            id="evt_arjun_04",
            session_id="ses_arjun_01",
            student_id="usr_student_arjun",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_first_law_thermo",
            event_type="question_answered",
            payload={"question_id": "q_thermo_01", "is_correct": False, "score": 0.0, "time_spent_sec": 55},
            score=0.0,
        ),
        # Priya Events (Advanced Mastery)
        LearningEvent(
            id="evt_priya_01",
            session_id="ses_priya_01",
            student_id="usr_student_priya",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_haber_process",
            event_type="question_answered",
            payload={"question_id": "q_haber_01", "is_correct": True, "score": 1.0, "time_spent_sec": 24},
            score=1.0,
        ),
        LearningEvent(
            id="evt_priya_02",
            session_id="ses_priya_01",
            student_id="usr_student_priya",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_gibbs_spontaneity",
            event_type="question_answered",
            payload={"question_id": "q_gibbs_01", "is_correct": True, "score": 1.0, "time_spent_sec": 31},
            score=1.0,
        ),
        LearningEvent(
            id="evt_priya_03",
            session_id="ses_priya_01",
            student_id="usr_student_priya",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_buffer_solutions",
            event_type="question_answered",
            payload={"question_id": "q_buf_01", "is_correct": True, "score": 1.0, "time_spent_sec": 29},
            score=1.0,
        ),
        # Rohan Events (At-Risk / Consecutive Misconceptions)
        LearningEvent(
            id="evt_rohan_01",
            session_id="ses_rohan_01",
            student_id="usr_student_rohan",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_enthalpy_hess",
            event_type="misconception_triggered",
            payload={
                "misconception_code": "THERMO_SIGN_CONVENTION",
                "diagnosis": "Student confused sign convention for work done ON the system versus BY the system.",
                "remediation_hint": "IUPAC convention: w is positive when work is done ON the system (compression).",
            },
            score=0.0,
        ),
        # Rahul Events
        LearningEvent(
            id="evt_rahul_01",
            session_id="ses_rahul_01",
            student_id="usr_student_rahul",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_first_law_thermo",
            event_type="question_answered",
            payload={"question_id": "q_thermo_01", "is_correct": True, "score": 1.0, "time_spent_sec": 38},
            score=1.0,
        ),
        # Tanvi Events
        LearningEvent(
            id="evt_tanvi_01",
            session_id="ses_tanvi_01",
            student_id="usr_student_tanvi",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_le_chatelier",
            event_type="question_answered",
            payload={"question_id": "q_le_01", "is_correct": True, "score": 1.0, "time_spent_sec": 33},
            score=1.0,
        ),
    ]
    for ev in learning_events:
        db.record_learning_event(ev)
    print(f"  [OK] Seeded {len(learning_events)} High-Fidelity Learning Events & Diagnostic Telemetry")

    # 7. Seed Teacher AI Instructions & Intervention Alerts
    instructions = [
        TeacherInstructionRecord(
            id="inst_sharma_01",
            teacher_id="usr_teacher_sharma",
            student_id="all",
            course_id="crs_chem_101",
            instruction_text="Emphasize the difference between reaction rates and equilibrium concentrations. Guide students socratically when they confuse stoichiometric coefficients with equilibrium powers.",
            priority=1,
            is_active=True,
        ),
        TeacherInstructionRecord(
            id="inst_sharma_02",
            teacher_id="usr_teacher_sharma",
            student_id="usr_student_arjun",
            course_id="crs_chem_101",
            instruction_text="Provide step-by-step scaffolding for pressure shift calculations without giving the numerical answer directly.",
            priority=2,
            is_active=True,
        ),
        TeacherInstructionRecord(
            id="inst_verma_01",
            teacher_id="usr_teacher_verma",
            student_id="all",
            course_id="crs_phys_101",
            instruction_text="Require students to state Newton's Third Law action-reaction pairs explicitly before solving free-body diagram equations.",
            priority=1,
            is_active=True,
        ),
        TeacherInstructionRecord(
            id="inst_sundaram_01",
            teacher_id="usr_teacher_sundaram",
            student_id="all",
            course_id="crs_math_101",
            instruction_text="Enforce step-by-step differentiation breakdown when applying chain rule to trigonometric and exponential composite functions.",
            priority=1,
            is_active=True,
        ),
    ]
    for inst in instructions:
        db.create_teacher_instruction(inst)

    alerts = [
        InterventionRecord(
            id="alt_arjun_le_chatelier",
            student_id="usr_student_arjun",
            course_id="crs_chem_101",
            severity=AlertSeverity.CRITICAL,
            alert_type="misconception_repetition",
            message="Arjun Patel has triggered the Equilibrium Concentration Equality misconception twice. Recommend targeted micro-intervention on dynamic reaction rates.",
            status=AlertStatus.ACTIVE,
            assigned_teacher="usr_teacher_sharma",
        ),
        InterventionRecord(
            id="alt_rohan_thermo_signs",
            student_id="usr_student_rohan",
            course_id="crs_chem_101",
            severity=AlertSeverity.WARNING,
            alert_type="misconception_repetition",
            message="Rohan Gupta showed repeated sign errors in thermodynamic work calculations (Delta U = q + w).",
            status=AlertStatus.ACTIVE,
            assigned_teacher="usr_teacher_sharma",
        ),
        InterventionRecord(
            id="alt_ananya_review_due",
            student_id="usr_student_ananya",
            course_id="crs_chem_101",
            severity=AlertSeverity.INFO,
            alert_type="spaced_review_due",
            message="Ananya Verma has 3 spaced review items due for Chemical Equilibrium Module 1.",
            status=AlertStatus.ACTIVE,
            assigned_teacher="usr_teacher_sharma",
        ),
    ]
    for alt in alerts:
        db.create_intervention(alt)
    print(f"  [OK] Seeded {len(instructions)} Pedagogical Directives & {len(alerts)} Active Teacher Alerts")

    # 8. Seed AI Backend Providers & Models (SLM GGUF as Default Priority 1)
    providers = [
        AIProvider(
            id="prov-local",
            name="Local SLM Engine (llama.cpp / Ollama)",
            provider_type="local",
            base_url="http://127.0.0.1:11434/v1",
            is_active=True,
        ),
        AIProvider(
            id="prov-vllm",
            name="vLLM High-Throughput Cluster",
            provider_type="vllm",
            base_url="http://127.0.0.1:8000/v1",
            is_active=True,
        ),
        AIProvider(
            id="prov-openai",
            name="OpenAI Gateway (GPT-4o)",
            provider_type="openai",
            base_url="https://api.openai.com/v1",
            is_active=True,
        ),
        AIProvider(
            id="prov-anthropic",
            name="Anthropic Claude API",
            provider_type="anthropic",
            base_url="https://api.anthropic.com/v1",
            is_active=True,
        ),
    ]
    for p in providers:
        db.create_ai_provider(p)

    models = [
        AIModel(
            id="Gayatri-Tutor-v3-Q4_K_M",
            provider_id="prov-local",
            model_name="Gayatri-Tutor-v3-Q4_K_M",
            context_window=8192,
            is_default=True,  # Default SLM GGUF
        ),
        AIModel(
            id="Gayatri-Tutor-SLM-Q4_K_M",
            provider_id="prov-local",
            model_name="Gayatri-Tutor-SLM-Q4_K_M",
            context_window=8192,
            is_default=False,
        ),
        AIModel(
            id="Qwen2.5-3B-Instruct-Q4_K_M",
            provider_id="prov-local",
            model_name="Qwen2.5-3B-Instruct-Q4_K_M",
            context_window=8192,
            is_default=False,
        ),
        AIModel(
            id="Llama-3.2-3B-Instruct-Q4_K_M",
            provider_id="prov-local",
            model_name="Llama-3.2-3B-Instruct-Q4_K_M",
            context_window=8192,
            is_default=False,
        ),
        AIModel(
            id="gpt-4o",
            provider_id="prov-openai",
            model_name="gpt-4o",
            context_window=128000,
            is_default=False,
        ),
        AIModel(
            id="claude-3-5-sonnet",
            provider_id="prov-anthropic",
            model_name="claude-3-5-sonnet",
            context_window=200000,
            is_default=False,
        ),
    ]
    for m in models:
        db.create_ai_model(m)
    print(f"  [OK] Seeded {len(providers)} AI Providers & {len(models)} Registered Models (Gayatri-Tutor-v3 SLM Default)")

    # 9. Seed Authoritative Audit Trail Events
    audit_events = [
        AuditLog(
            id="aud_001",
            organization_id="org_global",
            user_id="usr_superadmin",
            action="CREATE_ORGANIZATION",
            resource="Organization:org_dps",
            details={"name": "Delhi Public School (R.K. Puram)", "tier": "ENTERPRISE", "quota": 500},
        ),
        AuditLog(
            id="aud_002",
            organization_id="org_dps",
            user_id="usr_superadmin",
            action="PUBLISH_CURRICULUM",
            resource="Curriculum:cur_chem_101",
            details={"version": "1.0.0", "concepts_count": 9, "status": "approved"},
        ),
        AuditLog(
            id="aud_003",
            organization_id="org_global",
            user_id="usr_superadmin",
            action="UPDATE_AI_POLICY",
            resource="Policy:ai_governance",
            details={"policy_level": "strict", "anti_answer_leakage": True, "max_tokens_per_turn": 1024},
        ),
        AuditLog(
            id="aud_004",
            organization_id="org_dps",
            user_id="usr_dps_admin",
            action="PROVISION_USER",
            resource="User:usr_teacher_sharma",
            details={"role": "TEACHER", "assigned_course": "crs_chem_101"},
        ),
        AuditLog(
            id="aud_005",
            organization_id="org_dps",
            user_id="usr_teacher_sharma",
            action="DISPATCH_TEACHER_DIRECTIVE",
            resource="Instruction:inst_sharma_01",
            details={"scope": "crs_chem_101", "priority": 1},
        ),
    ]
    for aud in audit_events:
        db.record_audit_log(aud)
    print(f"  [OK] Seeded {len(audit_events)} Immutable Audit Trail Events")

    # 10. Save local tokens to JSON file for immediate reference
    token_file = PROJECT_ROOT / "local_auth_tokens.json"
    token_file.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"\n[KEY] Generated Test Auth Tokens written to: {token_file.name}")

    print("\n[SUCCESS] Comprehensive Multi-Domain Seeding Complete! Ready for Demo Recording.\n")
    return tokens


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "gayatri_local.db"
    seed_local_environment(db_file)
