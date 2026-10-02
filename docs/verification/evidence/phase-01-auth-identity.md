# Phase 01 Evidence — Authentication & Identity Binding

## Objective
Enforce strict authentication on protected endpoints (`/tutor/turn`), bind request identity to authenticated principal, eliminate fabricated fallback identities in production, and fail closed when JWT secrets are missing or default.

## Starting commit
`a20e317` (`master`)

## Files changed
- `central_platform/auth/dependencies.py`: Removed synthetic user fallback in production mode; fail closed with 401 if user account is not found in database.
- `central_platform/auth/tokens.py`: Added `get_jwt_secret_key()` refusing default fallback secret in production mode.
- `central_platform/api/routes/tutor.py`: Enforced strict `current_user: User = Depends(get_current_user)` and `enforce_resource_boundaries()` preventing identity spoofing.
- `tests/test_phase01_auth_identity_remediation.py`: Added 8 adversarial and regression tests covering F-001, F-002, and F-004.
- `tests/test_phase10_generic_tutor_orchestrator.py`: Updated test to pass authenticated token and verify unauthenticated 401 rejection.
- `tests/test_phase12_real_online_api_boundary.py`: Updated test to pass authenticated token and verify unauthenticated 401 rejection.
- `tests/test_phase18_teacher_instruction_rag_integration.py`: Updated test to pass authenticated token.
- `tests/test_phase22_security_privacy_isolation_audit.py`: Updated injection test to pass authenticated token.

## Defects addressed
- **F-001 (P0):** Protected APIs can operate without authentication. Fixed: `/tutor/turn` strictly requires valid Bearer token.
- **F-002 (P0):** Caller-supplied `student_id` is not bound to authenticated identity. Fixed: `enforce_resource_boundaries` blocks student identity spoofing with 403.
- **F-004 (P1):** In-memory fabrication of default `org-default` fallback user. Fixed: In production, missing database user returns 401; missing production JWT secret aborts with `RuntimeError`.

## Tests added
- `tests/test_phase01_auth_identity_remediation.py`:
  - `test_F001_unauthenticated_tutor_request_returns_401`
  - `test_F001_malformed_bearer_token_returns_401`
  - `test_F001_expired_token_returns_401`
  - `test_F002_student_cannot_spoof_other_student_id_returns_403`
  - `test_F002_valid_student_accesses_own_turn_succeeds`
  - `test_F004_nonexistent_user_fails_closed_in_production`
  - `test_F004_production_startup_without_jwt_secret_fails_safely`
  - `test_F004_revoked_token_returns_401`

## Tests executed
- `pytest -v tests/test_phase01_auth_identity_remediation.py`: 8 passed in 7.24s.
- `pytest tests/test_phase10_generic_tutor_orchestrator.py tests/test_phase12_real_online_api_boundary.py tests/test_phase18_teacher_instruction_rag_integration.py tests/test_phase22_security_privacy_isolation_audit.py`: 47 passed in 17.16s.
- `pytest -q`: 1,152 passed in 225.57s (0 failed, 0 skipped, 100% pass rate).

## Runtime verification
- Verified live HTTP 401 on unauthenticated tutor request.
- Verified live HTTP 403 when student A attempts to submit turn for student B.
- Verified live HTTP 200 when student A submits turn for student A.
- Verified runtime abort when `GAYATRI_ENV=production` and `GAYATRI_JWT_SECRET` is unset.

## Security verification
- Zero anonymous access to `/tutor/turn`.
- Zero student identity spoofing permitted.
- Revocation registry checks enforced.

## Regression verification
- Legacy test callers updated to pass authenticated context; all regression suites pass.

## Failure-injection results
- Injected expired token -> 401 rejected.
- Injected revoked token -> 401 rejected.
- Injected missing DB user in production -> 401 rejected.
- Injected missing JWT secret in production -> `RuntimeError` startup abort.

## Known limitations
None for Phase 01.

## Ending commit
`a2e6a03` (`fix/phase-01-auth-identity`)

## Next phase
Phase 02: Course, Enrollment, Version, and Context Resolution
