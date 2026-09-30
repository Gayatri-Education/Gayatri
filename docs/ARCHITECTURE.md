# System Architecture Specification — Gayatri AI Platform

## 1. High-Level Architecture Overview

The Gayatri AI Platform follows a clean multi-layered, local-first hybrid architecture designed for extreme reliability, offline capability, strict multi-tenant data isolation, and modular persona-based UI portals.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Student UI   │  │ Teacher UI   │  │ Parent UI    │  │ Fee Admin UI │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         └─────────────────┴───────────┬─────────┴─────────────────┘     │
│                                       ▼                                 │
│                           Application Shell Controller                   │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────┐
│                            AI & PEDAGOGY LAYER                          │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │ Local-First AI Gateway │ │ Context Builder   │ │ Response Validator│  │
│  └───────────┬───────────┘ └─────────┬─────────┘ └─────────┬─────────┘  │
│              ▼                       ▼                     ▼            │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │ Local SLM (llama.cpp) │ │ Cloud Adapters    │ │ RAG Reliability   │  │
│  └───────────────────────┘ └───────────────────┘ └───────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────┐
│                        LEARNING ENGINE & STATE LAYER                    │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │ Learning Graph DAG    │ │ Mastery Engine    │ │ Next Action Engine│  │
│  └───────────┬───────────┘ └─────────┬─────────┘ └─────────┬─────────┘  │
│              ▼                       ▼                     ▼            │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │ Learning Event Store  │ │ Analytics Engine  │ │ State Commit      │  │
│  └───────────────────────┘ └───────────────────┘ └───────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────┐
│                      DATA & INFRASTRUCTURE LAYER                        │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │ Platform Database     │ │ Payment Gateways  │ │ Parent Privacy    │  │
│  │ (SQLite / Postgres)   │ │ (Razorpay / UPI)  │ │ Rules Engine      │  │
│  └───────────────────────┘ └───────────────────┘ └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

1. **Local-First & Capability-Based Fallback**:
   - Primary AI inference runs locally using an ultra-lean GGUF quantized model (`Qwen2.5-0.5B-Instruct` via `llama.cpp`).
   - Strategy-driven routing (`LOCAL_ONLY`, `LOCAL_FIRST`, `CLOUD_PREFERRED`) seamlessly falls back to cloud providers (OpenAI, Anthropic, Gemini) if local resources are unavailable or if cloud-level capabilities are requested.

2. **Deterministic Evidence-Backed Pedagogy**:
   - Neural output is never permitted to directly mutate student mastery state or decide learning steps without validation.
   - All learning state transitions are driven by deterministic algorithms evaluating student interaction events (attempt accuracy, hint penalties, time decay, prerequisite graphs).

3. **Two-Phase Atomic State Staging**:
   - Neural language model responses are passed through the `ResponseValidatorEngine` enforcing factual accuracy, curriculum alignment, anti-answer leakage, and safety.
   - Learning state updates are staged in memory and committed to the `PlatformDatabase` ONLY when validation succeeds. Failed or invalid responses trigger immediate rollback.

4. **Multi-Tenant Isolation & Privacy**:
   - Data scoping enforces zero cross-tenant data leakage.
   - Parent visibility is governed by explicit privacy policies (`FULL_TRANSPARENCY`, `SUMMARY_ONLY`, `RESTRICTED`, `BLOCKED`) managed by institution policies and student settings.

---

## 3. Subsystem Breakdown

### 3.1 AI Gateway & Context Pipeline (`central_platform/ai/`)
- **Query Understanding Engine (`query_understanding.py`)**: Structured JSON intent extraction with SLM and fallback rule-based fallback.
- **Context Builder (`context_builder.py`)**: Assembles 7 contextual layers into trimmed system/user prompts avoiding token bloat.
- **Response Planner & Validator (`response_planner.py`, `response_validator.py`)**: Generates pedagogical scaffold plans and validates candidate LLM responses against 7 educational invariants.

### 3.2 Learning Engine (`central_platform/learning/`)
- **Canonical Learning State (`state.py`)**: Persistent memory object encapsulating mastery, misconceptions, review queue, and event logs.
- **Learning Graph (`graph.py`)**: Directed Acyclic Graph (DAG) concept prerequisite manager handling cycle detection and prerequisite readiness.
- **Mastery Evidence Engine (`mastery.py`)**: Computes multi-factor mastery combining recent accuracy, long-term recall, hint penalties, attempt diminishing returns, and Ebbinghaus forgetting curve decay.
- **Next Action Engine (`actions.py`)**: Pedagogy engine determining the next action (`CONTINUE`, `EXPLAIN`, `HINT`, `REMEDIATE`, `PRACTICE`, `REVIEW`, `ASSESS`, `CHALLENGE`, `ADVANCE`).

### 3.3 Persona Portals & UI System (`app/ui/design_system/`, `central_platform/portals/`)
- **App Shell**: Shared layout with dark/light themes, collapsible sidebar, topbar, and 8-language i18n support.
- **Student Portal**: Dashboard analytics, curriculum tree, graph visualizer, spaced review queue, assignment list, and activity stream.
- **Teacher Portal**: Roster management, student health status (`EXCELLENT`, `GOOD`, `NEEDS_ATTENTION`, `AT_RISK`), intervention assignment, and AI Copilot.
- **Parent Portal**: Child selector, academic progress overview, attendance records, recommendation feed, and fee payment details.
- **Fee Admin UI**: Fee structure configuration, monthly billing batch generation, receipt printing, outstanding fee reporting, and CSV exports.

### 3.4 Data & Payment Layer (`central_platform/db.py`, `fees/`, `payments/`)
- Multi-table relational schema for core platform entities and fee management.
- SQL DDL migrations (`001`, `002`, `003`) providing automated schema upgrades.
- Decoupled payment gateway adapters (**Mock**, **Razorpay**, **UPI**) with HMAC verification and webhook handling.

---

## 4. Scalability & Resilience

- **Performance Profiling**: Built-in `PerformanceProfiler` context manager tracks latency, token throughput, query timings, and memory growth.
- **Failure Recovery Manager**: Self-healing JSON repairs, degraded execution fallbacks, and transactional rollback mechanisms.
- **Deployment Validator**: Automated 9-point deployment readiness check covering environment, secrets, database, backups, logging, health endpoints, models, static assets, and HTTPS security.
