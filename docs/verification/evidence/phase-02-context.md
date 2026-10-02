# Phase 02 Evidence — Course, Enrollment, Version, and Context Resolution

## Objective
Eliminate automatic provisioning and context guessing during tutor turn execution so that tutor sessions depend strictly on authoritative platform state.

## Starting commit
`4d45a8c` (`master`)

## Files changed
- `central_platform/tutor/orchestrator.py`: Removed public course auto-enrollment; removed user auto-creation; enforced session identity & course ownership; hardened version resolution.
- `tests/test_phase10_generic_tutor_orchestrator.py`: Converted stale auto-enroll test to strict regression test requiring explicit prior enrollment; pre-enrolled student in history test.
- `tests/test_phase02_context_resolution_remediation.py`: Added 6 adversarial and regression tests covering F-003, F-010, and F-023.

## Defects addressed
- **F-003 (P1):** Tutor can create users/sessions/enrollments automatically. Fixed: Zero auto-enrollment and zero user creation in orchestrator.
- **F-010 (P1):** Context failures swallowed and tutor continues. Fixed: Strict error propagation and session ownership checks.
- **F-023 (P1):** Missing learner/course context synthesized instead of rejected. Fixed: Unpublished versions explicitly rejected.

## Tests added
- `tests/test_phase02_context_resolution_remediation.py`:
  - `test_F003_public_course_unenrolled_student_raises_enrollment_error`
  - `test_F003_tutor_never_auto_creates_user_in_db`
  - `test_F003_session_belonging_to_another_student_raises_error`
  - `test_F003_session_belonging_to_another_course_raises_error`
  - `test_F023_unpublished_course_version_rejected`
  - `test_F023_enrolled_student_with_published_version_succeeds`

## Tests executed
- `pytest -v tests/test_phase02_context_resolution_remediation.py`: 6 passed in 5.06s.
- `pytest -q`: 1,158 passed in 240.45s (0 failures, 0 skipped, 100% pass rate).

## Runtime verification
- Unenrolled student submitting turn to public course returns `EnrollmentError` (403).
- Turn request with unregistered student returns `EnrollmentError` (403); zero users inserted into DB.
- Reusing an existing session from another student returns `EnrollmentError` (403).
- Requesting DRAFT or ARCHIVED version returns `CourseNotFoundError` (404).

## Security verification
- Cross-student session hijacking prevented.
- Cross-course session pollution prevented.
- Public course enrollment boundary strictly enforced.

## Regression verification
- All existing legitimate workflows pre-enroll students via authoritative provisioning API; full regression suite passing.

## Failure-injection results
- Injected unregistered student -> EnrollmentError, 0 writes.
- Injected unenrolled public course -> EnrollmentError, 0 writes.
- Injected cross-student session -> EnrollmentError, 0 writes.
- Injected unpublished course version -> CourseNotFoundError, 0 writes.

## Known limitations
None for Phase 02.

## Ending commit
(Pending commit on `fix/phase-02-context-resolution`)

## Next phase
Phase 03: RAG Authorization, Retrieval, and Grounding
