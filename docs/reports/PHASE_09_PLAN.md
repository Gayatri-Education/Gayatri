# Phase 09 Implementation Plan: Model Registry & AI Gateway Unification

**Document ID:** `PHASE_09_PLAN`  
**Phase:** 09  
**Parent Plan:** [GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md](../../GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md) (Section 12.9)  
**Target Branch:** `master`  
**Author:** Antigravity AI  
**Status:** DRAFT - PENDING APPROVAL  

---

## 1. Executive Summary & Objectives

The primary objective of Phase 09 is to eliminate contradictory model configurations, establish a single authoritative model registry and manifest schema, decommission legacy inference dependencies (`BUG-ARCH-002`), and unify AI Gateway routing under strict architectural invariants.

### Key Objectives
1. **Unify Authoritative Model Manifest (`model_manifest.json`)**:
   - Align schema with Section 12.9 requirements: `model_id`, `provider`, `artifact_path`, `format`, `quantization`, `prompt_template`, `context_window`, `streaming`, `capabilities`, `resource_profile`, `checksum`, and versioning.
   - Maintain backward compatibility with existing validator keys (`core/model_fetch/manifest_validator.py`).
2. **Reconcile Core Configuration (`core/config.py` - `BUG-ARCH-006`)**:
   - Align `LOCAL_MODEL_FILE` detection and fallback with manifest default (`qwen2.5-0.5b-instruct-q4_k_m.gguf`).
   - Reconcile `MODEL_HUGGINGFACE_REPO` and `MODEL_GGUF_FILENAME` to eliminate contradictory legacy Gemma defaults.
3. **Decommission Legacy Inference Dependencies (`BUG-ARCH-002`)**:
   - Extract prompt construction (`build_chat_messages` / `_build_messages`) and tutor context extraction (`get_tutor_context` / `_get_tutor_context`) from `legacy/agents/default_agents.py` into a clean, decoupled `core/inference/context.py`.
   - Update `core/runtimes/chemistry.py` and `core/runtimes/general.py` to import exclusively from `core.inference.context`.
   - Refactor `core/inference/service.py` to route directly via `core.providers.local.LocalProvider` / provider registry instead of `legacy.agents.default_agents._local_chat_stream`.
   - Update `tests/architecture/test_anti_legacy_imports.py` to enforce **ZERO** legacy imports across `core/`, `central_platform/`, and `app/`.
4. **Observable Inference & Gateway Routing**:
   - Inference flow: Tutor Runtime $\rightarrow$ AI Gateway / InferenceService $\rightarrow$ Provider $\rightarrow$ Model.
   - Deterministic and observable fallbacks (no silent swaps, explicit logging).
   - Enforce privacy boundaries: `local_only` policy blocks non-local network egress fail-closed.
   - Comprehensive streaming, cancellation, and provider error/timeout handling without swallowing exceptions into false success (Rule 3).

---

## 2. Forensic Discovery & Baseline State

| Component | Current State | Target State | Notes |
|:---|:---|:---|:---|
| `model_manifest.json` | Qwen 2.5-0.5B with basic metadata | Complete manifest schema (`format`, `artifact_path`, `prompt_template`, `context_window`, `streaming`, `resource_profile`, `capabilities`) | Backward-compatible with existing schema keys. |
| `core/config.py` | Divergent `gemma-2-2b-it-IQ3_M.gguf` & `Gayatri-Tutor-v3-Q4_K_M.gguf` defaults | Synchronized with `model_manifest.json` (`qwen2.5-0.5b-instruct-q4_k_m.gguf`) | Resolves `BUG-ARCH-006`. |
| `core/inference/service.py` | Imports `_local_chat_stream` from `legacy.agents.default_agents` | Routes directly through `LocalProvider` / Provider Registry with fallback & privacy enforcement | Resolves `BUG-ARCH-002`. |
| `core/runtimes/chemistry.py` | Imports `_build_messages, _get_tutor_context` from `legacy` | Imports from `core.inference.context` | Eliminates legacy coupling while respecting no-central_platform boundary. |
| `core/runtimes/general.py` | Imports `_build_messages` from `legacy` | Imports from `core.inference.context` | Clean decoupled prompt formatting. |
| `tests/architecture/test_anti_legacy_imports.py` | Whitelists 3 legacy callers | Whitelist reduced to `set()` (Zero legacy callers allowed) | Strict architectural guard. |

---

## 3. Detailed Implementation Steps

### Step 1: Model Manifest Schema Extension & Validator Hardening
- Extend `model_manifest.json` with standardized fields:
  ```json
  {
    "model_id": "gayatri-chem-qwen2.5-0.5b-v4",
    "display_name": "Gayatri Chemistry Tutor (0.5B)",
    "provider": "local",
    "local_path": "models/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    "artifact_path": "models/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    "format": "gguf",
    "download_source": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    "quantization": "Q4_K_M",
    "context_length": 8192,
    "context_window": 8192,
    "architecture": "Qwen2.5",
    "parameter_count": "0.5B",
    "chat_template": "chatml",
    "prompt_template": "chatml",
    "streaming": true,
    "capabilities": ["text-generation", "socratic-tutoring", "tools", "json"],
    "supports_tools": true,
    "supports_json": true,
    "hardware_requirements": "1GB RAM, CPU",
    "resource_profile": "1GB RAM, CPU",
    "language_support": ["en", "hi"],
    "version": "v4.0",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "license": "MIT"
  }
  ```
- Enhance `core/model_fetch/manifest_validator.py` with:
  - Helper `get_active_manifest()` returning loaded and validated manifest dictionary.
  - Validation for `format`, `context_window` / `context_length`, and `prompt_template`.

### Step 2: Configuration Reconciliation (`core/config.py`)
- Update `_detect_initial_model_file()` default return value to `"qwen2.5-0.5b-instruct-q4_k_m.gguf"`.
- Update `MODEL_HUGGINGFACE_REPO` and `MODEL_GGUF_FILENAME` to point to the Qwen 2.5 0.5B GGUF source.
- Preserve backward-compatibility for path overrides (`GAYATRI_MODEL_FILE`).

### Step 3: Decouple Prompt Building (`core/inference/context.py`)
- Create `core/inference/context.py`:
  - `build_chat_messages(system_prompt, user_message, history=None, dynamic_context=None)`
  - `get_tutor_context(context=None)`
  - Aliases `_build_messages` and `_get_tutor_context` for smooth compatibility.
- Update `legacy/agents/default_agents.py` to import from `core.inference.context` and mark as deprecated.

### Step 4: Refactor `core/inference/service.py`
- Remove import from `legacy.agents.default_agents`.
- Implement robust `stream_chat` and `generate`:
  - Uses `LocalProvider.chat_stream` for local execution.
  - Enforces `ExecutionMode.LOCAL_ONLY` privacy checks.
  - Provides clear, observable fallback responses when the local model is offline/uninstalled.
  - Handles streaming cancellation and propagates execution exceptions without silent swallowing.

### Step 5: Update Runtimes & Architecture Guards
- Update `core/runtimes/chemistry.py` to import `_build_messages, _get_tutor_context` from `core.inference.context`.
- Update `core/runtimes/general.py` to import `_build_messages` from `core.inference.context`.
- Update `tests/architecture/test_anti_legacy_imports.py` to set `known_legacy_callers = set()` (0 allowed).

### Step 6: Comprehensive Test Suite (`tests/test_phase09_model_registry_ai_gateway.py`)
Implement full test coverage for:
1. `test_manifest_consistency_and_canonical_keys`: validates manifest fields against spec.
2. `test_missing_model_behavior`: asserts clear offline diagnostic without crashing runtime.
3. `test_wrong_model_exception`: asserts explicit error on invalid model file/id.
4. `test_corrupt_model_rejection`: asserts checksum/validation failure rejection.
5. `test_provider_timeout_handling`: verifies timeout propagation.
6. `test_provider_invalid_response_handling`: ensures invalid response raises error (no fake success).
7. `test_local_only_policy_enforcement`: blocks non-local providers when privacy mode is local_only.
8. `test_local_first_fallback_observable`: verifies fallback events are logged and observable.
9. `test_provider_selection_by_task_and_name`: verifies routing decisions.
10. `test_streaming_and_cancellation`: tests token streaming and clean stop on cancellation.
11. `test_anti_legacy_zero_callers`: verifies zero legacy callers across `core`, `central_platform`, `app`.
12. `test_prompt_template_chatml_consistency`: ensures chatml formatting matches Qwen tokenizer tokens.

---

## 4. Verification and Rollout Gate

1. **Local Test Execution**:
   - `pytest tests/test_phase09_model_registry_ai_gateway.py -v` (100% pass)
   - Full regression suite: `pytest` (all 932+ tests passing)
2. **Artifact Generation**:
   - `docs/reports/PHASE_09_TEST_REPORT.md`
   - `docs/reports/PHASE_09_TEST_RESULTS.json`
3. **Ledger Updates**:
   - `PROJECT_STATE.yaml` (Phase 09 complete, BUG-ARCH-002 & BUG-ARCH-006 marked resolved)
   - `DEVELOPMENT_LOG.md`
   - `BUG_REGISTER.md`
   - `GITHUB_SYNC_QUEUE.md`
4. **Git Operations**:
   - `git add .`
   - `git commit -m "Phase 09: Model Registry & AI Gateway Unification (BUG-ARCH-002, BUG-ARCH-006)"`
   - `git push origin master`
