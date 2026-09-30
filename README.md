# Gayatri AI Platform — Next-Generation Adaptive Education Platform

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build & Tests](https://img.shields.io/badge/tests-845%20passed-brightgreen.svg)]()
[![Platform Version](https://img.shields.io/badge/platform-v4.0.0-purple.svg)]()

**Gayatri AI Platform** is an enterprise-grade, evidence-driven, NCERT & multi-curriculum aligned adaptive learning platform. It integrates local-first Small Language Models (SLMs), multi-cloud AI provider routing, concept-aware RAG, deterministic evidence-backed mastery tracking, multi-persona UI portals (Student, Teacher, Parent, Fee Administration), payment provider abstractions, and real-time learning analytics.

---

## 🚀 Key Capabilities & Architecture Overview

```text
                                GAYATRI AI PLATFORM
                                         │
       ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
       ▼                   ▼                           ▼                   ▼
  Student Portal     Teacher Portal              Parent Portal       Fee Admin UI
  (Learner Hub)      (Class Roster & Copilot)   (Privacy & Feed)    (Billing & Payments)
       │                   │                           │                   │
       └───────────────────┴─────────────┬─────────────┴───────────────────┘
                                         │
                                         ▼
                            Unified Application Shell
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ▼                                 ▼                                 ▼
 AI Gateway Router             Canonical Learning State            Fee & Payment Subsystem
 (Local SLM + Cloud Fallbacks)  (Learning Graph & Mastery)         (Razorpay, UPI, Mock)
       │                                 │                                 │
       ▼                                 ▼                                 ▼
 RAG Reliability Service        State Commit Pipeline              Parent Privacy Rules
 (Hybrid Retrieval & Provenance) (Two-Phase Commit Isolation)       (Data Visibility Boundary)
```

### 1. Multi-Persona UI Shell & Portal System (`app/ui/design_system/`)
- Shared Design System supporting **Dark Theme** (default) and **Light Theme**.
- Collapsible Application Shell supporting 8 languages (**English, Hindi, Sanskrit, Tamil, Telugu, Kannada, Marathi, Bengali**).
- **Student Portal**: Dashboard analytics, curriculum tree, learning graph DAG visualization, spaced review queue, assignment management, and activity stream.
- **Teacher Portal**: Class overview, student health metrics (`EXCELLENT`, `GOOD`, `NEEDS_ATTENTION`, `AT_RISK`), student profiles, pedagogical intervention authoring, and AI Copilot.
- **Parent Portal**: Multi-child switcher, progress summary, attendance records, recommendation feed, and fee payment summaries.
- **Fee Admin UI**: Monthly batch billing generation, student fee accounts, receipt issuance, outstanding fee reporting, and CSV exports.

### 2. Local-First AI Gateway & Model Router (`central_platform/ai/`)
- Dual-tier routing strategy (`LOCAL_ONLY`, `LOCAL_FIRST`, `CLOUD_PREFERRED`).
- Integrated local GGUF model execution (`llama.cpp` CPU-optimized) and cloud provider adapters (**OpenAI**, **Anthropic**, **Gemini**, **OpenRouter**).
- **Structured Query Understanding**: Dynamic intent classification, concept parsing, and prompt-injection defense.
- **Context Builder**: 7-layer context assembly (Conversation, Learner State, Curriculum, Teacher Instructions, Institution Policy, RAG evidence, Recent Events).
- **Response Validator & Pedagogical Planner**: Factual verification, anti-answer leakage flags, LaTeX math verification, and self-healing automated fallback.

### 3. Canonical Learning Engine & Graph (`central_platform/learning/`)
- **Canonical Learning State**: Unified memory layer replacing legacy disjoint dictionaries.
- **Learning Event Store**: Append-only idempotent log of 20 canonical learning event types.
- **Learning Graph Engine**: Recursive prerequisite DAG traversal, cycle detection, and concept node states.
- **Evidence-Backed Mastery Engine**: Accuracy scoring, hint penalties, attempt diminishing returns, Ebbinghaus time decay, and prerequisite propagation.
- **Next Action Engine**: Pedagogical decision rules selecting across 9 actions (`CONTINUE`, `EXPLAIN`, `HINT`, `REMEDIATE`, `PRACTICE`, `REVIEW`, `ASSESS`, `CHALLENGE`, `ADVANCE`).
- **State Commit Pipeline**: Two-phase state staging and atomic database transaction commit contingent on validation success.

### 4. Fee & Payment Subsystem (`central_platform/fees/` & `central_platform/payments/`)
- SQL DDL migration schema (`003_fee_management_schema.sql`) for fee structures, accounts, invoices, payments, receipts, discounts, and refunds.
- Abstract Payment Gateway Adapter supporting **Mock Adapter**, **Razorpay Adapter** (with HMAC signature verification), and **UPI Adapter** (`upi://pay` URI formatting).

### 5. Privacy, Security & Resilience (`central_platform/privacy/`, `security/`, `recovery/`)
- **Parent Privacy Engine**: 4 policy levels (`FULL_TRANSPARENCY`, `SUMMARY_ONLY`, `RESTRICTED`, `BLOCKED`) governing student data visibility.
- **Security Audit Runner**: Automated PII masking (emails & phone numbers), prompt-injection scanning, filename path traversal checks, and tenant isolation verification.
- **Failure Recovery Manager**: Degradation policies, self-healing JSON repair, RAG fallback, and payment rollback handling.
- **Performance Profiler**: Latency context manager, memory growth measurement, token throughput calculation, and p95 bottleneck detection.
- **Deployment Validator**: 9 automated infrastructure validation checks (environment, secrets, migrations, backups, logging, health endpoints, models, static assets, HTTPS).

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+
- Git

### Quickstart

```bash
# Clone the repository
git clone https://github.com/Gayatri-Education/Gayatri.git
cd Gayatri

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## 🧪 Running Tests

Execute the full regression test suite (845 tests):

```bash
python -m pytest --tb=short -q
```

Run specific subsystem test modules:

```bash
python -m pytest tests/test_phase39_full_regression_master.py
python -m pytest tests/test_phase40_performance.py
python -m pytest tests/test_phase41_deployment_validation.py
```

---

## 📊 Platform Progress Matrix

All 43 Master Plan phases have been fully implemented, verified, documented, and tested.

| Phase Range | Subsystem | Status | Tests Passed |
|---|---|---|---|
| **Phase 00 – 05** | Baseline, Audits, Model Manifest, Demo Isolation | `COMPLETE` | 664 / 664 |
| **Phase 06 – 10** | Identity, Hierarchy, RBAC, Curriculum Plugins | `COMPLETE` | 675 / 675 |
| **Phase 11 – 15** | Canonical State, Events, Learning Graph, Mastery, Next Action | `COMPLETE` | 700 / 700 |
| **Phase 16 – 20** | Query Understanding, Context Builder, Planner, Validator, State Commit | `COMPLETE` | 727 / 727 |
| **Phase 21 – 23** | Local-First Router, Cloud Providers, RAG Reliability | `COMPLETE` | 746 / 746 |
| **Phase 24 – 29** | Shared UI, App Shell, Tutor UI, Student, Teacher, Parent Portals | `COMPLETE` | 782 / 782 |
| **Phase 30 – 33** | Fee Data Layer, Fee Admin UI, Payment Adapters, i18n (8 Languages) | `COMPLETE` | 800 / 800 |
| **Phase 34 – 38** | Parent Privacy, Analytics, Explainability, Security Audit, Failure Recovery | `COMPLETE` | 827 / 827 |
| **Phase 39 – 41** | Full Regression Master, Performance Profiler, Deployment Validation | `COMPLETE` | 845 / 845 |
| **Phase 42 – 43** | Documentation Completion & Production Readiness Gate | `COMPLETE` | 845 / 845 |

---

## 📄 Documentation Sitemap

Full system documentation is located in the `docs/` directory:

- [System Architecture](docs/ARCHITECTURE.md)
- [Data Model & Database Schema](docs/DATA_MODEL.md)
- [Learning Graph & Mastery Engine](docs/LEARNING_GRAPH.md)
- [UI/UX & Design System](docs/UI_UX_SYSTEM.md)
- [Security & Privacy Model](docs/SECURITY_MODEL.md)
- [Testing Strategy & Backtesting](docs/TESTING_STRATEGY.md)
- [Deployment & Operations Guide](docs/DEPLOYMENT.md)

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
