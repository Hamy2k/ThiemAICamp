# Sentry setup — frontend + backend

Free tier: 5k errors/month, 7-day retention. Sign up: https://sentry.io

Two projects needed (separate DSNs).

---

## Part A — Backend (FastAPI)

### A.1 Create project

1. Sentry → **Projects** → **Create Project** → platform: **FastAPI**.
2. Name: `recruit-backend`. Team: your default.
3. Copy the DSN shown (`https://...@o1234.ingest.sentry.io/5678`).

### A.2 Install SDK (add to backend)

Already listed as optional — add to `pyproject.toml` dependencies:

```toml
"sentry-sdk[fastapi]>=2.15.0",
```

Reinstall locally: `pip install -e .`

### A.3 Initialize — add to `app/main.py`

Insert **above** `def create_app()`:

```python
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration

if dsn := os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "development"),
        traces_sample_rate=0.05,          # 5% of requests traced
        profiles_sample_rate=0.0,         # off — saves budget
        send_default_pii=False,           # PDPD: never send phone/name
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            AsyncPGIntegration(),
        ],
    )
```

### A.4 PII scrubbing

Add `before_send` hook to strip any field that leaks PII:

```python
def _scrub(event, hint):
    # Strip request bodies — they contain phone/name
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = "[REDACTED_BODY]"
    return event

sentry_sdk.init(..., before_send=_scrub)
```

### A.5 Set env var in Railway

```
SENTRY_DSN=https://...@o1234.ingest.sentry.io/5678
```

Redeploy. Trigger a test error via `/v1/` on a non-existent path — should NOT create an error (404 is not reported by default). To verify:

```bash
railway run python -c "import sentry_sdk; sentry_sdk.capture_message('smoke test from $(date)')"
```

Check Sentry → Issues within 30s.

---

## Part B — Frontend (Next.js)

### B.1 Create project

1. Sentry → **Create Project** → platform: **Next.js**.
2. Name: `recruit-frontend`. Copy DSN.

### B.2 Install wizard (one command)

```bash
cd recruit-frontend
npx @sentry/wizard@latest -i nextjs --saas --org <your-org> --project recruit-frontend
```

The wizard writes:
- `sentry.client.config.ts`
- `sentry.server.config.ts`
- `sentry.edge.config.ts`
- updates `next.config.js` with Sentry wrapper

### B.3 Review + prune client config

Free tier: keep client bundle lean. Edit `sentry.client.config.ts`:

```ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.02,
  replaysSessionSampleRate: 0,          // no session replay (costs budget + PII)
  replaysOnErrorSampleRate: 0,
  sendDefaultPii: false,
  environment: process.env.NEXT_PUBLIC_VERCEL_ENV ?? "development",
  integrations: [],                     // drop default integrations for bundle
});
```

### B.4 Set env vars in Vercel

```
NEXT_PUBLIC_SENTRY_DSN=https://...
SENTRY_AUTH_TOKEN=sntrys_...           # for source map upload at build
SENTRY_ORG=<your-org>
SENTRY_PROJECT=recruit-frontend
```

Redeploy. Trigger test error via browser console:
```js
throw new Error("sentry-smoke")
```
Check Sentry within 30s.

---

## Part C — Alert rules (both projects)

### C.1 Slack/Telegram alert channel

Sentry → **Settings** → **Integrations** → install **Slack** (or **Microsoft Teams**).

### C.2 Alert rules — minimum 3

Create these alerts per project:

| Name | Trigger | Action |
|---|---|---|
| **Spike: errors >20 in 5min** | `event.count > 20 in 5 minutes` | Slack channel #alerts |
| **Regression: new issue** | Issue seen for first time in 24h | Slack channel #alerts |
| **Claude down**: `ClaudeUnavailableError` | Tag `error.type == ClaudeUnavailableError` AND `event.count > 5 in 5 min` | Slack + Telegram to on-call |

### C.3 Validation — break Claude intentionally

```bash
# Temporarily set bad key
railway variables set ANTHROPIC_API_KEY=broken-key
# Submit a lead via frontend, try screening
# → expect Sentry alert within 1 min for ClaudeUnavailableError
# Restore
railway variables set ANTHROPIC_API_KEY=<real key>
```

✅ Pass = Sentry shows issue + Slack message arrived < 60s.
