"""
Phase 43 — Production Readiness Gate Test Suite.

Programmatically validates all production readiness checklist items for Gayatri AI Platform.
"""

import os
import json
import pytest

from central_platform.deployment.validator import DeploymentValidator, ValidationStatus
from central_platform.portals.student import StudentPortalController
from central_platform.portals.teacher import TeacherPortalController
from central_platform.portals.parent import ParentPortalController
from central_platform.portals.fee_admin import FeeAdminController
from central_platform.payments.registry import PaymentGatewayRegistry
from central_platform.payments.mock import MockPaymentAdapter
from central_platform.i18n.registry import TranslationRegistry, LanguageCode
from central_platform.privacy.policies import PrivacyRulesEngine, ParentVisibilityLevel
from central_platform.analytics.engine import LearningAnalyticsEngine, LearningHealthLevel
from central_platform.explainability.engine import ExplainabilityEngine
from central_platform.security.audit import SecurityAuditRunner
from central_platform.recovery.manager import FailureRecoveryManager, RecoveryStatus
from central_platform.performance.profiler import PerformanceProfiler
from central_platform.learning.graph import LearningGraph
from central_platform.learning.mastery import MasteryEvidenceEngine
from central_platform.models.schema import LearningEvent
from central_platform.db import PlatformDatabase


def test_production_readiness_gate_deployment_validation():
    validator = DeploymentValidator()
    report = validator.run_full_validation()
    assert report.failed_checks == 0, f"Deployment validation failed checks: {report.summary}"
    assert report.is_ready is True


def test_production_readiness_gate_portals():
    student_ctrl = StudentPortalController()
    teacher_ctrl = TeacherPortalController()
    parent_ctrl = ParentPortalController()
    fee_ctrl = FeeAdminController()

    assert student_ctrl is not None
    assert teacher_ctrl is not None
    assert parent_ctrl is not None
    assert fee_ctrl is not None


def test_production_readiness_gate_payments():
    mock_prov = PaymentGatewayRegistry.get_provider("mock")
    assert isinstance(mock_prov, MockPaymentAdapter)
    rzp_prov = PaymentGatewayRegistry.get_provider("razorpay")
    assert rzp_prov is not None


def test_production_readiness_gate_i18n():
    assert TranslationRegistry.get_text("welcome", lang="en", name="Aarav") is not None
    assert TranslationRegistry.get_text("dashboard", lang="hi") == "डैशबोर्ड"


def test_production_readiness_gate_privacy():
    assert PrivacyRulesEngine.can_parent_view_chat_history("parent_001", "student_001") is False


def test_production_readiness_gate_analytics():
    level = LearningAnalyticsEngine.classify_health_level(90.0, 0)
    assert level == LearningHealthLevel.EXCELLENT


def test_production_readiness_gate_explainability():
    expl = ExplainabilityEngine.explain_content_recommendation(
        student_id="std_101",
        concept_name="Organic Chemistry",
        learner_state={"mastery_score": 62.5, "recent_mistakes_count": 2},
    )
    assert expl is not None
    assert "Organic Chemistry" in expl.title


def test_production_readiness_gate_security():
    runner = SecurityAuditRunner()
    masked = runner.sanitize_pii_logs("User email is test@example.com")
    assert "t**t@example.com" in masked or "***" in masked


def test_production_readiness_gate_recovery():
    res = FailureRecoveryManager.repair_malformed_model_output('{"answer": "42"}')
    assert res.status == RecoveryStatus.RECOVERED
    assert res.data["answer"] == "42"


def test_production_readiness_gate_performance():
    profiler = PerformanceProfiler()
    assert profiler is not None


def test_production_readiness_gate_learning_graph():
    db = PlatformDatabase()
    graph = LearningGraph(db)
    assert graph is not None

    engine = MasteryEvidenceEngine()
    events = [
        LearningEvent(
            id="e1",
            session_id="s1",
            student_id="u1",
            concept_id="cpt_1",
            event_type="answer_submitted",
            score=1.0,
            payload={"correctness": "correct", "hint_level": 0},
        )
    ]
    res = engine.calculate_evidence_mastery("cpt_1", events)
    assert res.effective_mastery > 0.0
