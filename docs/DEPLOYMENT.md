# Deployment & Operations Manual — Gayatri AI Platform

## 1. Deployment Overview

The Gayatri AI Platform supports dual deployment modes:
1. **Local Edge Mode**: Desktop / On-premise deployment utilizing CPU-optimized GGUF local model inference (`llama.cpp`) and local SQLite database (`gayatri_local.db`).
2. **Enterprise Cloud Mode**: Dockerized production deployment connecting to PostgreSQL, cloud model providers (OpenAI, Anthropic, Gemini), and Razorpay/UPI payment gateways.

---

## 2. Environment Configuration & Variables

Key environment variables in `.env`:

```env
# Application Setup
APP_ENV=production
PORT=8000
LOG_LEVEL=INFO
FORCE_HTTPS=true

# Security Secrets
SECRET_KEY=your_secure_random_64_character_hex_secret_key_here
JWT_SECRET=your_jwt_signing_secret_here

# Database Configuration
DATABASE_URL=sqlite:///gayatri_local.db
# For PostgreSQL: postgresql://user:password@localhost:5432/gayatri_prod

# Local Model Setup
LOCAL_MODEL_PATH=models/qwen2.5-0.5b-instruct-q4_k_m.gguf
MODEL_MANIFEST_PATH=model_manifest.json

# Optional Cloud Providers
AI_PROVIDER=local_first
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Payment Gateway Configuration
PAYMENT_GATEWAY_PROVIDER=razorpay
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

---

## 3. Database Migration Execution

Run database DDL migrations sequentially:

```bash
# SQLite / PostgreSQL Migration Command
python -m central_platform.db migrate
```

Migration scripts located in `migrations/`:
- `001_initial_schema.sql`: Users, curricula, learning records.
- `002_curriculum_abstraction.sql`: Curriculum board abstractions and metadata.
- `003_fee_management_schema.sql`: Fee structures, invoices, payments, receipts, discounts.

---

## 4. Automated Deployment Validator Usage

Before launching or deploying the application, execute the `DeploymentValidator`:

```python
from central_platform.deployment.validator import DeploymentValidator

validator = DeploymentValidator()
report = validator.run_full_validation()

print(report.summary)
if not report.is_ready:
    for result in report.results:
        if result.status.value == "FAIL":
            print(f"FAILED CHECK: {result.check_name} - {result.message}")
```

Or via CLI command:

```bash
python -c "from central_platform.deployment.validator import DeploymentValidator; print(DeploymentValidator().run_full_validation().summary)"
```

The validator automatically verifies:
1. Environment configuration
2. Secret key strength
3. Database connection & migration tables
4. Backup directory write access
5. Log storage readiness
6. Core service health endpoints (`/health`)
7. Model manifest & local model binary availability
8. All 16 static UI asset CSS/JS files
9. HTTPS security transport settings
