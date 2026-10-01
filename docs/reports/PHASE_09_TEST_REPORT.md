# Phase 09 Test & Verification Report: Model Registry & AI Gateway Unification

**Document ID:** `PHASE_09_TEST_REPORT`  
**Phase:** 09  
**Parent Plan:** [GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md](../../GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md) (Section 12.9)  
**Timestamp:** 2026-10-01T22:31:30+05:30  
**Branch:** `master`  
**Status:** 100% VERIFIED  

---

## 1. Test Execution Metadata

```text
commit SHA: c3efabd
branch: master
timestamp: 2026-10-01T22:31:30+05:30
environment: Local Development / CI-equivalent
python: 3.12.10
OS: Windows 11
dependencies: llama-cpp-python, pytest-7.4.4, fastapi, pydantic, sqlalchemy
command: pytest -q
scope: Full Platform Regression + Phase 09 Test Suite
collected: 946
passed: 946
failed: 0
skipped: 0
xfailed: 0
duration: 135.53s
coverage: 100% pass on all active units and architectural guards
result: SUCCESS (100% Green)
```

---

## 2. Model & Configuration Reconciliation Report (BUG-ARCH-006)

Prior to Phase 09, `core/config.py` contained hardcoded defaults pointing to legacy Gemma weights (`gemma-2-2b-it-IQ3_M.gguf`) and legacy tutor fallback names (`Gayatri-Tutor-v3-Q4_K_M.gguf`), whereas `model_manifest.json` specified the canonical lightweight model `gayatri-chem-qwen2.5-0.5b-v4` (`qwen2.5-0.5b-instruct-q4_k_m.gguf`).

### Reconciliation Summary:
| Parameter | Pre-Phase 09 Config | Pre-Phase 09 Manifest | Reconciled Canonical State |
|:---|:---|:---|:---|
| **Model ID** | `Gayatri-Tutor-v3-Q4_K_M` | `gayatri-chem-qwen2.5-0.5b-v4` | `gayatri-chem-qwen2.5-0.5b-v4` |
| **Model Filename** | `gemma-2-2b-it-IQ3_M.gguf` | `qwen2.5-0.5b-instruct-q4_k_m.gguf` | `qwen2.5-0.5b-instruct-q4_k_m.gguf` |
| **HuggingFace Repo** | `bartowski/gemma-2-2b-it-GGUF` | `Qwen/Qwen2.5-0.5B-Instruct-GGUF` | `Qwen/Qwen2.5-0.5B-Instruct-GGUF` |
| **Chat Template** | Unspecified / hardcoded | `chatml` | `chatml` (Standardized ChatML) |
| **Quantization** | Unspecified | `Q4_K_M` | `Q4_K_M` |
| **Context Length** | 8192 | 8192 | 8192 |
| **Streaming** | Implicit | Absent | Explicit `streaming: true` |
| **Resource Profile** | Unspecified | `"1GB RAM, CPU"` | `"1GB RAM, CPU"` |

---

## 3. Legacy Decommissioning Report (BUG-ARCH-002)

All callers importing from `legacy.agents.default_agents` have been permanently eliminated from production runtime:
1. `core/inference/service.py`: Replaced `from legacy.agents.default_agents import _local_chat_stream` with direct invocation through `core.providers.local.LocalProvider.chat_stream` and `core.providers.registry.get_registry()`.
2. `core/runtimes/chemistry.py`: Replaced `from legacy.agents.default_agents import _build_messages, _get_tutor_context` with clean decoupled imports from `core.inference.context`.
3. `core/runtimes/general.py`: Replaced `from legacy.agents.default_agents import _build_messages` with import from `core.inference.context`.
4. `legacy/agents/default_agents.py`: Re-exports context helpers from `core.inference.context`, raises `DeprecationWarning`, and is scheduled for final removal in Phase 28.
5. `tests/architecture/test_anti_legacy_imports.py`: Whitelist reduced from 3 callers to **0 callers**. Automated static analysis verifies zero legacy imports across `core/`, `central_platform/`, and `app/`.

---

## 4. Provider Matrix & Routing Verification

| Provider | Type | Available in `local_only` | Available in `cloud_allowed` | Fallback Tier | Streaming | Cancellation |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `local` (GGUF / Qwen) | On-Device SLM | YES | YES | Primary (Local-First) | YES | Cooperative Flag |
| `openai` | Cloud LLM | NO (Blocked) | YES | Secondary (Tier 1/2) | YES | Yes |
| `anthropic` | Cloud LLM | NO (Blocked) | YES | Secondary (Tier 1/2) | YES | Yes |
| `google` | Cloud LLM | NO (Blocked) | YES | Secondary (Tier 1/2) | YES | Yes |
| `mock` | Simulation | YES (Testing) | YES (Testing) | Offline Fallback | YES | Instant |

---

## 5. Failure Injection & Boundary Test Results

| Test ID | Scenario | Expected Outcome | Actual Outcome | Status |
|:---|:---|:---|:---|:---:|
| **FI-01** | Missing local GGUF model artifact on disk | Clear offline user message yielded without crashing runtime | Yielded diagnostic message directing user to download weights | PASSED |
| **FI-02** | Request to unregistered provider name | `ValueError` raised immediately; no silent fallback to default | `ValueError: Requested provider 'non_existent_provider' is not registered.` | PASSED |
| **FI-03** | Corrupt model artifact with mismatched SHA-256 | `verify_model_checksum` returns `False` | Rejected corrupted binary file | PASSED |
| **FI-04** | Remote provider request timeout (30s) | `TimeoutError` raised and propagated (Rule 3) | `TimeoutError: Provider request timed out` | PASSED |
| **FI-05** | Remote provider returns malformed stream chunk | `ValueError` raised without silent absorption into fake success | `ValueError: Malformed stream chunk received` | PASSED |
| **FI-06** | Cloud provider invocation in `local_only` mode | `PermissionError` raised fail-closed | `PermissionError: Data cannot leave the device...` | PASSED |
| **FI-07** | User cancels streaming turn midway | Generation stops cooperatively at cancel point | Stream stopped after 3 tokens cleanly | PASSED |

---

## 6. Regression Verification

- **Full Suite Run:** 946 passed in 135.53s.
- **Failures:** 0.
- **Skipped:** 0.
- **Regressions:** None.
