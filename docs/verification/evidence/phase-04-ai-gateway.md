# Phase 04 Evidence — AI Gateway and Model Failure Semantics

## Objective
A model response must mean an actual configured model provider succeeded. Eliminate automatic fallback to `mock_engine`, eliminate synthetic mock completions on provider failures, enforce strict provider error states, fail closed on provider failure without fabricating tutor turns, and record machine-readable provenance.

## Starting commit
`53e506f` (`master`)

## Files changed
- `central_platform/ai/schema.py`:
  - Added enum `ModelExecutionStatus`: `MODEL_SUCCESS`, `MODEL_UNAVAILABLE`, `MODEL_TIMEOUT`, `MODEL_RATE_LIMITED`, `MODEL_CONFIGURATION_ERROR`, `MODEL_INVALID_RESPONSE`.
  - Added `status: ModelExecutionStatus` and `mock: bool` to `AIExecutionResult`.
  - Added `provenance` property returning `{ "provider": ..., "model": ..., "mock": ..., "status": ... }`.
- `central_platform/api/schemas.py`:
  - Added `mock: bool = False` and `status: Optional[str] = None` to `AIExecutionApiResponse`.
- `central_platform/ai/adapters.py`:
  - Added `is_production_mode()` helper.
  - In `MockAIAdapter`: strictly rejected execution when `is_production_mode()` is True with `MODEL_CONFIGURATION_ERROR`; set `mock=True` on test mock generation.
  - In `OpenAICompatibleAdapter`, `AnthropicAdapter`, and `GeminiAdapter`:
    - Eliminated synthetic fallback to `MockAIAdapter` when API key is missing. Missing credentials now return fail-closed `MODEL_CONFIGURATION_ERROR`.
    - Added normalized exception handling (`map_exception_to_error_status`) categorizing HTTP 429 to `MODEL_RATE_LIMITED`, HTTP 5xx to `MODEL_UNAVAILABLE`, timeouts to `MODEL_TIMEOUT`, and malformed payloads to `MODEL_INVALID_RESPONSE`.
    - Real provider executions return `mock=False`.
  - In `LocalGGUFAdapter`:
    - Failed closed with `MODEL_UNAVAILABLE` when local inference is unavailable in production.
- `central_platform/ai/gateway.py`:
  - Eliminated automatic fallback injection of `"mock_engine"` (lines 214-215).
  - Enforced production safety gate in `_init_default_providers` and `register_provider` rejecting `mock_engine` and mock adapters when `GAYATRI_ENV=production`.
  - In `execute()`: when all providers fail, returns fail-closed `AIExecutionResult` with structured error status (`status=last_error_status`, `mock=False`).
- `central_platform/ai/model_router.py`:
  - In `route()`: when no eligible provider is found in production mode, returns empty target provider instead of defaulting to `mock_engine`.
- `central_platform/api/routes/ai.py`:
  - Populated `mock` and `status` in `AIExecutionApiResponse` for both success and error responses.
- `central_platform/tutor/orchestrator.py`:
  - In `execute_turn()`: when `not ai_res.success`, fails closed immediately:
    - Zero fabricated tutor responses (does not substitute validation fallback).
    - Zero state commits (does not stage or commit mastery updates or learning events).
    - Returns `status="MODEL_UNAVAILABLE"`, `pedagogical_action="SERVICE_UNAVAILABLE"`, `validation_passed=False`, `state_committed=False`.
    - Populates `model_provenance` with `{ provider, model, mock, status, success }`.
- `tests/test_phase22_cloud_provider_abstraction.py`:
  - Updated `test_openai_compatible_adapter_error_when_no_api_key` to assert fail-closed error with no mock completion.
- `tests/test_phase04_ai_gateway_remediation.py`:
  - Added 11 comprehensive positive and adversarial contract tests.

## Defects addressed
- **F-011 (P0):** Gateway appends `mock_engine` to fallback chains. Fixed: Removed automatic mock injection. In production, mock providers are prohibited and rejected.
- **F-012 (P0):** Provider failures/timeouts converted to mock completions. Fixed: Missing credentials, timeouts, HTTP 500s, 429s, and malformed responses return explicit failure states (`MODEL_TIMEOUT`, `MODEL_UNAVAILABLE`, `MODEL_RATE_LIMITED`, `MODEL_CONFIGURATION_ERROR`, `MODEL_INVALID_RESPONSE`) with `mock: false`.
- **F-013 (P1):** Tutor orchestrator executes turns on empty response when AI gateway fails. Fixed: Tutor halts turn immediately upon model failure; state staging and commits are aborted; student mastery is unchanged.
- **F-014 (P1):** Missing explicit machine-readable provider provenance. Fixed: `model_provenance` records exact provider, model, status, and `mock: false`.

## Tests added
- `tests/test_phase04_ai_gateway_remediation.py`:
  - `test_provider_success_contract`
  - `test_provider_timeout_contract`
  - `test_provider_http_500_unavailable_contract`
  - `test_provider_rate_limited_contract`
  - `test_provider_invalid_json_contract`
  - `test_missing_credentials_fails_closed`
  - `test_production_mode_rejects_mock_provider_registration`
  - `test_production_mode_mock_adapter_execution_rejection`
  - `test_gateway_fallback_between_real_providers`
  - `test_gateway_all_providers_fail_returns_structured_failure`
  - `test_tutor_orchestrator_fails_closed_when_ai_gateway_fails`

## Tests executed
- `pytest tests/test_phase04_ai_gateway_remediation.py -v`: 11 passed in 0.78s.
- `pytest tests/test_phase22_cloud_provider_abstraction.py tests/test_phase17_ai_gateway_model_router_platform.py -v`: 23 passed in 2.96s.
- `pytest tests/test_phase09_model_registry_ai_gateway.py -v`: 14 passed in 0.26s.
- `pytest tests/test_phase10_generic_tutor_orchestrator.py -v`: 11 passed in 2.89s.
- `pytest tests/test_phase18_teacher_instruction_rag_integration.py -v`: 12 passed in 13.45s.
- `pytest -q`: 1,178 passed in 259.75s (0 failures, 0 skipped, 100% pass rate).
- `python -m compileall central_platform core tests`: 0 errors.

## Runtime verification
- Verified that missing credentials for cloud providers never produce synthetic mock completions.
- Verified that setting `GAYATRI_ENV=production` blocks registration and execution of mock providers.
- Verified that upstream model failure halts tutor execution without incrementing student mastery or staging learning events.
- Verified that provenance records distinguish real execution (`mock: false`) from mock testing (`mock: true`).

## Next phase
Phase 5 — Transactional learning state and authoritative SLR.
