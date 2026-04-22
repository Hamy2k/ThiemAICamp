# Environment variable matrix

Every env var read by either project, which platform sets it, and an example.

## Legend

- **Scope**: `backend` (Railway) · `frontend` (Vercel) · `local` (dev only) · `db` (DB-only secret)
- **Required**: ✅ yes · ⚠️ optional but recommended · – not required

## Backend (Railway — set in project → Variables)

| Name | Scope | Example | Required | Description |
|---|---|---|---|---|
| `DATABASE_URL` | backend | `postgresql+asyncpg://user:pass@host.railway.internal:5432/railway` | ✅ | Auto-injected by Railway when Postgres addon linked. **Must** prefix with `postgresql+asyncpg://` for async driver — use Railway variable reference (see `DEPLOY.md`). |
| `ANTHROPIC_API_KEY` | backend | `sk-ant-api03-…` | ✅ | Generate at console.anthropic.com → API Keys. Start with a scoped key for MVP. |
| `MODEL_JOB_POST` | backend | `claude-sonnet-4-6` | ⚠️ | Default in code. Override only to pin a specific revision. |
| `MODEL_SCREENING` | backend | `claude-haiku-4-5-20251001` | ⚠️ | Same. |
| `MODEL_SCORING` | backend | `claude-haiku-4-5-20251001` | ⚠️ | Same. |
| `TELEGRAM_BOT_TOKEN` | backend | `123456:ABC-DEF…` | ✅ | From @BotFather (see `TELEGRAM_SETUP.md`). Required for HR notifications. |
| `TELEGRAM_WEBHOOK_SECRET` | backend | `<32-char random hex>` | ⚠️ | Only needed if you set a Telegram webhook pointing back at the bot. Phase 4 MVP uses polling from HR's side. |
| `CORS_ORIGINS` | backend | `https://careers.example.vn,https://recruit-frontend.vercel.app` | ✅ | Comma-separated. Must include production Vercel domain + custom domain. |
| `APP_ENV` | backend | `production` | ⚠️ | Used by log formatting and Sentry environment tag. |
| `LOG_LEVEL` | backend | `INFO` | ⚠️ | `INFO` in prod, `DEBUG` in dev. |
| `CLAUDE_TIMEOUT_SECONDS` | backend | `10` | ⚠️ | Per Phase 2 constraint (≤10s). |
| `CLAUDE_RETRY_COUNT` | backend | `1` | ⚠️ | 1 retry on 5xx/timeout (Phase 2 contract). |
| `CLAUDE_RETRY_BACKOFF_MS` | backend | `500` | ⚠️ | Retry backoff. |
| `TELEGRAM_TIMEOUT_SECONDS` | backend | `5` | ⚠️ | Per Phase 2 constraint. |
| `IDEMPOTENCY_WINDOW_SECONDS` | backend | `600` | ⚠️ | Dedupe window for `/v1/leads`. |
| `RATE_LIMIT_IP_PER_10MIN` | backend | `5` | ⚠️ | |
| `RATE_LIMIT_PHONE_PER_HOUR` | backend | `3` | ⚠️ | |
| `SENTRY_DSN` | backend | `https://…@o123.ingest.sentry.io/456` | ⚠️ | Enables error tracking. Without it, errors log to stdout only. |
| `AI_GATEWAY_BASE_URL` | backend | `https://ai-gateway.vercel.sh/v1` | – | Optional: route Claude via Vercel AI Gateway for spend limits. |
| `PORT` | backend | `8000` | – | Auto-injected by Railway. Do **not** set manually. |

## Frontend (Vercel — Project Settings → Environment Variables)

| Name | Scope | Example | Required | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | frontend | `https://api.example.vn` or `https://recruit-backend.up.railway.app` | ✅ | Must match Railway public URL **without trailing slash**. |
| `NEXT_PUBLIC_CONSENT_VERSION` | frontend | `v1.0-2026-04` | ✅ | Must match the version string the backend accepts in `POST /v1/leads`. Coordinate bumps with legal. |
| `SENTRY_DSN` | frontend | `https://…@o123.ingest.sentry.io/789` | ⚠️ | Separate DSN from backend — use a different Sentry project. |
| `SENTRY_AUTH_TOKEN` | frontend | `sntrys_…` | ⚠️ | Build-time: uploads source maps for symbolicated stack traces. Set only in Vercel, not locally. |
| `SENTRY_ORG` | frontend | `example-vn` | ⚠️ | Needed if `SENTRY_AUTH_TOKEN` set. |
| `SENTRY_PROJECT` | frontend | `recruit-frontend` | ⚠️ | Same. |

Set **Environment** scope to `Production` for prod values, `Preview` for staging branch auto-deploys.

## Database (Railway Postgres addon)

Railway auto-generates these; reference via `${{Postgres.DATABASE_URL}}` in backend service.

| Name | Source | Notes |
|---|---|---|
| `DATABASE_URL` | Railway Postgres addon | Convert to asyncpg driver at app level — see `DEPLOY.md`. |
| `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE` | Railway | Individual components, usually unneeded. |

## Local dev

Copy `.env.example` to `.env` in each project root. Minimum to run backend locally:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recruit
ANTHROPIC_API_KEY=sk-ant-api03-test
TELEGRAM_BOT_TOKEN=
CORS_ORIGINS=http://localhost:3000
```

Minimum to run frontend locally:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_CONSENT_VERSION=v1.0-2026-04
```

## Rotation schedule

| Var | Rotate every | Procedure |
|---|---|---|
| `ANTHROPIC_API_KEY` | 90 days or on team departure | See `RUNBOOK.md` → "Rotate Claude API key" |
| `TELEGRAM_BOT_TOKEN` | Only on suspected compromise | Revoke old, issue new via @BotFather `/revoke` |
| DB password | 180 days | Use Railway "reset credentials"; backend auto-redeploys |
| Sentry DSN | Only on team cleanup | Regenerate in Sentry project settings |
