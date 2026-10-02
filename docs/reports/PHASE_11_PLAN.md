# Phase 11 Plan: Generic Assessment & Evaluation Engine

**Phase:** Phase 11 (Section 12.11 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`)  
**Objective:** Make assessments course-independent while preserving deterministic evaluators where domain adapters provide them.

---

## 1. Architectural Analysis & Current Baseline

### Current State
1. `central_platform/assessment/` contains:
   - `grading.py`: `DeterministicGrader` (MCQ, Numerical) and `AIAssistedGrader` (hardcoding Chemistry misconception patterns: `MISCON_THERMO_HEAT_WORK_CONFUSION`, `MISCON_ISOTHERMAL_ADIABATIC`, `MISCON_BOND_BREAKING_ENERGY`).
   - `service.py`: `AssessmentService._ensure_entities` hardcodes `"crs-chem-101"` and `"CHEM101"` as default course.
   - `models.py`: Assessment data models.
   - `rubrics.py`: Rubric templates.
   - `adaptive.py`: Adaptive testing engine.
2. `core/tutor/evaluator.py`:
   - `StudentAnswerEvaluator` contains fallback checking `chem_keywords = {"energy", "heat", "work", "enthalpy", "entropy", "gibbs", ...}`.
3. Tests:
   - 957 tests currently passing (100% green).
   - Existing assessment tests: `tests/test_phase11_assessment_engine.py`, `tests/test_phase11_assessment_platform.py`, `tests/test_phase19_assessment_platform.py`, `tests/test_phase6_evaluator.py`.

### Target State
1. **Capability-Driven Evaluator Registry (`central_platform/assessment/evaluators/`):**
   - Clean, modular evaluators registered by question capability (`MCQ`, `NUMERICAL`, `RUBRIC`, `CODE`, `BOOLEAN`, plus pluggable domain adapter evaluators like `CHEMISTRY_EQUATION`, `CHEMISTRY_REACTION`).
2. **Canonical 4-Valued Evaluation Contract:**
   - Result: `CORRECT`, `PARTIALLY_CORRECT`, `INCORRECT`, `UNCERTAIN`.
   - Typed `EvaluationOutcome`:
     - `outcome`: EvaluationResult enum / string (`CORRECT`, `PARTIALLY_CORRECT`, `INCORRECT`, `UNCERTAIN`)
     - `score`: float [0.0, 1.0]
     - `confidence`: float [0.0, 1.0]
     - `error_type`: string (`none`, `arithmetic`, `unit`, `conceptual`, `malformed`, `syntax`, `timeout`, `other`)
     - `misconception_code`: Optional[str] (resolved dynamically from course curriculum / domain adapter, not hardcoded)
     - `evidence`: List[str] explaining the evaluation decision
     - `remediation_hint`: Optional[str]
3. **Decoupled Deterministic & AI-Assisted Grading:**
   - Remove hardcoded chemistry misconceptions from `grading.py`. Misconceptions are looked up from the active course version or passed dynamically.
   - Remove `"crs-chem-101"` hardcoded default in `AssessmentService._ensure_entities`. Require explicit or course-derived context.
   - Generalize `core/tutor/evaluator.py` to decouple from subject-specific keyword fallback.
4. **Anti-Answer-Leakage Service (`central_platform/assessment/sanitizer.py`):**
   - Strips `correct_answer`, `rubric`, `explanation`, and solution steps from assessment payloads before delivering them to student clients during active attempts.
   - Validates that grading feedback given during formative/summative assessments does not leak answers to unanswered questions.
5. **Course & Version Isolation:**
   - Assessments, attempts, and question banks strictly scoped to `(course_id, course_version_id)`.
   - Remediation recommendations isolated to the course curriculum with zero cross-course contamination.
6. **Teacher Manual Review & Audit:**
   - Teacher can override AI grading, adjust marks, provide manual feedback, and approve final submissions.

---

## 2. Implementation Scope

### A. New Modules
- `central_platform/assessment/evaluators/base.py`: Abstract `BaseEvaluator` protocol and `EvaluationOutcome`.
- `central_platform/assessment/evaluators/registry.py`: `EvaluatorRegistry` allowing modular registration and capability-based lookup.
- `central_platform/assessment/evaluators/deterministic.py`: `MCQEvaluator`, `NumericalEvaluator` (with unit tolerance and unit mismatch detection), `BooleanEvaluator`.
- `central_platform/assessment/evaluators/rubric.py`: `RubricEvaluator` with dynamic course-specific misconception lookup.
- `central_platform/assessment/evaluators/code.py`: `CodeExecutionEvaluator` integrating with `ProgrammingSandboxAdapter`.
- `central_platform/assessment/evaluators/adapter_hooks.py`: Pluggable domain adapter evaluators (e.g. `ChemistryEquationEvaluator`).
- `central_platform/assessment/sanitizer.py`: `AssessmentSanitizer` enforcing anti-answer-leakage invariants.

### B. Modified Modules
- `central_platform/assessment/grading.py`: Re-export and delegate to modular evaluators; eliminate hardcoded `MISCONCEPTION_PATTERNS`.
- `central_platform/assessment/service.py`: Eliminate hardcoded `"crs-chem-101"` in `_ensure_entities`. Integrate with `EvaluatorRegistry` and `AssessmentSanitizer`.
- `core/tutor/evaluator.py`: Replace hardcoded `chem_keywords` fallback with domain-neutral substantive response checks and adapter hooks.

### C. Test Suite
- `tests/test_phase11_generic_assessment_evaluation.py`:
  1. Generic item types (MCQ, Numerical, Boolean, Rubric, Code execution).
  2. Uncertain answers (ambiguous single words "yes", "idk", empty answers).
  3. Malformed answers (invalid numerical format, syntax error in code).
  4. Unit mismatch evaluation (correct number, wrong unit -> `PARTIALLY_CORRECT` with `error_type="unit"`).
  5. Anti-answer-leakage verification (student attempt payload has zero answers/explanations).
  6. Course and version scoping (assessments strictly isolated between courses; no cross-talk).
  7. Teacher review and grading adjustment lifecycle.
  8. Remediation recommendation isolation (remediations belong solely to the tested course).
  9. Zero chemistry coupling in generic evaluators (static inspection invariant).

---

## 3. Verification Plan & Quality Gates

1. Run Phase 11 targeted test suite: `pytest tests/test_phase11_generic_assessment_evaluation.py -v`.
2. Run full regression suite: `pytest -q` (all 957+ tests must pass 100% green).
3. Generate reports: `docs/reports/PHASE_11_TEST_REPORT.md` and `docs/reports/PHASE_11_TEST_RESULTS.json`.
4. Update ledgers: `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`.
5. Git commit and push to `origin/master`.
