# Gayatri AI Platform: Production Deployment & Operations Guide (Phase 27)

## Overview
This document specifies the deployment architecture, configuration parameters, monitoring stack, and incident response procedures for production operation of the Gayatri AI Educational Platform.

## 1. System Requirements & Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `GAYATRI_ENV` | string | `production` | Deployment environment (`production`, `staging`, `development`) |
| `GAYATRI_PORT` | integer | `8000` | HTTP listening port for ASGI FastAPI gateway |
| `GAYATRI_DB_PATH` | string | `data/gayatri_platform.db` | Path to persistent SQLite or PostgreSQL URI (`postgresql://user:pass@host/db`) |
| `GAYATRI_JWT_SECRET` | string | `[CRYPTO_RANDOM]` | High-entropy secret for HMAC-SHA256 token signing |
| `OPENAI_API_KEY` | string | - | Primary cloud LLM provider API token |
| `GEMINI_API_KEY` | string | - | Secondary cloud LLM provider API token |
| `GAYATRI_DAILY_BUDGET_USD` | float | `100.0` | Global daily AI expenditure ceiling |

## 2. Health & Observability Probes
- **Liveness Probe**: `GET /livez` - returns `{ "alive": true }` (200 OK)
- **Readiness Probe**: `GET /readyz` - verifies database and model readiness `{ "ready": true }` (200 OK)
- **Comprehensive Health**: `GET /healthz` - inspects DB connection, AI provider states, and uptime metrics (200 OK)
- **System Metrics**: `GET /api/v1/analytics/system` - telemetry on DAU, token usage, latency percentiles, and costs

## 3. Production Deployment Architecture
```text
                    [ Internet / Clients (Desktop & Web) ]
                                    │
                                    ▼
                         [ Reverse Proxy (Nginx) ]
                       SSL Termination / Rate Limit
                                    │
                                    ▼
                    [ FastAPI Gateway (Uvicorn Workers) ]
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                      ▼
    [ PostgreSQL / SQLite ]   [ Local GGUF SLM ]    [ Cloud AI Gateway ]
     Authoritative SLR & DB     Offline Fallback      OpenAI / Gemini / Anthropic
```

## 4. Incident Response & Triage Runbook
1. **AI Provider Outage**: Check `GET /api/v1/ai/status`. Gateway automatically switches to Local SLM / fallback providers.
2. **Emergency Kill Switch**: To immediately halt all outgoing LLM calls without restarting the application:
   `POST /api/v1/admin/kill-switch?active=true&reason=incident_triage`
3. **Database Corrupt / Lock**: Refer to `docs/operations/backup-and-restore.md` to restore the latest verified snapshot.
