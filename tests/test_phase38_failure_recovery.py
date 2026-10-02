"""Phase 38 — Failure Recovery & Resilience Subsystem Unit & Integration Tests.

Verifies:
1. FailureCategory & RecoveryStatus enums and RecoveryResult serialization.
2. Local model unavailable & corrupt model fallback to lightweight SLM.
3. Provider timeout handling & fallback routing.
4. RAG retrieval failure fallback to direct curriculum context.
5. Database query failure fallback to snapshot cache.
6. Self-healing JSON repair for malformed LLM outputs (markdown fences, raw text wrapping).
7. Payment gateway transaction failure rollback.
"""

import pytest

from central_platform.recovery.manager import (
    FailureCategory,
    FailureRecoveryManager,
    RecoveryResult,
    RecoveryStatus,
)


def test_failure_recovery_contracts():
    res = RecoveryResult(
        failure_category=FailureCategory.MODEL_UNAVAILABLE,
        status=RecoveryStatus.DEGRADED_FALLBACK,
        fallback_used="LocalSLM",
        message="Model fallback active",
    )
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    d = res.to_dict()
    assert d["failure_category"] == "model_unavailable"
    assert d["status"] == "degraded_fallback"


def test_handle_model_failure():
    res_unavail = FailureRecoveryManager.handle_model_failure(RuntimeError("CUDA out of memory"))
    assert res_unavail.failure_category == FailureCategory.MODEL_UNAVAILABLE
    assert res_unavail.status == RecoveryStatus.DEGRADED_FALLBACK
    assert "Qwen2.5-0.5B" in res_unavail.fallback_used

    res_corrupt = FailureRecoveryManager.handle_model_failure(ValueError("GGUF header invalid"), is_corrupt=True)
    assert res_corrupt.failure_category == FailureCategory.CORRUPT_MODEL
    assert res_corrupt.status == RecoveryStatus.DEGRADED_FALLBACK


def test_handle_provider_timeout_and_rag_failure():
    res_timeout = FailureRecoveryManager.handle_provider_timeout(TimeoutError("Gateway timeout"))
    assert res_timeout.failure_category == FailureCategory.PROVIDER_TIMEOUT
    assert res_timeout.fallback_used == "LocalFirstRouter"

    res_rag = FailureRecoveryManager.handle_rag_failure(ConnectionError("Vector DB unavailable"), "Photosynthesis")
    assert res_rag.failure_category == FailureCategory.RAG_FAILURE
    assert res_rag.data["concept"] == "Photosynthesis"


def test_handle_database_failure():
    res_db = FailureRecoveryManager.handle_database_failure(Exception("Disk I/O error"), {"student_id": "std_1"})
    assert res_db.failure_category == FailureCategory.DATABASE_FAILURE
    assert res_db.data["student_id"] == "std_1"


def test_repair_malformed_model_output():
    # 1. Valid JSON
    res_valid = FailureRecoveryManager.repair_malformed_model_output('{"answer": "42"}')
    assert res_valid.status == RecoveryStatus.RECOVERED
    assert res_valid.data["answer"] == "42"

    # 2. Markdown fence JSON
    raw_markdown = 'Here is the JSON output:\n```json\n{"summary": "Physics notes"}\n```'
    res_md = FailureRecoveryManager.repair_malformed_model_output(raw_markdown)
    assert res_md.status == RecoveryStatus.RECOVERED
    assert res_md.data["summary"] == "Physics notes"

    # 3. Unformatted raw text
    raw_plain = "The student answered correctly on topic 3."
    res_plain = FailureRecoveryManager.repair_malformed_model_output(raw_plain)
    assert res_plain.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res_plain.data["text"] == raw_plain


def test_handle_payment_failure():
    res_pay = FailureRecoveryManager.handle_payment_failure(ValueError("Insufficient funds"), "TXN_999")
    assert res_pay.failure_category == FailureCategory.PAYMENT_FAILURE
    assert res_pay.status == RecoveryStatus.RECOVERED
    assert res_pay.data["status"] == "failed_rolled_back"
