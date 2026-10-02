# Local Git Reconciliation Forensic Report

**Date of Audit:** 2026-10-02T15:55:00+05:30  
**Target Repository:** `Gayatri-Education/Gayatri`  
**Auditor:** Senior Software Architect & Repository Forensic Auditor  
**Local Operating System:** Windows (win32)  
**Local Python Environment:** Python 3.12.10  

---

## 1. Safety Baseline & Branch Invariants

Before any modifications were performed, repository safety invariants were verified:

```text
Working Branch:       master
Pre-Audit HEAD:       210d844495dab49b4f06d0bb4fb14387ef5ba5d9
Safety Branch:        forensic/local-truth-safety (pinned at 210d844495dab49b4f06d0bb4fb14387ef5ba5d9)
Remote URL:           https://github.com/Gayatri-Education/Gayatri.git
Untracked Code Files: 0 (working tree was clean)
```

No code was deleted, no force-pushes were executed, and no branches were discarded.

---

## 2. Remote Branch & Divergence Analysis

A full fetch and divergence inspection was executed against remote tracking branches:

```bash
git fetch --all --prune
git branch -a
git rev-list --left-right --count HEAD...origin/master
git rev-list --left-right --count HEAD...origin/main
```

### Observations:
1. **`origin/master`**:
   - Commit: `210d844495dab49b4f06d0bb4fb14387ef5ba5d9`
   - Divergence count `HEAD...origin/master`: `0 0` (local `master` was in exact sync with `origin/master`).
2. **`origin/main`**:
   - Commit: `43baf6965645e8dd65dedc7b20025b8894e6ac96`
   - Commit Message: `Merge pull request #3 from Gayatri-Education/master`
   - Divergence count `HEAD...origin/main`: `0 3` (3 merge commits on `main` merging `master` via GitHub Pull Requests #1, #2, #3).
   - Tree Difference: `git diff master origin/main` returned **empty** (0 lines difference). The source tree on `origin/main` was bit-for-bit identical to `master`.
3. **Repository Default Branch**:
   - `remotes/origin/HEAD` points to `origin/main` on GitHub.
   - Development is actively committed on `master` and promoted to `main` via PR merges.
   - **Decision**: Retain `master` as the active working development branch and synchronize to GitHub, keeping branch history transparent and unforced.

---

## 3. GitHub Actions CI Failure Forensic Analysis

Inspection of GitHub Actions workflow runs via the GitHub API (`https://api.github.com/repos/Gayatri-Education/Gayatri/actions/runs?per_page=5`) revealed:

- **Run #53** (`main` / `43baf69`): `failure` (Completed at 2026-10-02T09:47:41Z)
- **Run #52** (`master` PR #3 / `210d844`): `failure` (Completed at 2026-10-02T09:47:07Z)
- **Run #51** (`master` / `210d844`): `failure` (Completed at 2026-10-02T09:43:44Z)
- **Run #50** (`master` / `f22c474`): `failure` (Completed at 2026-10-02T09:45:05Z)

### Step-by-Step CI Breakdown (Job 110786604686):
| Step # | Step Name | Status | Conclusion | Duration |
|---|---|---|---|---|
| 1 | Set up job | completed | `success` | 1s |
| 2 | Run actions/checkout@v4 | completed | `success` | 9s |
| 3 | Set up Python 3.12 | completed | `success` | 4s |
| 4 | Install dependencies | completed | `success` | 8m 53s |
| 5 | Verify compilation hygiene | completed | `success` | 2s |
| 6 | Run architecture guardrail suite | completed | `success` | 3s |
| **7** | **Run headless test suite** | **completed** | **`failure`** | **21s** |
| 14 | Post Run actions/checkout@v4 | completed | `success` | 3s |
| 15 | Complete job | completed | `success` | 0s |

### Root Cause of CI Failure:
Step 4 executed:
```bash
pip install -r requirements.txt
```
Prior to this task, `requirements.txt` contained only:
```text
PySide6>=6.11.0
llama-cpp-python>=0.3.0
httpx>=0.27.0
cryptography>=43.0.0
pydantic>=2.0
pytest>=8.0.0
pytest-qt>=4.4.0
ruff>=0.6.0
```
It **lacked** declarations for:
- `fastapi`
- `uvicorn`
- `pyjwt`
- `psutil`
- `rank-bm25`

When Step 7 executed `pytest -v -m "not gui"`, pytest immediately encountered `ModuleNotFoundError: No module named 'fastapi'` when collecting or importing API routers (e.g. `tests/test_phase02_platform_api.py`), terminating the CI run within 21 seconds with failure.

Meanwhile, on the local developer machine, these packages were already present in the global Python 3.12 environment, creating a **silent disparity between local test success and remote CI failure**.

---

## 4. Reconciled Local Modifications

During this reconciliation task, the following changes were applied and tested:

1. **`requirements.txt`**: Added explicit declarations for `fastapi>=0.110.0`, `uvicorn>=0.28.0`, `pyjwt>=2.8.0`, `psutil>=5.9.0`, `rank-bm25>=0.2.2`, `pypdf>=4.0.0`, `pymupdf>=1.24.0`.
2. **`pyproject.toml`**:
   - Updated package discovery from `include = ["app*", "core*", "tests*"]` to `include = ["app*", "core*", "central_platform*", "adapters*", "tests*"]`.
   - Updated runtime dependencies to include all required packages.
   - Updated platform version to `5.0.0` and license to `MIT`.
3. **`.github/workflows/ci.yml`**: Added `env: QT_QPA_PLATFORM: offscreen` to headless test step to ensure reliable headless execution on Windows CI runners.
4. **`docs/forensics/*`**: Created authoritative evidence documents capturing the true state of the repository.

---

## 5. Recent Commit History on Authoritative Development Branch

```text
210d844 chore: mark documentation sync queue item 025 pushed
f22c474 docs: comprehensive update to README, architecture, data model, and project state for Phase 23
4578abf docs: update PROJECT_STATE.md with Phase 23 commit hash (1a8bfd4) and 1,114 verified passing tests
1a8bfd4 feat(phase23): reliability, failure injection & recovery — standardized contracts across 12 failure domains
54edfe9 docs: update PROJECT_STATE.md with Phase 22 commit hash and verified test count (1,102)
585c6a3 feat(phase22): security, privacy & isolation audit — RBAC gaps, prompt injection guard, RAG auth, privilege escalation fixes
6b86258 feat(phase21): reconcile schema manifest, harden migration runner, and verify integrity
fcb9720 feat(phase20): remove legacy directory, dead configs, and stale scratch assets
7e2c6dc feat(phase19): extract chemistry domain adapter and verify disablement
a3885ec feat(phase18): integrate teacher instructions with rag, add provenance tracking, and fix deadends and silent fails
8f65325 feat(phase17): implement student multi-course workflow ui
1210a25 feat(phase16): implement teacher workflow ui and class management
3fb9d8e feat(phase15): implement admin course and content workflow ui
33df924 feat(phase14): implement sync and conflict resolution
b88b616 feat(phase13): implement offline local runtime package and sync readiness
386dd5e fix: resolve silent failures, deadends, and assertion guards across test and production modules
```
