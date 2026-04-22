# Deploy guide — Phase 4

Target: Vercel (frontend) + Railway (backend + Postgres) + Telegram (notifications).

Expected total time from clean clone to production URL: **< 30 minutes**.

---

## Prerequisites

Install once:

```bash
npm i -g vercel
npm i -g @railway/cli
railway login
vercel login
```

Create accounts (free):
- https://railway.app
- https://vercel.com
- https://sentry.io
- https://logtail.com (or https://betterstack.com for newer UI)
- https://uptimerobot.com
- Telegram app → talk to @BotFather

---

## Step 1 — Backend on Railway (10 min)

### 1.1 Provision Postgres

1. Railway → **New Project** → **Provision PostgreSQL**.
2. Note the auto-generated project; Railway exposes `DATABASE_URL` as a service variable.

### 1.2 Create backend service

1. Same project → **+ New** → **GitHub Repo** → pick the `recruit-backend` repo.
2. Railway auto-detects Nixpacks; it reads `railway.toml` from the repo root.
3. Wait for first (likely failing) build — it needs env vars first.

### 1.3 Link DB + set env

Service → **Variables** tab → add:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
```

⚠️ **Must convert driver prefix** — Railway's DATABASE_URL is `postgresql://`, backend needs `postgresql+asyncpg://`. Two options:

**Option A (recommended):** use Railway's reference variable with inline edit — click **Raw Editor** and paste:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}?sslmode=disable
```
Then in `app/config.py` (already in Phase 2) the `get_settings()` replaces prefix.
**Actually simpler:** use a dedicated env var and let the app normalize:

```python
# already in app/db/session.py if needed — verify before deploy
url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
```

**Option B:** paste the raw connection string with `+asyncpg` by copying Postgres credentials and building manually.

Add the rest per `ENV_VARS.md`:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
TELEGRAM_BOT_TOKEN=123456:...
CORS_ORIGINS=https://recruit-frontend.vercel.app,https://careers.example.vn
APP_ENV=production
LOG_LEVEL=INFO
SENTRY_DSN=https://...@sentry.io/...
MODEL_JOB_POST=claude-sonnet-4-6
MODEL_SCREENING=claude-haiku-4-5-20251001
MODEL_SCORING=claude-haiku-4-5-20251001
```

### 1.4 Expose public domain

Service → **Settings** → **Networking** → **Generate Domain**.
Copy the `https://recruit-backend-xxx.up.railway.app` URL — this becomes `NEXT_PUBLIC_API_BASE_URL` on the frontend.

### 1.5 Deploy + verify

Push to main → Railway auto-deploys. Monitor **Deploy Logs**:

1. Look for `[release] alembic upgrade head` → `done`.
2. Look for `Uvicorn running on http://0.0.0.0:8000`.
3. Healthcheck polls `/v1/health`; wait until green.

```bash
curl https://recruit-backend-xxx.up.railway.app/v1/health
# → {"status":"ok","db":true}
```

### 1.6 Seed HR user (one-off)

Backend has no HR signup UI. Bootstrap an HR record:

```bash
railway run python - <<'PY'
import asyncio, os
from app.db.session import AsyncSessionLocal
from app.db.models import Company, HRUser

async def main():
    async with AsyncSessionLocal() as s:
        c = Company(name="Acme Corp", industry="manufacturing")
        s.add(c); await s.flush()
        hr = HRUser(
            company_id=c.id,
            email="hr@acme.vn",
            full_name="HR Admin",
            api_key_hash=os.environ["HR_BOOTSTRAP_TOKEN"],
            telegram_chat_id=os.environ.get("HR_TELEGRAM_CHAT_ID"),
        )
        s.add(hr)
        await s.commit()
        print(f"HR id={hr.id} token={os.environ['HR_BOOTSTRAP_TOKEN']}")
asyncio.run(main())
PY
```

Set `HR_BOOTSTRAP_TOKEN` + `HR_TELEGRAM_CHAT_ID` locally before the `railway run`. Store the returned token in a password manager.

---

## Step 2 — Frontend on Vercel (5 min)

### 2.1 Import repo

1. Vercel → **Add New** → **Project** → import `recruit-frontend`.
2. Framework: Next.js (auto-detected).
3. Root directory: leave default.
4. Build command, output directory: leave default.

### 2.2 Env vars

Project Settings → **Environment Variables** → add for **Production**:

```
NEXT_PUBLIC_API_BASE_URL=https://recruit-backend-xxx.up.railway.app
NEXT_PUBLIC_CONSENT_VERSION=v1.0-2026-04
SENTRY_DSN=https://...
SENTRY_AUTH_TOKEN=sntrys_...
SENTRY_ORG=example-vn
SENTRY_PROJECT=recruit-frontend
```

### 2.3 Deploy

```bash
cd recruit-frontend
vercel --prod
```

…or just `git push` since Vercel auto-deploys main branch.

### 2.4 Verify

Open `https://recruit-frontend-xxx.vercel.app/apply?tracking_id=test` — should show "Không thấy thông tin việc làm" (expected — no tracking link exists yet).

---

## Step 3 — Custom domains (5 min)

Assumes you own `example.vn` and manage DNS somewhere (Cloudflare recommended — free).

### 3.1 Backend → `api.example.vn`

1. Railway service → **Settings** → **Custom Domain** → enter `api.example.vn`.
2. Railway shows a CNAME target like `recruit-backend-xxx.up.railway.app`.
3. DNS: `CNAME api → recruit-backend-xxx.up.railway.app`.
4. Wait for SSL cert (~2 min).

### 3.2 Frontend → `careers.example.vn`

1. Vercel → Project → **Settings** → **Domains** → add `careers.example.vn`.
2. DNS: `CNAME careers → cname.vercel-dns.com`.
3. Wait for Vercel cert.

### 3.3 Update CORS + `NEXT_PUBLIC_API_BASE_URL`

Railway backend → update `CORS_ORIGINS`:
```
CORS_ORIGINS=https://careers.example.vn,https://recruit-frontend.vercel.app
```

Vercel frontend → update:
```
NEXT_PUBLIC_API_BASE_URL=https://api.example.vn
```

Redeploy both.

---

## Step 4 — Observability (see dedicated guides)

- `SENTRY_SETUP.md`
- `LOGTAIL_SETUP.md`
- `UPTIME_SETUP.md`
- `TELEGRAM_SETUP.md`

---

## Step 5 — E2E smoke test

```bash
cd recruit-deploy
export API_BASE=https://api.example.vn
export HR_TOKEN=<from Step 1.6>
export TELEGRAM_BOT_TOKEN=<from TELEGRAM_SETUP>
export TELEGRAM_CHAT_ID=<your HR chat_id>

bash smoke_test.sh
```

Expected: `✅ All 6 checks passed`. Non-zero exit on any failure.

---

## Step 6 — Verify production

| Check | URL | Expected |
|---|---|---|
| Backend health | `https://api.example.vn/v1/health` | `{"status":"ok","db":true}` |
| Frontend landing | `https://careers.example.vn/apply?tracking_id=<real_id>` | Job card + 3-field form |
| Screening | Submit form → `/screening/...` | First AI message visible |
| HR | `https://careers.example.vn/admin/jobs/new` | Token gate page |

If all green: ship. Update team in Slack, tag a git release `v0.1.0-prod`.

---

## Hard miss / SPEC_CONFLICT flags

1. **`postgresql://` vs `postgresql+asyncpg://`** — Railway's DATABASE_URL uses the generic prefix. Phase 2 `app/config.py` expects `+asyncpg`. Do **one** of: (a) add a one-line prefix swap in `config.py` (no Phase 2 refactor if treated as deploy glue), (b) set DATABASE_URL manually with `+asyncpg` prefix. Recommended: (b) to honor "don't refactor Phase 2".
2. **Railway free tier sleeps inactive services** (30-day trial period). For 24×7 uptime you need the $5 Hobby or $20 Pro plan. Factor into cost sheet.
3. **Cold-start < 3s constraint** — Railway Hobby tier typically boots a Python app in 8-15s. For true <3s, keep traffic warm via UptimeRobot ping every 5 min. See `UPTIME_SETUP.md`.
