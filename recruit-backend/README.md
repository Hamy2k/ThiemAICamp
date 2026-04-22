# Recruit Backend

AI-powered job distribution backend for blue-collar hiring in Vietnam.
Implements the Phase 1 system design (with validation patches P1–P4 applied).

**Phase 2 scope:** Python + FastAPI backend only. No frontend, no Docker, no CI.

## Stack

| Layer | Tool |
|---|---|
| Web | FastAPI 0.115+ |
| DB | PostgreSQL 15 (asyncpg + SQLAlchemy 2.0 async) |
| Migrations | Alembic |
| LLM | Anthropic SDK (Claude Sonnet 4.6 + Haiku 4.5) |
| Notifications | Telegram Bot API (httpx) |
| Validation | pydantic v2 |
| Tests | pytest + pytest-asyncio |

## Prerequisites

- Python **3.11+** (Phase 2 spec requires 3.11; your local `python --version` must satisfy)
- PostgreSQL 15+ running locally (or use Neon for dev)
- Anthropic API key

## Install & run — 3 commands

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Copy env, apply migrations
cp .env.example .env && alembic upgrade head

# 3. Start API
uvicorn app.main:app --reload
```

The API listens on http://localhost:8000. Interactive docs: http://localhost:8000/docs.

## Environment variables

Every env var is documented in `.env.example`. Critical ones:

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Async Postgres URL, must use `asyncpg` driver |
| `ANTHROPIC_API_KEY` | Claude API key |
| `AI_GATEWAY_BASE_URL` | (optional) Vercel AI Gateway base URL — route through gateway for cost tracking & failover |
| `MODEL_JOB_POST` / `MODEL_SCREENING` / `MODEL_SCORING` | Claude model IDs |
| `TELEGRAM_BOT_TOKEN` | Bot token for HR notifications |
| `CLAUDE_TIMEOUT_SECONDS` | Per-call timeout (default 10s) |
| `CLAUDE_RETRY_COUNT` | Retries on 5xx/timeout (default 1) |
| `CLAUDE_RETRY_BACKOFF_MS` | Backoff between retries (default 500ms) |

## Tests

### Unit tests (no DB / no API keys needed)

```bash
pytest tests/unit -v
```

Covers:
- `tests/unit/test_phone.py` — edge case 6 (phone E.164)
- `tests/unit/test_vietnamese.py` — edge case 5 (accent normalization)
- `tests/unit/test_scoring.py` — deterministic rubric + fallback
- `tests/unit/test_fallback_parser.py` — rule-based message parsing

### Integration tests (need Postgres)

```bash
# Point to a throwaway DB — will be TRUNCATE'd between tests
createdb recruit_test
TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/recruit_test" \
  pytest tests/integration -v
```

Covers all 6 edge cases from Phase 1 spec:

| # | Edge case | Test |
|---|---|---|
| 1 | Duplicate phone → merge | `test_duplicate_phone_merges_history` |
| 2 | Abandoned chat → partial saved | `test_partial_screening_saved` |
| 3 | Multiple matches → top notified | `test_top_match_sent_to_hr` |
| 4 | Unrealistic salary → warn, don't block | `test_salary_warning_does_not_block` |
| 5 | Non-accent Vietnamese → normalize | `test_accent_normalization` |
| 6 | Phone formats → E.164 | `test_phone_format_stored_as_e164` |

### Coverage

```bash
pytest --cov=app.services --cov=app.ai tests/
```

## Project structure

```
backend/
├── alembic/
│   ├── env.py                  # Async migration runner
│   └── versions/
│       └── 0001_initial_schema.py  # All 15 tables + triggers + pdpd_delete_lead
├── app/
│   ├── main.py                 # FastAPI factory
│   ├── config.py               # pydantic Settings
│   ├── db/
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── session.py          # Async engine + get_db()
│   │   └── models/             # Domain-grouped ORM (7 files, 15 tables)
│   ├── schemas/                # pydantic v2 request/response
│   ├── api/
│   │   ├── deps.py             # Auth, request-id, error envelope
│   │   └── v1/
│   │       ├── jobs.py         # POST/PATCH /hr/jobs, /generate-content
│   │       ├── leads.py        # POST /leads (consent + dedupe + tracking)
│   │       ├── screening.py    # POST /screening/{message,complete}
│   │       ├── tracking.py     # /hr/sources, /hr/jobs/:id/tracking-links, GET /j/:tid
│   │       ├── analytics.py    # /hr/analytics/{sources,variants}
│   │       └── health.py
│   ├── services/
│   │   ├── scoring.py          # Deterministic rubric + haversine + weights
│   │   ├── matching.py         # Top match for job
│   │   ├── notification.py     # Telegram sender (httpx)
│   │   └── gazetteer.py        # VN district centroids
│   ├── ai/
│   │   ├── client.py           # Claude wrapper: retry + cost tracking
│   │   ├── job_generator.py    # Sonnet: 5 variants per call
│   │   ├── screener.py         # Haiku turn-by-turn + fallback
│   │   ├── scorer.py           # Haiku structured output + fallback
│   │   ├── fallback_parser.py  # Rule-based parser (when Claude fails)
│   │   └── prompts/            # Vietnamese .txt templates (loaded at runtime)
│   └── utils/
│       ├── phone.py            # E.164 via phonenumbers
│       ├── vietnamese.py       # NFC + strip_accents + landmarks
│       ├── idempotency.py      # In-memory TTL store (replace w/ Redis in prod)
│       └── logging.py          # JSON logs to stdout
├── tests/
│   ├── conftest.py             # DB + httpx fixtures
│   ├── unit/                   # No external deps
│   └── integration/            # Real DB
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## Endpoints

All under `/v1/` prefix.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | public | Liveness + DB ping |
| POST | `/hr/jobs` | HR bearer | Create draft job |
| POST | `/hr/jobs/{id}/generate-content` | HR bearer | Sonnet: 5 variants |
| PATCH | `/hr/jobs/{id}` | HR bearer | Publish / close |
| POST | `/hr/sources` | HR bearer | Register distribution source |
| POST | `/hr/jobs/{id}/tracking-links` | HR bearer | Create tracking URL |
| GET | `/j/{tracking_id}` | public | Landing (logs click → trigger bumps) |
| POST | `/leads` | public + CSRF (Phase 3) | Submit 3-field form |
| POST | `/screening/message` | cookie (Phase 3) | Screening turn |
| POST | `/screening/complete` | cookie (Phase 3) | Finalize + score + notify HR |
| DELETE | `/leads/{id}` | scoped | PDPD right-to-deletion |
| GET | `/hr/analytics/sources` | HR bearer | Leads per source |
| GET | `/hr/analytics/variants` | HR bearer | Conversion per variant |

## AI cost budget tracking

Every Claude call persists to `ai_calls`. Daily cost query:

```sql
SELECT DATE(created_at) AS d, call_site,
       SUM(cost_usd)::numeric(10,2) AS spend,
       COUNT(*) AS calls
FROM ai_calls
GROUP BY 1, 2 ORDER BY 1 DESC;
```

Phase 1 budget: **$0.01 / qualified lead**. Design estimated $0.0089. Monitor via query above.

## PII at rest — encryption approach

**Not implemented in application code.** Rely on:
1. **Managed Postgres (Neon / RDS / etc.) with encryption-at-rest enabled** — free on most tiers.
2. **Column-level encryption** (optional Phase 3): use `pgcrypto`'s `pgp_sym_encrypt` on `leads.phone_raw`, `leads.full_name`, `leads.area_raw`, `consent_records.ip_address`. Key lives in KMS / Vault, rotated quarterly.
3. **TLS 1.2+ to DB** — enforced in connection string (`sslmode=require`).
4. **Redaction on deletion** — `pdpd_delete_lead()` stored proc (Phase 1 patch P2) replaces PII with sentinels.

## SPEC_CONFLICT / deviations from Phase 2 brief

1. **"One file per table"** — pragmatic group of 15 tables into 7 domain-files in `app/db/models/`. All tables still visible in `Base.metadata`.
2. **Python 3.10 vs 3.11+** — spec requires 3.11+. Local `python --version` on dev machine here is 3.10. Upgrade before running.
3. **Python SDK vs Phase 1's Next.js choice** — Phase 1 proposed Next.js; Phase 2 spec mandates Python/FastAPI. Backend honors Phase 2 mandate.
4. **Rate limit** — in-process lock file for MVP only. Production must swap to Redis (see `app/utils/idempotency.py`).
5. **Session cookie / CSRF for worker endpoints** — Phase 1 specified these, but full cookie/CSRF wiring defers to Phase 3 (frontend integration). MVP treats `/leads`, `/screening/*` as unauthenticated but idempotent.

## Next phases

- **Phase 3**: Frontend (worker landing page + HR dashboard).
- **Phase 4**: Dockerfile, CI/CD, production secrets.
- **v0.2**: Semantic matching (embeddings), Facebook auto-post, Zalo OA.
