# Security & Privacy Model — Gayatri AI Platform

## 1. Role-Based Access Control (RBAC)

The platform enforces strict role-based data boundaries across 4 core user roles:

```text
               ┌──────────────────────────────────────────────┐
               │                  ORG_ADMIN                   │
               │   (Full platform & fee administration)       │
               └──────────────────────┬───────────────────────┘
                                      │
               ┌──────────────────────┴───────────────────────┐
               │                   TEACHER                    │
               │  (Class rosters, health analytics, copilot)  │
               └──────────────────────┬───────────────────────┘
                                      │
               ┌──────────────────────┴───────────────────────┐
               │                    PARENT                    │
               │  (Child progress, fees, policy-filtered feed) │
               └──────────────────────┬───────────────────────┘
                                      │
               ┌──────────────────────┴───────────────────────┐
               │                   STUDENT                    │
               │  (Personalized learning, state, assessments)  │
               └──────────────────────────────────────────────┘
```

---

## 2. Multi-Tenant Data Isolation

- Every database query automatically injects `tenant_id = :tenant_id` filters.
- Cross-tenant data leakage is prevented at both the database DAL layer (`central_platform/db.py`) and RAG vector store query layer (`RAGService.query`).
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

## 4. Automated Security Audit Subsystem (`central_platform/security/audit.py`)

The `SecurityAuditRunner` performs automated security checks:

1. **Prompt Injection Defense (`audit_prompt_injection`)**:
   - Detects direct injection, roleplay overrides ("ignore previous instructions", "you are now DAN"), and chemical safety hazards.
2. **PII Log Sanitization (`sanitize_pii_logs`)**:
   - Automatically masks email addresses (`user@domain.com` $\rightarrow$ `u***@d***.com`) and 10-digit Indian phone numbers (`+91 9876543210` $\rightarrow$ `+91 ******3210`).
3. **Upload Filename Path Traversal Defense (`audit_upload_filename`)**:
   - Rejects directory traversal attempts (`../`, `..\\`, null bytes `%00`).
4. **Payment HMAC Verification (`RazorpayPaymentAdapter`)**:
   - Verifies Razorpay payment signatures using HMAC-SHA256 (`razorpay_order_id|razorpay_payment_id`).
