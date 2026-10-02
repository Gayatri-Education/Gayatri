# Security & Privacy Model — Gayatri AI Platform

## 1. Role-Based Access Control (RBAC)

The Gayatri AI Platform enforces strict role-based data boundaries across 6 explicit user roles:

```text
               ┌────────────────────────────────────────────────────────┐
               │                      SUPER_ADMIN                       │
               │   (Global platform management, cross-tenant auditing)  │
               └───────────────────────────┬────────────────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │                       ORG_ADMIN                        │
               │  (Institution administration, course approvals, fees)  │
               └───────────────────────────┬────────────────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │                        TEACHER                         │
               │ (Course drafting, class rosters, instructions, copilot)│
               └───────────────────────────┬────────────────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │                        STUDENT                         │
               │  (Personalized learning, 16-step turns, assessments)   │
               └───────────────────────────┬────────────────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │                         PARENT                         │
               │ (Child progress, fees, policy-filtered recommendation) │
               └───────────────────────────┬────────────────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │                         GUEST                          │
               │  (Unauthenticated public course exploration - STUDENT) │
               └────────────────────────────────────────────────────────┘
```

### Role Permissions Matrix

| Capability | SUPER_ADMIN | ORG_ADMIN | TEACHER | STUDENT | PARENT | GUEST |
|---|---|---|---|---|---|---|
| View Public Courses | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Org-Private Courses | ✅ | ✅ | ✅ | ✅ (Enrolled) | ❌ | ❌ |
| Create / Edit Courses | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Approve / Publish Courses | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Author Teacher Instructions | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ingest RAG Knowledge Sources | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Publish / Delete RAG Sources | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Execute Tutor Turn | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Submit Assessment Answers | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Review Assessment Submissions | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Fee Structures & Billing | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Pay Student Invoices | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 2. Multi-Tenant Data Isolation

- Every database query automatically injects `tenant_id = :tenant_id` filters.
- Cross-tenant data leakage is prevented at both the database DAL layer (`central_platform/db.py`) and RAG vector store query layer (`RAGService.query`).
- Cross-tenant requests produce immediate `403 Forbidden` responses.
- Soft-deleted entities (`is_deleted = 1`) are automatically excluded from active queries.

---

## 3. Parent Privacy & Visibility Subsystem (`central_platform/privacy/policies.py`)

Parent access to student data is governed by 4 explicit visibility levels:

| Policy Level | Chat History Access | Assessment Answers Access | Teacher Notes Access | Financials Access |
|---|---|---|---|---|
| `FULL_TRANSPARENCY` | Full transcript | Complete answers & metrics | Viewable | Viewable |
| `SUMMARY_ONLY` | High-level summary | Score percentage only | Viewable | Viewable |
| `RESTRICTED` | Hidden | Score percentage only | Hidden | Viewable |
| `BLOCKED` | Hidden | Hidden | Hidden | Hidden |

The `PrivacyRulesEngine` filters student telemetry payloads before returning responses to parent UI clients.

---

## 4. Automated Security Audit Subsystem (`central_platform/security/auditor.py`)

The `SecurityAuditor` performs automated security checks:

1. **Prompt Injection Defense (`sanitize_prompt`)**:
   - Detects direct injection, roleplay overrides ("ignore previous instructions", "you are now DAN"), system prompt leaks, and hazardous subject requests.
   - Screened at Step 4 of the 16-step orchestrator turn. Flagged queries are halted and returned as safe pedagogical redirections.
2. **PII Log Sanitization (`sanitize_pii_logs`)**:
   - Automatically masks email addresses (`user@domain.com` $\rightarrow$ `u***@d***.com`) and phone numbers (`+91 9876543210` $\rightarrow$ `+91 ******3210`).
3. **Upload Filename Path Traversal Defense (`audit_upload_filename`)**:
   - Rejects directory traversal attempts (`../`, `..\\`, null bytes `%00`).
4. **Payment HMAC Verification (`RazorpayPaymentAdapter`)**:
   - Verifies Razorpay payment signatures using HMAC-SHA256 (`razorpay_order_id|razorpay_payment_id`).
5. **Local Device Quarantine**:
   - Local course caches and RAG indices are verified against SHA-256 signatures before mounting. Tampered files are instantly moved to an isolated `.quarantine/` directory.

---

## 5. Security Hardening (Phase 22 Audit Findings & Fixes)

During Phase 22, a thorough security audit uncovered and permanently resolved several critical authorization vulnerabilities:

- **Unauthenticated Course Listing Demotion**: Fixed a bug where unauthenticated users were assigned `SUPER_ADMIN` guest context; now correctly demoted to `STUDENT` guest context, preventing exposure of private courses.
- **Course Review Queue Authorization**: The review queue endpoint now requires strict authentication (`401 Unauthorized`) and `ORG_ADMIN` or `SUPER_ADMIN` privileges (`403 Forbidden` for teachers or students).
- **Turn Sanitization**: Integrated prompt-injection sanitization directly into `/api/v1/tutor/turn` before forwarding queries to the AI Gateway.
- **RAG Write RBAC**: Added strict RBAC decorators across all knowledge ingestion and source management endpoints (ingestion requires `TEACHER+`, publishing and deletion require `ORG_ADMIN+`).
