# Data Model & Schema Specification — Gayatri AI Platform

## 1. Overview

The Gayatri AI Platform data model is structured around a central relational database schema (`gayatri_local.db` in SQLite, migration-ready for PostgreSQL) paired with canonical Python dataclasses in `central_platform/models/`.

---

## 2. Core Relational Schema

### 2.1 Identity & Tenant Tables
- **`users`**: Platform user accounts.
  - `user_id` (TEXT PRIMARY KEY), `tenant_id` (TEXT), `email` (TEXT), `name` (TEXT), `role` (TEXT), `created_at` (TIMESTAMP).
- **`institutions`**: Organizational hierarchy.
  - `institution_id` (TEXT PRIMARY KEY), `name` (TEXT), `code` (TEXT).

### 2.2 Curriculum & Learning Tables
- **`curricula`**: Multi-board curriculum definitions.
  - `curriculum_id` (TEXT PRIMARY KEY), `tenant_id` (TEXT), `title` (TEXT), `board` (TEXT), `grade_level` (INTEGER), `subject` (TEXT), `metadata` (JSON).
- **`student_learning_records`**: Consolidated student learning state.
  - `student_id` (TEXT PRIMARY KEY), `tenant_id` (TEXT), `mastery_data` (JSON), `misconceptions` (JSON), `updated_at` (TIMESTAMP).
- **`learning_events`**: Append-only event store.
  - `event_id` (TEXT PRIMARY KEY), `student_id` (TEXT), `event_type` (TEXT), `concept_id` (TEXT), `payload` (JSON), `timestamp` (TIMESTAMP).

### 2.3 Fee Management Tables (`migrations/003_fee_management_schema.sql`)
- **`fee_structures`**: Defined fee items and default amounts.
  - `structure_id` (TEXT PRIMARY KEY), `tenant_id` (TEXT), `name` (TEXT), `frequency` (TEXT), `amount` (DECIMAL), `due_day` (INTEGER).
- **`fee_plans`**: Student billing assignment plans.
  - `plan_id` (TEXT PRIMARY KEY), `tenant_id` (TEXT), `name` (TEXT), `total_annual_amount` (DECIMAL).
- **`fee_accounts`**: Financial ledger per student.
  - `account_id` (TEXT PRIMARY KEY), `student_id` (TEXT), `tenant_id` (TEXT), `balance_due` (DECIMAL), `total_billed` (DECIMAL), `total_paid` (DECIMAL).
- **`invoices`**: Generated monthly billing invoices.
  - `invoice_id` (TEXT PRIMARY KEY), `account_id` (TEXT), `student_id` (TEXT), `amount_due` (DECIMAL), `status` (TEXT), `due_date` (TEXT).
- **`payments`**: Transaction records.
  - `payment_id` (TEXT PRIMARY KEY), `invoice_id` (TEXT), `amount` (DECIMAL), `method` (TEXT), `status` (TEXT), `transaction_ref` (TEXT).
- **`receipts`**: Official payment receipts.
  - `receipt_id` (TEXT PRIMARY KEY), `payment_id` (TEXT), `receipt_number` (TEXT), `issued_at` (TIMESTAMP).
- **`discounts`**: Financial aid and scholarship adjustments.
  - `discount_id` (TEXT PRIMARY KEY), `account_id` (TEXT), `amount` (DECIMAL), `reason` (TEXT).
- **`refunds`**: Payment reversal records.
  - `refund_id` (TEXT PRIMARY KEY), `payment_id` (TEXT), `amount` (DECIMAL), `status` (TEXT).

---

## 3. Python Dataclass Specifications

### 3.1 `CanonicalLearningState` (`central_platform/learning/state.py`)
```python
@dataclass
class CanonicalLearningState:
    student_id: str
    tenant_id: str
    concept_mastery: Dict[str, float]
    concept_confidence: Dict[str, float]
    misconceptions: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
    due_reviews: List[str]
    active_teacher_instructions: List[str]
    last_updated: str
```

### 3.2 `StudentHealthMetric` (`central_platform/analytics/engine.py`)
```python
@dataclass
class StudentHealthMetric:
    student_id: str
    name: str
    overall_mastery: float
    health_level: LearningHealthLevel  # EXCELLENT, GOOD, NEEDS_ATTENTION, AT_RISK
    misconception_count: int
    due_review_count: int
    last_active: str
```

### 3.3 `PedagogicalResponsePlan` (`central_platform/ai/response_planner.py`)
```python
@dataclass
class PedagogicalResponsePlan:
    action_type: NextActionType
    learning_objective: str
    scaffolding_steps: List[str]
    tone_guidance: str
    anti_answer_leakage: bool
    requires_rag_citations: bool
```
