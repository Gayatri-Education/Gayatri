# Gayatri Repository Branch Policy

**Document:** `docs/verification/BRANCH_POLICY.md`  
**Governing Plan:** Section 0.1 of `GAYATRI_AI_AGENT_FORENSIC_REMEDIATION_PLAN.md`  
**Effective Date:** 2026-10-02  

---

## 1. Canonical Branch Declaration

- **Canonical Active Development Branch:** `master`
- **Release Mirror Branch:** `main`
- **Origin Remote:** `https://github.com/Gayatri-Education/Gayatri.git`

## 2. Forensic Reconciliation Analysis

A forensic audit of commit lineage between `origin/master` and `origin/main` was conducted on 2026-10-02:
1. `git merge-base origin/master origin/main` points to commit `f62d59c23c5089700048216e26ab6a23f6b7bb03`.
2. All non-merge commits on `main` originate from `master` and were integrated via GitHub pull requests (`PR #1`, `PR #2`, `PR #3`, `PR #4`).
3. `main` contains **zero independent application logic commits**.
4. `master` is 10 commits ahead of `main` containing subsequent course-decoupling and audit fixes up to commit `379f911`.
5. Therefore, `master` is declared the single canonical source of truth for all remediation work.

## 3. Workflow Protocol

1. **No Direct Commits to `master`:** Feature and bug-fix work must be developed on scoped branches (e.g., `fix/phase-XX-name`).
2. **Phase Completion Gates:** A phase branch may only be merged into `master` after independent runtime, security, test, and regression evidence has been recorded in `docs/verification/evidence/phase-XX-*.md`.
3. **Release Mirroring to `main`:** `main` shall only be updated via fast-forward or squash merge from `master` upon certified completion of release gates.
