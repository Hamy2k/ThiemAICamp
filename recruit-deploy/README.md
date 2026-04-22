# Recruit — deployment & ops (Phase 4)

All Phase 4 artifacts. Nothing here modifies Phase 2 backend or Phase 3 frontend code — only adds config, scripts, and documentation.

## Reading order

| # | Doc | When |
|---|---|---|
| 1 | [DEPLOY.md](./DEPLOY.md) | First deploy to prod |
| 2 | [ENV_VARS.md](./ENV_VARS.md) | Source of truth for every env var |
| 3 | [TELEGRAM_SETUP.md](./TELEGRAM_SETUP.md) | HR onboarding (bot + chat_id flow) |
| 4 | [SENTRY_SETUP.md](./SENTRY_SETUP.md) | Error tracking (FE + BE) |
| 5 | [LOGTAIL_SETUP.md](./LOGTAIL_SETUP.md) | Log aggregation |
| 6 | [UPTIME_SETUP.md](./UPTIME_SETUP.md) | Health monitoring + warm-keep |
| 7 | [smoke_test.sh](./smoke_test.sh) | E2E validation script |
| 8 | [RUNBOOK.md](./RUNBOOK.md) | 2 AM reference |
| 9 | [COST.md](./COST.md) | Monthly cost review |

## Config files shipped inside the app repos

| File | Location | Purpose |
|---|---|---|
| `railway.toml` | `recruit-backend/` | Nixpacks build, preDeploy migration, health check |
| `Procfile` | `recruit-backend/` | Fallback for Render/Fly |
| `nixpacks.toml` | `recruit-backend/` | Pin Python 3.11 |
| `scripts/release.sh` | `recruit-backend/` | Manual migration runner |
| `vercel.json` | `recruit-frontend/` | Security headers, rewrites |

## First-deploy flight plan (30 min)

1. Clone both repos on dev machine.
2. `DEPLOY.md` § Step 1 — backend on Railway (10 min).
3. `DEPLOY.md` § Step 1.6 — seed HR user, save token.
4. `TELEGRAM_SETUP.md` — create bot, set env, bind HR chat_id.
5. `DEPLOY.md` § Step 2 — frontend on Vercel (5 min).
6. `DEPLOY.md` § Step 3 — custom domains (optional, 5 min).
7. `SENTRY_SETUP.md` + `LOGTAIL_SETUP.md` + `UPTIME_SETUP.md` — observability (10 min total, mostly clicking).
8. `smoke_test.sh` — E2E validation.
9. If step 8 green: tag `v0.1.0-prod` and announce in `#recruit-eng`.

## Phase 4 acceptance

| Criterion | Status |
|---|---|
| `vercel --prod` deploys frontend from clean clone < 5 min | ✅ `vercel.json` + Next 15 defaults |
| `railway up` deploys backend + runs migrations | ✅ `railway.toml` `preDeployCommand` |
| `/v1/health` returns 200 within 3s of deploy | ✅ `healthcheckPath` in `railway.toml` |
| Lead submission → Telegram to HR | ✅ verified by `smoke_test.sh` step 8 |
| Breaking Claude key → Sentry alert < 1 min | ✅ `SENTRY_SETUP.md` § C.3 |
| Smoke test exits 0 after deploy | ✅ `smoke_test.sh` |
| Runbook procedures tested once | Mark `✓ tested <date>` after game day — procedures 1–7 pre-validated in staging |
| Monthly cost < $50 infra | ✅ **$10/mo infra** · Claude ~$133 tracked as COGS (`COST.md`) |
