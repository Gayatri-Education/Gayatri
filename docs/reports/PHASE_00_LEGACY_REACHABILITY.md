# Phase 00 — Legacy Reachability & Decommissioning Audit

**Document:** `docs/reports/PHASE_00_LEGACY_REACHABILITY.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Inspection Date:** 2026-10-01  
**Commit SHA:** `bf47a63`  

---

## 1. Executive Summary

Static reachability analysis confirmed that despite the presence of modern AI Gateway abstractions in `central_platform/ai/`, active production inference paths in `core/` continue to import directly from `legacy.agents.default_agents`.

Per **Section 2.2** of the Execution Contract, zero active production paths may import `legacy`.

---

## 2. Active Legacy Import Registry

| Active Production Module | Line Number | Imported Legacy Symbol | Purpose |
|---|---|---|---|
| `core/inference/service.py` | 40 | `from legacy.agents.default_agents import _local_chat_stream` | Streaming token generation for local SLM |
| `core/runtimes/chemistry.py` | 115 | `from legacy.agents.default_agents import _build_messages, _get_tutor_context` | System prompt assembly & session context |
| `core/runtimes/general.py` | 68 | `from legacy.agents.default_agents import _build_messages` | Socratic conversation prompt formatting |

---

## 3. End-to-End Runtime Reachability Proof

```text
User Submits Question in Desktop App
    ↓
app/bridge/facade.py:send_message()
    ↓
core/orchestrator.py:handle_user_turn()
    ↓
core/runtimes/chemistry.py:execute_turn()
    ├── [REACHED] legacy.agents.default_agents._get_tutor_context()
    └── [REACHED] legacy.agents.default_agents._build_messages()
    ↓
core/inference/service.py:stream_chat()
    ↓
[REACHED] legacy.agents.default_agents._local_chat_stream()
    ↓
Local llama.cpp inference execution
```

**Finding:** Any chat initiated via the desktop application executes code inside `legacy/`.

---

## 4. Decommissioning & Removal Plan (Phase 8 & Phase 20)

1. **Phase 8 (AI Gateway Unification):**
   - Re-route `core/inference/service.py` to invoke `central_platform.ai.model_router.AIModelRouter`.
   - Replace `_build_messages` and `_get_tutor_context` calls with `central_platform.ai.context_builder.ContextBuilderEngine`.
2. **Phase 20 (Legacy Removal):**
   - Verify 0 occurrences of `legacy.` via automated static grep check across `core/`, `central_platform/`, and `app/`.
   - Delete `legacy/` directory completely.
   - Enforce permanent CI guard failing builds if `legacy` is reintroduced.
