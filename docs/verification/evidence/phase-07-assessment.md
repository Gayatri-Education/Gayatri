# Phase 07 Evidence — Assessment Correctness and Learner Evidence

## Objective
Make assessment results reliable enough to serve as authoritative learning evidence per Master Plan Section 12 & Section 28:
1. Eliminate synthetic auto-provisioning in `AssessmentService._ensure_entities` and require real existing entities (fail-closed validation in production).
2. Implement deterministic numerical grading handling all edge cases: `0`, `-0`, `1e-3`, `1E3`, `NaN`, `Infinity`, tolerance thresholds, expected units, and disallowing ambiguous multiple numbers in explanations.
3. Guarantee MCQ and Boolean grading equivalence and whitespace/case normalization.
4. Provide transparent subjective rubric evaluation with dynamic calibrated confidence and explicit documentation of rule-based evaluator limitations.
5. Secure the assessment attempt lifecycle: in-progress attempts do not alter SLR concept mastery; double-submissions and student identity mismatches are rejected; and finalized submissions directly update authoritative SLR concept mastery.

## Starting commit
`6153aa0` (`master`)

## Files changed
- `central_platform/assessment/service.py`:
  - Added `allow_auto_provision: bool = False` flag to `AssessmentService.__init__`.
  - Refactored `_ensure_entities`: in production (`allow_auto_provision=False`), fails closed with explicit `ValueError` if referenced organization, course, or student does not exist, or if student organization mismatches.
  - In `submit_attempt`: added checks to reject already finalized attempts (`GRADED`, `SUBMITTED`, `reviewed`) and reject submissions where `student_id` does not match the attempt's student ID.
  - In `_emit_assessment_learning_events`: synchronized finalized assessment question scores directly into authoritative SLR concept mastery (`slr_service.update_concept_mastery`) and persisted detected misconceptions (`slr_service.record_student_misconception`).
- `central_platform/assessment/grading.py`:
  - Refactored `DeterministicGrader.grade_numerical`:
    - Strict rejection of `NaN`, `Infinity`, `inf`, `-inf`.
    - Normalization of signed zero (`-0.0` -> `0.0`).
    - Full scientific notation support (`1e-3`, `1E3`, `1.5e-4`).
    - Rejection of units-only answers without numerical magnitude.
    - Ambiguous multiple-number rejection in student explanations (unless explicitly designated via `final answer = ...`).
    - Unit extraction and verification: verifies matching units (`kJ` vs `J`), rejects incorrect units or missing units when expected.
  - Added `DeterministicGrader.grade_boolean`: normalizes True/False, T/F, yes/no, 1/0.
  - Enhanced `DeterministicGrader.grade_mcq`: handles letter tokens, parenthesized letters `(A)`, `Option A`, and option text.
  - In `AIAssistedGrader.grade_with_rubric`: derived `ai_confidence` dynamically from evidence instead of hardcoding `0.92`, and explicitly documented evaluator limitations in `ai_rationale`.
- `central_platform/api/routes/assessments.py`:
  - Wrapped `create_question`, `create_assessment`, and `create_assignment` in `try ... except ValueError as err: raise HTTPException(status_code=400, detail=str(err))`.
  - Preserved backward compatibility for legacy clients in `submit_assessment_legacy` by delegating to `legacy_service` configured with `allow_auto_provision=True`.
- `tests/test_phase11_generic_assessment_evaluation.py`:
  - Seeded `course-phys-1` and `course-cs-1` in `test_db` fixture for strict entity validation compliance.
- `tests/test_phase12_real_online_api_boundary.py`:
  - Seeded student entity in db before starting attempt in boundary test.
- `tests/test_phase07_assessment_remediation.py`:
  - Added 15 comprehensive contract and adversarial tests.

## Defects addressed
- **Section 12 Remediation Plan:**
  - Eliminated synthetic entity auto-provisioning in production assessment execution.
  - Solved numerical grading vulnerabilities (`0`, `-0`, scientific notation, `NaN`/`Infinity` exploits, units, ambiguous multi-number parsing).
  - Ensured in-progress attempts cannot prematurely advance persistent SLR mastery.
  - Replaced hardcoded rubric confidence with dynamic evidence-based confidence and transparent evaluator documentation.

## Tests added
- `tests/test_phase07_assessment_remediation.py`:
  - `test_entity_validation_missing_course_rejected`: Verifies creating questions/assessments for non-existent courses fails closed.
  - `test_entity_validation_missing_student_rejected`: Verifies starting attempt for non-existent student fails closed.
  - `test_entity_validation_wrong_organization_rejected`: Verifies attempt rejected if student organization does not match assessment.
  - `test_numerical_zero_and_negative_zero`: Verifies 0, -0, and +0 evaluate as equivalent zero magnitude.
  - `test_numerical_scientific_notation`: Verifies scientific notation (1e-3, 1E3, 1.5e-4) evaluated accurately.
  - `test_numerical_nan_and_infinity_rejection`: Adversarial test rejecting NaN, Infinity, -inf.
  - `test_numerical_units_only_rejected`: Adversarial test rejecting unit strings without numerical magnitude.
  - `test_numerical_multiple_numbers_in_explanation`: Verifies rejection of ambiguous multi-number explanations and acceptance of designated final answers.
  - `test_numerical_unit_verification`: Verifies correct value with correct unit passes, wrong unit fails, missing unit fails.
  - `test_mcq_letter_and_content_equivalence`: Verifies MCQ letter, parenthesized letter, and text equivalence.
  - `test_boolean_grading_normalization`: Verifies True/False boolean normalization.
  - `test_rubric_evaluation_dynamic_confidence_and_limitations`: Verifies dynamic confidence calculation and documented evaluator limitations.
  - `test_in_progress_attempt_does_not_alter_slr`: Invariant test: in-progress attempt emits 0 learning events and alters 0 SLR mastery scores.
  - `test_submit_attempt_updates_slr_and_learning_events`: Verifies submitted attempt updates authoritative SLR concept mastery and learning events.
  - `test_adversarial_attempt_student_mismatch_and_double_submit`: Verifies student identity mismatch and attempt double-submission are rejected.

## Verification result
- **Test Suite Pass Rate:** 1,211 passed in 268.79s (100% pass rate, 0 failures).
- **Targeted Suites:**
  - `tests/test_phase07_assessment_remediation.py`: 15/15 passed.
  - `tests/test_phase19_assessment_platform.py`: 7/7 passed.
  - `tests/test_phase11_generic_assessment_evaluation.py`: 12/12 passed.
  - `tests/test_phase7_assessment_engine.py`: 5/5 passed.
  - `tests/test_phase02_platform_api.py`: 23/23 passed.
  - `tests/test_phase12_real_online_api_boundary.py`: 12/12 passed.
  - All Phase 1–7 remediation suites (67 tests): 67/67 passed.
