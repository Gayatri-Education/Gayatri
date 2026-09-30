# Documentation Inventory & Audit (Phase 01)

## 1. Setup Instructions
- **Location:** `README.md`
- **Contents:** Mentions Python 3.12+, `git clone`, `venv`, and `pip install -r requirements.txt`. Also states how to run tests (`pytest`).
- **Status:** Still largely valid for the local setup, but ignores the incoming Postgres setup or multi-tenant portal requirements.

## 2. Architecture Claims
- **Location:** `README.md`, `docs/AI_AGENT_ARCHITECTURE_AND_TRAINING_FLOW.md`, `docs/INFERENCE_ARCHITECTURE.md`, `docs/architecture/current-state.md`, `docs/REPOSITORY_ARCHITECTURE_CURRENT.md`
- **Claims:** Claims a V3 architecture using Qwen/Qwen2.5-0.5B-Instruct, local RAG, deterministic evaluator, and an adaptive learning engine. Mentions `core/tutor/state.py` for student-scoped state.
- **Contradictions:** The new Master Plan aims to unify state into a Postgres database (`central_platform`), whereas `README.md` and some architecture docs claim SQLite/JSON tracking. `current-state.md` might be out of sync with the V4 target.

## 3. Model Instructions
- **Location:** `model_manifest.json`, `docs/prompts/prompt_registry.md`, `docs/LLM_CALL_GRAPH.md`
- **Status:** The manifest expects Qwen2.5-0.5B-Instruct (GGUF Q4_K_M). This aligns with the new Master Plan's requirement for a declarative manifest.

## 4. Stale Information & Legacy Trackers
- The repository is flooded with legacy tracking documents from previous phases:
  - `docs/GAYATRI_TUTOR_V3_ENGINEERING_TRACKER.md` (75KB+)
  - `docs/implementation/V2_PLATFORM_MASTER_PLAN.md`
  - `docs/implementation/GAYATRI_TUTOR_INTELLIGENCE_UPGRADE_MASTER_PLAN.md`
  - `docs/implementation/GAYATRI_INTELLIGENCE_PROGRESS.md`
  - `GAYATRI_V2_PLATFORM_RECONCILIATION_PRODUCTION_MASTER_PLAN.md`
  - `CLEANUP_REPORT.md`
  - `CURRENT_REPO_AUDIT.md`
  - `docs/PROJECT_PROGRESS.md`
- **Action:** These are stale. The single source of truth is now `Gayatri_AI_Agent_Master_Development_Plan.md` and the 4 new control docs (`PROJECT_STATE.md`, `PHASE_LOG.md`, `BUG_TRACKER.md`, `DECISIONS.md`).

## 5. Operations & Security
- **Location:** `docs/operations/deployment-guide.md`, `docs/operations/backup-and-restore.md`, `docs/security/security-regression.md`, `docs/PRIVACY_CONTRACT.md`
- **Status:** To be verified against the new V4 requirements. `PRIVACY_CONTRACT.md` claims isolation, but needs testing against multi-tenant boundaries.

## 6. Next Steps for Documentation
- Do NOT rewrite `README.md` yet.
- Retain existing docs for reference, but ignore old trackers in favor of the Master Plan.
- Future phases will produce consolidated V4 architecture docs and eventually replace the README.
