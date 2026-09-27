# Authoritative Frozen Baseline Benchmarks (Phase 01)

This directory contains the frozen empirical baseline generated during Phase 01.
Per Section 10 of `GAYATRI_V2_PLATFORM_RECONCILIATION_PRODUCTION_MASTER_PLAN.md`, these scores establish the regression lock.
No future platform migration, API rewrite, or database upgrade may degrade these benchmark scores.

---

## 1. Frozen Benchmark Summary

- **Generated**: 2026-09-27T18:31:11.354332+00:00
- **Status**: **VERIFIED**
- **Total Cases Tested**: 44
- **Cases Passed**: 44
- **Accuracy**: 100.00%
- **Execution Time**: 0.098s

| Benchmark Suite | Total Cases | Passed | Accuracy | Status |
|---|---|---|---|---|
| **Chemistry Benchmark** | 21 | 21 | 100.0% | PASS |
| **RAG Retrieval Benchmark** | 7 | 7 | 100.0% | PASS |
| **Adaptive Learning Benchmark** | 7 | 7 | 100.0% | PASS |
| **Misconception Diagnosis Benchmark** | 9 | 9 | 100.0% | PASS |

---

## 2. Locked Invariants
1. **Chemistry Precision**: Stoichiometric balancing and numerical tolerance checking are 100% deterministic.
2. **Anti-Answer Leakage**: Student question and hint responses never expose raw answers or explanations prior to grading.
3. **BKT Monotonic Growth**: Repeated independent student success monotonically increases knowledge probability without arbitrary inflation.
4. **Misconception Catalog Integrity**: All 21 diagnostic misconception catalog codes are bound to valid Socratic remediation prompts.
5. **RAG Provenance & Citations**: Knowledge retrieved from NCERT textbooks is strictly factual evidence and includes verified page and chapter citations.

---

## 3. How to Reproduce
Run the frozen benchmark suite at any time:
```powershell
python scripts/run_frozen_baseline.py
```
