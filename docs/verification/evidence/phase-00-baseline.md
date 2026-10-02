# Phase 00 Evidence — Ground Truth & Baseline Truth

## Objective
Establish repository ground truth, reconcile canonical branch policy, make CI reproducible, and eliminate contradictory production readiness claims before modifying application code.

## Starting commit
`379f911` (`master`)

## Files changed
- `PROJECT_STATE.yaml`: Reconciled false `PRODUCTION_RELEASE_READY` claim with explicit verification fields.
- `docs/verification/VERIFICATION_STATE.yaml`: Added per-phase manifest tracking execution status, test commands, runtime/security results, and evidence.
- `docs/verification/REMEDIATION_PROGRESS.yaml`: Added machine-readable remediation progress tracking YAML per Section 23.
- `docs/verification/BRANCH_POLICY.md`: Documented canonical branch policy establishing `master` as active development and `main` as release mirror per Section 0.1.
- `docs/verification/evidence/phase-00-baseline.md`: Created baseline evidence record.

## Defects addressed
- **F-019 (P0):** Readiness checks tested object existence rather than real runtime behavior.
- **F-020 (P0):** Claimed verified state contradicted actual CI and branch state.
- **F-021 (P1):** Divergence between `main` and `master` clarified with documented merge lineage.
- **F-022 (P0):** Test suite cataloged for obsolete contracts to be updated in subsequent phases.

## Tests executed
- `python -m compileall app core central_platform tests scripts`: 0 errors.
- `pytest -q`: 1,144 passed in 202.80s (0 failed, 0 skipped, 100% pass rate).

## Runtime verification
- Python 3.12.10 64-bit on Windows 11 verified.
- Dependency hygiene verified: `requirements.txt` and `pyproject.toml` declare all core packages (`PySide6`, `fastapi`, `uvicorn`, `pyjwt`, `psutil`, `rank-bm25`, `psycopg2-binary`, `pypdf`, `pymupdf`).
- Architecture guards in `tests/architecture/` confirmed intact.

## Security verification
- Audit of current state confirms 25 critical defects (F-001 through F-025) in production paths.
- Removed premature claims of `PRODUCTION_RELEASE_READY`.

## Regression verification
- Full test baseline preserved prior to any logic modifications.

## Failure-injection results
- N/A for Phase 00 (documentation and truth establishment).

## Known limitations
- The repository currently passes existing tests because those tests assert old contracts (e.g. unauthenticated access or auto-enrollment). These will be upgraded phase-by-phase without breaking genuine user workflows.

## Ending commit
(Pending commit on `fix/phase-00-ground-truth`)

## Next phase
Phase 01: Authentication and Identity Binding
