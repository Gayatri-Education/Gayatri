"""Phase 04 — AI Gateway and Model Failure Semantics Remediation Tests.

Verifies:
1. Provider execution states:
   - MODEL_SUCCESS
   - MODEL_UNAVAILABLE
   - MODEL_TIMEOUT
   - MODEL_RATE_LIMITED
   - MODEL_CONFIGURATION_ERROR
   - MODEL_INVALID_RESPONSE
2. Elimination of automatic fallback to mock_engine (F-011).
3. Elimination of synthetic mock completions on provider failures (F-012).
4. Tutor fail-closed semantics on AI model failure (F-013):
   - Zero fabricated successful AI turns.
   - Zero mastery advancement on model failure.
   - Zero state changes committed on model failure.
   - Structured error details and service unavailable messaging.
5. Machine-readable provenance records ({provider, model, mock: false}) (F-014).
6. Production gate prohibiting mock adapters when GAYATRI_ENV=production.
"""
from __future__ import annotations

import json
import socket
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from central_platform.ai.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    MockAIAdapter,
    OpenAIAdapter,
)
from central_platform.ai.gateway import AIGatewayService
from central_platform.ai.schema import (
    AIExecutionRequest,
    AIExecutionResult,
    AIModelDescriptor,
    ModelExecutionStatus,
    ModelTier,
    ProviderConfig,
    ProviderType,
    TaskType,
)
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
from central_platform.tutor.orchestrator import GenericTutorOrchestrator, TutorTurnRequest


@pytest.fixture
def mem_db():
    db = PlatformDatabase(":memory:")
    db.create_organization(
        Organization(id="org-core", name="Core Academic Institution", slug="core-academic")
    )
    user = User(
        id="std-04-101",
        organization_id="org-core",
        email="student@test.com",
        full_name="Test Student",
        role=UserRole.STUDENT,
    )
    db.create_user(user)

    course = Course(
        id="crs-physics-101",
        organization_id="org-core",
        code="PHYS101",
        title="Classical Mechanics",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)

    version = CourseVersion(
        id="ver-crs-physics-101-v1",
        course_id="crs-physics-101",
        version_number="1.0",
        status=CourseStatus.PUBLISHED,
        created_by="teacher-1",
    )
    db.create_course_version(version)

    enrollment = Enrollment(
        id="enr-04-101",
        student_id="std-04-101",
        course_id="crs-physics-101",
        is_active=True,
    )
    db.create_enrollment(enrollment)

    return db



@pytest.fixture
def openai_model_desc():
    return AIModelDescriptor(
        model_id="gpt-4o",
        model_name="gpt-4o",
        tier=ModelTier.TIER_1_HEAVY,
        cost_per_1k_input_usd=0.005,
        cost_per_1k_output_usd=0.015,
    )


# ── 1. Real Provider Success Contract ──────────────────────────────────────

def test_provider_success_contract(openai_model_desc, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-valid-key")
    cfg = ProviderConfig(
        provider_name="test_openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="TEST_OPENAI_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": "Newton's first law explains inertia."}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30},
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        req = AIExecutionRequest(prompt="Explain Newton's first law", task_type=TaskType.TUTORING)
        res = adapter.execute(req, openai_model_desc)

    assert res.success is True
    assert res.status == ModelExecutionStatus.MODEL_SUCCESS
    assert res.mock is False
    assert res.provider == "test_openai"
    assert res.model == "gpt-4o"
    assert "inertia" in res.content
    assert res.prompt_tokens == 12
    assert res.completion_tokens == 18
    assert res.provenance == {
        "provider": "test_openai",
        "model": "gpt-4o",
        "mock": False,
        "status": "MODEL_SUCCESS",
    }


# ── 2. Provider Error States (Timeout, 500, 429, Invalid Response) ────────

def test_provider_timeout_contract(openai_model_desc, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-valid-key")
    cfg = ProviderConfig(
        provider_name="test_openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="TEST_OPENAI_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    with patch("urllib.request.urlopen", side_effect=socket.timeout("Connection timed out")):
        req = AIExecutionRequest(prompt="Calculate velocity", task_type=TaskType.TUTORING)
        res = adapter.execute(req, openai_model_desc)

    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_TIMEOUT
    assert res.mock is False
    assert res.content == ""
    assert res.error_class == "TimeoutError"


def test_provider_http_500_unavailable_contract(openai_model_desc, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-valid-key")
    cfg = ProviderConfig(
        provider_name="test_openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="TEST_OPENAI_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    err_500 = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=err_500):
        req = AIExecutionRequest(prompt="Define acceleration", task_type=TaskType.TUTORING)
        res = adapter.execute(req, openai_model_desc)

    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_UNAVAILABLE
    assert res.mock is False
    assert res.content == ""
    assert res.error_class == "HTTP_500"


def test_provider_rate_limited_contract(openai_model_desc, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-valid-key")
    cfg = ProviderConfig(
        provider_name="test_openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="TEST_OPENAI_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    err_429 = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=err_429):
        req = AIExecutionRequest(prompt="Explain momentum", task_type=TaskType.TUTORING)
        res = adapter.execute(req, openai_model_desc)

    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_RATE_LIMITED
    assert res.mock is False
    assert res.content == ""
    assert res.error_class == "HTTP_429"


def test_provider_invalid_json_contract(openai_model_desc, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-valid-key")
    cfg = ProviderConfig(
        provider_name="test_openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="TEST_OPENAI_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<!DOCTYPE html><html><body>502 Bad Gateway</body></html>"
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        req = AIExecutionRequest(prompt="Explain friction", task_type=TaskType.TUTORING)
        res = adapter.execute(req, openai_model_desc)

    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_INVALID_RESPONSE
    assert res.mock is False
    assert res.content == ""


def test_missing_credentials_fails_closed(openai_model_desc, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = ProviderConfig(
        provider_name="openai",
        provider_type=ProviderType.OPENAI,
        api_key_ref="OPENAI_API_KEY",
        models=[openai_model_desc],
    )
    adapter = OpenAIAdapter(cfg)

    req = AIExecutionRequest(prompt="Explain work", task_type=TaskType.TUTORING)
    res = adapter.execute(req, openai_model_desc)

    # Must fail closed: never convert missing key to mock response (F-012)
    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_CONFIGURATION_ERROR
    assert res.error_class == "MissingAPIKeyError"
    assert res.mock is False
    assert res.content == ""


# ── 3. Production Mock Rejection (F-011, F-012) ────────────────────────────

def test_production_mode_rejects_mock_provider_registration(monkeypatch):
    monkeypatch.setenv("GAYATRI_ENV", "production")
    gateway = AIGatewayService(db=PlatformDatabase(":memory:"))

    # In production, mock_engine is NOT registered by default
    assert "mock_engine" not in gateway.adapters

    # Attempting to register a mock provider in production raises ValueError
    mock_cfg = ProviderConfig(
        provider_name="unauthorized_mock",
        provider_type=ProviderType.MOCK,
    )
    with pytest.raises(ValueError, match="strictly prohibited in production mode"):
        gateway.register_provider(mock_cfg)


def test_production_mode_mock_adapter_execution_rejection(monkeypatch):
    monkeypatch.setenv("GAYATRI_ENV", "production")
    cfg = ProviderConfig(provider_name="rogue_mock", provider_type=ProviderType.MOCK)
    adapter = MockAIAdapter(cfg)

    desc = AIModelDescriptor(model_id="m", model_name="m")
    req = AIExecutionRequest(prompt="Help with math")
    res = adapter.execute(req, desc)

    assert res.success is False
    assert res.status == ModelExecutionStatus.MODEL_CONFIGURATION_ERROR
    assert res.error_class == "MockInProductionProhibited"
    assert res.content == ""


# ── 4. Fallback Chain without Mock Injection (F-011) ──────────────────────

def test_gateway_fallback_between_real_providers(openai_model_desc, monkeypatch):
    """When primary provider fails with 500, fallback to configured secondary provider succeeds without mock."""
    monkeypatch.setenv("PRIMARY_KEY", "sk-pri")
    monkeypatch.setenv("SECONDARY_KEY", "sk-sec")

    pri_desc = AIModelDescriptor(model_id="m-pri", model_name="m-pri", tier=ModelTier.TIER_2_STANDARD)
    sec_desc = AIModelDescriptor(model_id="m-sec", model_name="m-sec", tier=ModelTier.TIER_2_STANDARD)

    pri_cfg = ProviderConfig(
        provider_name="primary_provider",
        provider_type=ProviderType.OPENAI,
        api_key_ref="PRIMARY_KEY",
        priority=1,
        fallback_provider="secondary_provider",
        models=[pri_desc],
    )
    sec_cfg = ProviderConfig(
        provider_name="secondary_provider",
        provider_type=ProviderType.OPENAI,
        api_key_ref="SECONDARY_KEY",
        priority=2,
        models=[sec_desc],
    )

    gateway = AIGatewayService(db=PlatformDatabase(":memory:"))
    gateway.adapters.clear()
    gateway.router.providers.clear()
    gateway.register_provider(pri_cfg)
    gateway.register_provider(sec_cfg)

    # Primary fails with 500, secondary returns valid answer
    err_500 = urllib.error.HTTPError(url="http://fail", code=500, msg="Fail", hdrs={}, fp=None)
    succ_resp = MagicMock()
    succ_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": "Fallback provider succeeded."}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }).encode("utf-8")
    succ_resp.__enter__.return_value = succ_resp

    with patch("urllib.request.urlopen", side_effect=[err_500, succ_resp]):
        req = AIExecutionRequest(prompt="Test fallback", task_type=TaskType.TUTORING)
        res = gateway.execute(req)

    assert res.success is True
    assert res.provider == "secondary_provider"
    assert res.content == "Fallback provider succeeded."
    assert res.fallback_used is True
    assert res.original_provider == "primary_provider"
    assert res.mock is False


def test_gateway_all_providers_fail_returns_structured_failure():
    """When all providers fail, gateway returns success=False without silently falling back to mock."""
    gateway = AIGatewayService(db=PlatformDatabase(":memory:"))
    gateway.adapters.clear()
    gateway.router.providers.clear()

    desc = AIModelDescriptor(model_id="fail-m", model_name="fail-m")
    cfg = ProviderConfig(
        provider_name="failing_cloud",
        provider_type=ProviderType.OPENAI,
        api_key_ref="UNSET_KEY",
        priority=1,
        models=[desc],
    )
    gateway.register_provider(cfg)

    req = AIExecutionRequest(prompt="Explain kinetic energy", task_type=TaskType.TUTORING)
    res = gateway.execute(req)

    assert res.success is False
    assert res.status in (ModelExecutionStatus.MODEL_CONFIGURATION_ERROR, ModelExecutionStatus.MODEL_UNAVAILABLE)
    assert res.mock is False
    assert res.content == ""


# ── 5. Tutor Fail-Closed Semantics on AI Failure (F-013, F-014) ────────────

def test_tutor_orchestrator_fails_closed_when_ai_gateway_fails(mem_db):
    """When AI model execution fails, tutor must NOT fabricate a turn or update student mastery."""
    orchestrator = GenericTutorOrchestrator(db=mem_db)

    # Mock the gateway to return failure
    failed_ai_result = AIExecutionResult(
        request_id="req-fail-001",
        content="",
        provider="cloud_llm",
        model="gpt-4o",
        success=False,
        status=ModelExecutionStatus.MODEL_UNAVAILABLE,
        error_class="HTTP_503",
        error_message="Service Unavailable from upstream LLM provider",
        mock=False,
    )

    with patch.object(orchestrator.ai_gateway, "execute", return_value=failed_ai_result):
        turn_req = TutorTurnRequest(
            student_id="std-04-101",
            course_id="crs-physics-101",
            session_id="ses-04-101",
            message="Why does an object continue moving in space?",
            max_tokens=256,
        )

        turn_res = orchestrator.execute_turn(turn_req)

    # 1. Zero fabricated turn
    assert turn_res.status == "MODEL_UNAVAILABLE"
    assert turn_res.validation_passed is False
    assert turn_res.state_committed is False
    assert turn_res.pedagogical_action == "SERVICE_UNAVAILABLE"
    assert "temporarily unavailable" in turn_res.response_text

    # 2. No mastery update staged or committed
    canonical_state = orchestrator.learning_state.get_canonical_state("std-04-101", "crs-physics-101")
    assert len(canonical_state.mastery) == 0  # No mastery created or incremented!
    assert len(canonical_state.recent_events) == 0  # No learning events committed!



    # 3. Provenance record reflects failure and mock: false
    assert turn_res.model_provenance["provider"] == "cloud_llm"
    assert turn_res.model_provenance["model"] == "gpt-4o"
    assert turn_res.model_provenance["mock"] is False
    assert turn_res.model_provenance["success"] is False
    assert turn_res.model_provenance["status"] == "MODEL_UNAVAILABLE"

