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
    org_global = Organization(id="org_global", name="Gayatri Central Network", slug="gayatri-central")
    org_dps = Organization(id="org_dps", name="Delhi Public School (R.K. Puram)", slug="dps-rkp")
    org_kv = Organization(id="org_kv", name="Kendriya Vidyalaya (IIT Campus)", slug="kv-iit")
    org_mumbai = Organization(id="org_mumbai", name="Mumbai Institute of Science", slug="mis-mumbai")

    for org in [org_global, org_dps, org_kv, org_mumbai]:
        db.create_organization(org)
    print("  [OK] Seeded 4 Educational Organizations (Global Network, DPS, KV, Mumbai Science)")

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
            "id": "usr_teacher_verma",
            "email": "teacher.verma@dps.edu",
            "name": "Dr. Rajesh Verma (Physics Faculty)",
            "role": UserRole.TEACHER,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_arjun",
            "email": "student.arjun@dps.edu",
            "name": "Arjun Patel (Grade 11 Student - Focus Persona)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_priya",
            "email": "student.priya@dps.edu",
            "name": "Priya Sen (Grade 11 Student - Advanced Persona)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_rahul",
            "email": "student.rahul@dps.edu",
            "name": "Rahul Sharma (Grade 11 Student)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_ananya",
            "email": "student.ananya@dps.edu",
            "name": "Ananya Verma (Grade 11 Student)",
            "role": UserRole.STUDENT,
            "org_id": "org_dps",
        },
        {
            "id": "usr_student_rohan",
            "email": "student.rohan@dps.edu",
            "name": "Rohan Gupta (Grade 11 Student - Needs Support)",
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
    print(f"  [OK] Seeded {len(users_data)} Multi-Tiered Users (Super Admin, Org Admins, Teachers, Students)")

    # 3. Seed Courses & Subjects
    c1 = Course(
        id="crs_chem_101",
        organization_id="org_dps",
        code="CHEM-101",
        title="Class 11 Chemistry - Equilibrium & Thermodynamics",
        description="Core foundational chemistry covering dynamic chemical equilibrium, Le Chatelier's principle, and thermodynamics.",
    )
    c2 = Course(
        id="crs_phys_101",
        organization_id="org_dps",
        code="PHYS-101",
        title="Class 11 Physics - Mechanics & Waves",
        description="Comprehensive Newtonian mechanics, work-energy theorem, and rotational dynamics.",
    )
    db.create_course(c1)
    db.create_course(c2)

    subj_chem = Subject(
        id="subj_chem",
        course_id="crs_chem_101",
        name="Physical Chemistry",
        code="PHYS_CHEM",
    )
    subj_phys = Subject(
        id="subj_phys",
        course_id="crs_phys_101",
        name="Classical Mechanics",
        code="CLASS_MECH",
    )
    db.create_subject(subj_chem)
    db.create_subject(subj_phys)
    print("  [OK] Seeded 2 Courses (Chemistry-101, Physics-101) and Respective Subjects")

    # 4. Seed Published Curriculum DAG with Multiple Modules & Concepts
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
        change_log="Initial official published release for academic year 2026-2027",
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
        title="Module 2: Chemical Thermodynamics",
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
    top_thermo_laws = Topic(
        id="top_thermo_laws",
        module_id="mod_thermo",
        title="Topic 2.1: First & Second Laws of Thermodynamics",
        sequence_order=1,
    )
    top_gibbs = Topic(
        id="top_gibbs",
        module_id="mod_thermo",
        title="Topic 2.2: Gibbs Free Energy & Spontaneity",
        sequence_order=2,
    )
    db.create_topic(top_dyn)
    db.create_topic(top_le_chat)
    db.create_topic(top_thermo_laws)
    db.create_topic(top_gibbs)

    # Concepts
    concepts = [
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
    ]
    for c in concepts:
        db.create_concept(c)

    # Prerequisites DAG
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_equilibrium_const", dependent_concept_id="c_le_chatelier"))
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_le_chatelier", dependent_concept_id="c_haber_process"))
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_first_law_thermo", dependent_concept_id="c_enthalpy_hess"))
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_enthalpy_hess", dependent_concept_id="c_gibbs_spontaneity"))
    print("  [OK] Seeded 6 Chemistry Concepts with Comprehensive Prerequisite DAG")

    # 5. Seed Class Groups, Cohorts & Enrollments
    class_group_a = ClassGroup(
        id="cls_grade11_a",
        organization_id="org_dps",
        course_id="crs_chem_101",
        name="Grade 11 Section A (Science)",
        section="A",
    )
    db.create_class_group(class_group_a)

    cohort_a = Cohort(
        id="coh_2026_a",
        class_group_id="cls_grade11_a",
        name="Class 11-A Chemistry (Batch 2026-2027)",
        academic_year="2026-2027",
    )
    db.create_cohort(cohort_a)

    enrolled_students = [
        "usr_student_arjun",
        "usr_student_priya",
        "usr_student_rahul",
        "usr_student_ananya",
        "usr_student_rohan",
    ]
    for idx, sid in enumerate(enrolled_students, start=1):
        enr = Enrollment(
            id=f"enr_chem_{idx:02d}",
            student_id=sid,
            course_id="crs_chem_101",
            cohort_id="coh_2026_a",
            enrolled_at=now_iso,
            is_active=True,
        )
        db.create_enrollment(enr)
    print(f"  [OK] Enrolled {len(enrolled_students)} Students into Class 11-A Cohort")

    # 6. Seed Tutoring Sessions & Learning Events across Students
    # Arjun Patel (At-Risk / Demonstrates Misconception Handling & Remediation)
    sess_arjun = Session(
        id="ses_arjun_chem_01",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        concept_id="c_le_chatelier",
        status=SessionStatus.ACTIVE,
        started_at=now_iso,
    )
    db.create_session(sess_arjun)

    # Priya Sen (Advanced / High Mastery)
    sess_priya = Session(
        id="ses_priya_chem_01",
        student_id="usr_student_priya",
        course_id="crs_chem_101",
        concept_id="c_gibbs_spontaneity",
        status=SessionStatus.COMPLETED,
        started_at=now_iso,
    )
    db.create_session(sess_priya)

    # Rahul Sharma
    sess_rahul = Session(
        id="ses_rahul_chem_01",
        student_id="usr_student_rahul",
        course_id="crs_chem_101",
        concept_id="c_first_law_thermo",
        status=SessionStatus.COMPLETED,
        started_at=now_iso,
    )
    db.create_session(sess_rahul)

    # Learning Events
    events = [
        # Arjun Events
        LearningEvent(
            id="evt_arjun_01",
            session_id="ses_arjun_chem_01",
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
        # Priya Events (Mastery across hard concepts)
        LearningEvent(
            id="evt_priya_01",
            session_id="ses_priya_chem_01",
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
            session_id="ses_priya_chem_01",
            student_id="usr_student_priya",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_gibbs_spontaneity",
            event_type="question_answered",
            payload={"question_id": "q_gibbs_01", "is_correct": True, "score": 1.0, "time_spent_sec": 31},
            score=1.0,
        ),
        # Rahul Events
        LearningEvent(
            id="evt_rahul_01",
            session_id="ses_rahul_chem_01",
            student_id="usr_student_rahul",
            organization_id="org_dps",
            course_id="crs_chem_101",
            concept_id="c_first_law_thermo",
            event_type="question_answered",
            payload={"question_id": "q_thermo_01", "is_correct": True, "score": 1.0, "time_spent_sec": 38},
            score=1.0,
        ),
    ]

    for ev in events:
        db.record_learning_event(ev)
    print("  [OK] Seeded Multi-Student Learning Events & Misconception Diagnostics")

    # 7. Seed Teacher AI Instructions & Active Intervention Alerts
    instruction_1 = TeacherInstructionRecord(
        id="inst_sharma_01",
        teacher_id="usr_teacher_sharma",
        student_id="all",
        course_id="crs_chem_101",
        instruction_text="Emphasize the difference between reaction rates and equilibrium concentrations. Guide students socratically when they confuse stoichiometric coefficients with equilibrium powers.",
        priority=1,
        is_active=True,
    )
    instruction_2 = TeacherInstructionRecord(
        id="inst_sharma_02",
        teacher_id="usr_teacher_sharma",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        instruction_text="Provide step-by-step scaffolding for pressure shift calculations without giving the numerical answer directly.",
        priority=2,
        is_active=True,
    )
    db.create_teacher_instruction(instruction_1)
    db.create_teacher_instruction(instruction_2)

    alert_1 = InterventionRecord(
        id="alt_arjun_le_chatelier",
        student_id="usr_student_arjun",
        course_id="crs_chem_101",
        severity=AlertSeverity.CRITICAL,
        alert_type="misconception_repetition",
        message="Arjun Patel has triggered the Equilibrium Concentration Equality misconception twice. Recommend targeted micro-intervention on dynamic reaction rates.",
        status=AlertStatus.ACTIVE,
        assigned_teacher="usr_teacher_sharma",
    )
    alert_2 = InterventionRecord(
        id="alt_rohan_stoichiometry",
        student_id="usr_student_rohan",
        course_id="crs_chem_101",
        severity=AlertSeverity.WARNING,
        alert_type="streak_drop",
        message="Rohan Gupta showed consecutive errors in mole ratio conversions during chemical equilibrium problem sets.",
        status=AlertStatus.ACTIVE,
        assigned_teacher="usr_teacher_sharma",
    )
    db.create_intervention(alert_1)
    db.create_intervention(alert_2)
    print("  [OK] Seeded 2 Active Teacher Directives & 2 Priority Intervention Alerts")

    # 8. Seed AI Providers & Models
    p_local = AIProvider(
        id="prov-local",
        name="Local Inference Engine (llama.cpp / Ollama)",
        provider_type="local",
        base_url="http://127.0.0.1:11434/v1",
        is_active=True,
    )
    p_openai = AIProvider(
        id="prov-openai",
        name="OpenAI Gateway (GPT-4o)",
        provider_type="openai",
        base_url="https://api.openai.com/v1",
        is_active=True,
    )
    p_anthropic = AIProvider(
        id="prov-anthropic",
        name="Anthropic Claude API",
        provider_type="anthropic",
        base_url="https://api.anthropic.com/v1",
        is_active=True,
    )
    for p in [p_local, p_openai, p_anthropic]:
        db.create_ai_provider(p)

    m1 = AIModel(
        id="gguf-llama3-8b",
        provider_id="prov-local",
        model_name="gguf-llama3-8b",
        context_window=8192,
        is_default=True,
    )
    m2 = AIModel(
        id="slm-chemistry-v1",
        provider_id="prov-local",
        model_name="slm-chemistry-v1",
        context_window=4096,
        is_default=False,
    )
    m3 = AIModel(
        id="gpt-4o",
        provider_id="prov-openai",
        model_name="gpt-4o",
        context_window=128000,
        is_default=False,
    )
    for m in [m1, m2, m3]:
        db.create_ai_model(m)
    print("  [OK] Seeded 3 AI Backend Providers and 3 Registered AI Models")

    # 9. Seed Audit Trail Logs
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
            details={"version": "1.0.0", "concepts_count": 6},
        ),
        AuditLog(
            id="aud_003",
            organization_id="org_global",
            user_id="usr_superadmin",
            action="UPDATE_AI_POLICY",
            resource="Policy:ai_governance",
            details={"policy_level": "strict", "anti_answer_leakage": True},
        ),
    ]
    for aud in audit_events:
        db.record_audit_log(aud)
    print("  [OK] Seeded Authoritative Audit Trail Events")

    # 10. Save local tokens to JSON file for immediate reference
    token_file = PROJECT_ROOT / "local_auth_tokens.json"
    token_file.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"\n[KEY] Generated Test Auth Tokens written to: {token_file.name}")

    print("\n[SUCCESS] Local Environment Seeding Complete! Ready for Testing & Demo Video.\n")
    return tokens


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "gayatri_local.db"
    seed_local_environment(db_file)
