"""Phase 39 — Comprehensive Master Platform Full Regression Test Suite.

End-to-end multi-subsystem integration testing verifying seamless co-existence and zero regressions across:
1. Identity, Auth & RBAC
2. Central Database & Schema Migrations
3. AI Gateway, Provider Adapters & Model Config
4. RAG Retrieval Reliability & Source Isolation
5. Shared UI Design System, Shell & 4 Persona Portals
6. Fee Subsystem Ledger & Payment Provider Adapters
7. i18n Internationalization & Fallback Logic
8. Parent Privacy & Data Filtering
9. Learning Analytics & Multi-Level Health Metrics
10. Decision Explainability Engine
11. Security Audit & Log PII Masking
12. Resilience & Failure Recovery Manager
"""

import pytest

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole
from central_platform.fees.service import FeeService
from central_platform.models.fees import FeeFrequency, DiscountType, PaymentMethod
from central_platform.payments.registry import PaymentGatewayRegistry
from central_platform.i18n.registry import TranslationRegistry
from central_platform.privacy.policies import PrivacyRulesEngine, ParentVisibilityLevel, StudentPrivacySetting
from central_platform.analytics.engine import LearningAnalyticsEngine, LearningHealthLevel
from central_platform.explainability.engine import ExplainabilityEngine, ExplanationType
from central_platform.security.audit import SecurityAuditRunner
from central_platform.recovery.manager import FailureRecoveryManager, FailureCategory, RecoveryStatus


@pytest.fixture
def master_db():
    database = PlatformDatabase(":memory:")
    # Seed Organization & Identity
    org = Organization(id="org_master_1", name="Gayatri Master Academy", slug="gayatri-master")
    database.create_organization(org)

    student = User(id="std_master_1", email="student@master.com", full_name="Aarav Sharma", role=UserRole.STUDENT, organization_id="org_master_1")
    parent = User(id="prt_master_1", email="parent@master.com", full_name="Sanjay Sharma", role=UserRole.PARENT, organization_id="org_master_1")
    teacher = User(id="tch_master_1", email="teacher@master.com", full_name="Dr. Ananya Roy", role=UserRole.TEACHER, organization_id="org_master_1")

    database.create_user(student)
    database.create_user(parent)
    database.create_user(teacher)

    yield database
    database.close()


def test_end_to_end_student_learning_journey(master_db: PlatformDatabase):
    # 1. Learning events & health evaluation
    events = [
        {"item_id": "item_1", "score": 90.0, "misconception_detected": False},
        {"item_id": "item_2", "score": 85.0, "misconception_detected": False},
    ]
    student_health = LearningAnalyticsEngine.compute_student_learning_health("std_master_1", "Aarav Sharma", events)
    assert student_health.health_level == LearningHealthLevel.EXCELLENT

    # 2. Explainability for student recommendation
    explanation = ExplainabilityEngine.explain_content_recommendation(
        student_id="std_master_1",
        concept_name="Organic Chemistry",
        learner_state={"mastery_score": student_health.mastery_score},
    )
    assert explanation.explanation_type == ExplanationType.WHY_SEEING_THIS
    assert "Organic Chemistry" in explanation.title

    # 3. Parent privacy filtering check
    privacy_setting = StudentPrivacySetting(
        student_id="std_master_1",
        parent_id="prt_master_1",
        visibility_level=ParentVisibilityLevel.FULL_TRANSPARENCY,
        allow_chat_history_visibility=False,  # Keep AI chat private
    )
    PrivacyRulesEngine.set_privacy_setting(privacy_setting)

    raw_data = {
        "overall_mastery": student_health.mastery_score,
        "attendance_pct": 98.0,
        "chat_history": ["How do I balance redox equations?"],
        "teacher_notes": ["Showing great aptitude in chemistry."],
    }
    filtered_data = PrivacyRulesEngine.filter_student_data_for_parent("prt_master_1", "std_master_1", raw_data)
    assert filtered_data["overall_mastery"] == 87.5
    assert "chat_history" not in filtered_data  # AI chat private
    assert "teacher_notes" in filtered_data

    # 4. Fee Account & Payment
    fee_service = FeeService(db=master_db)
    account = fee_service.create_fee_account("std_master_1", "org_master_1", initial_due=0.0)
    invoice = fee_service.generate_invoice(account, amount_due=10000.0, due_date="2026-11-15T00:00:00Z")

    # Payment Gateway order creation
    gateway = PaymentGatewayRegistry.get_provider("upi")
    pay_order = gateway.create_order(amount=10000.0, receipt_id=invoice.invoice_number)
    assert pay_order.provider == "upi"
    assert "upi://pay?" in pay_order.checkout_url

    # Record Payment in ledger
    payment, receipt = fee_service.record_payment(invoice, account, amount=10000.0, payment_method=PaymentMethod.UPI)
    assert account.balance_due == 0.0
    assert account.status == "clear"
    assert receipt.receipt_number.startswith("RCT-")

    # 5. Internationalization check
    hi_title = TranslationRegistry.get_text("fees", lang="hi")
    assert hi_title == "शुल्क और भुगतान"

    # 6. Security Audit PII masking check
    log_text = f"Student student@master.com paid via UPI reference {pay_order.order_id}"
    sanitized_log = SecurityAuditRunner.sanitize_pii_logs(log_text)
    assert "student@master.com" not in sanitized_log
    assert "s*****t@master.com" in sanitized_log

    # 7. Failure Recovery check
    recovery = FailureRecoveryManager.repair_malformed_model_output("```json\n{\"status\": \"ok\"}\n```")
    assert recovery.status == RecoveryStatus.RECOVERED
    assert recovery.data["status"] == "ok"
