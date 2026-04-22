# Runbook — Roman Recruit prod

**Target reader:** on-call engineer at 2 AM with no context recall.
Every procedure: **copy-pasteable**, no "figure out X yourself".

Mark `✓ tested <date>` next to procedures you've actually rehearsed.

---

## 0. Access checklist — before you're on-call

You need all of these **before** your first shift. Escrow in 1Password / Bitwarden shared vault:

- [ ] Railway account with access to project `recruit-prod`
- [ ] Vercel account with access to project `recruit-frontend`
- [ ] Sentry account with access to both projects
- [ ] Logtail (BetterStack) access
- [ ] UptimeRobot access
- [ ] Anthropic Console access
- [ ] @BotFather token (stored in Railway env, not in vault)
- [ ] DB connection string (view-only read replica preferred — create in Railway later)
- [ ] Slack `#recruit-alerts` channel

---

## Deploy frontend  ✓ tested

```bash
cd recruit-frontend
git checkout main && git pull
npm ci
vercel --prod
```

Time: ~3 min. Vercel deploy URL shown in output. Promote to domain:
- auto if `careers.example.vn` is set as production domain.

Verify: open `https://careers.example.vn/apply` — should render header + job-not-found card (if no tracking_id).

---

## Deploy backend  ✓ tested

**Option A — from git push (recommended):**
```bash
cd recruit-backend
git checkout main && git pull
git push origin main
```
Railway auto-deploys. Watch at https://railway.app → project → Deployments.

**Option B — from local (urgent hotfix):**
```bash
cd recruit-backend
railway link              # pick recruit-prod / backend service
railway up
```

Migration runs automatically (`preDeployCommand` in `railway.toml`). If migration fails, deploy aborts — DB untouched.

Verify: `curl https://api.example.vn/v1/health` → `{"status":"ok","db":true}`.

---

## Rollback frontend  ✓ tested

Vercel keeps all past deployments immutably.

**UI path (30 seconds):**
1. Vercel → project → **Deployments**.
2. Find the last green deployment before the bad one.
3. Click **⋯** → **Promote to Production**.
4. Confirm. DNS flips in ≤10s.

**CLI path:**
```bash
vercel rollback --prod --yes
```
(rolls back to the immediately previous prod deployment.)

---

## Rollback backend  ✓ tested

Railway keeps the last 10 deployments. Rollback from UI:

1. Railway → backend service → **Deployments**.
2. Find last green deploy → click **⋯** → **Redeploy**.
3. ⚠️ **Migration warning:** if the bad deploy ran a forward migration, rolling back the *code* does not roll back the schema. Either:
   - The rolled-back code works with the new schema (usually true for additive changes).
   - Run `alembic downgrade -1` via `railway run` first, then redeploy.

```bash
# downgrade one revision (use only when code rollback needs schema rollback)
railway run alembic downgrade -1
```

---

## Restore DB from backup  ✓ tested

Railway Postgres auto-backups nightly (kept per plan: Hobby 7 days, Pro 30 days).

### Full restore (last resort — wipes current DB)

1. Railway → Postgres service → **Backups** tab.
2. Choose the snapshot → **Restore**.
3. Type the database name to confirm.
4. Railway recreates the DB in-place; backend auto-reconnects.

Downtime: ~5 min while restore runs.

### Partial restore (only restore one table)

```bash
# 1. Create a staging DB and restore backup into it
railway run pg_dump $DATABASE_URL_SNAPSHOT > /tmp/snap.sql
createdb recruit_staging
psql recruit_staging < /tmp/snap.sql

# 2. Copy specific table into prod
pg_dump --table=matches recruit_staging | psql $DATABASE_URL
```

---

## Rotate Claude API key  ✓ tested

Assumes compromise or 90-day scheduled rotation.

1. Anthropic Console → **API Keys** → **Create Key**. Label: `recruit-prod-<date>`.
2. Copy new key.
3. Railway → backend → **Variables** → update `ANTHROPIC_API_KEY` → Save.
4. Railway auto-redeploys (takes ~2 min).
5. After 10 min of stable traffic, Anthropic Console → revoke old key.

Verify:
```bash
curl -sS https://api.example.vn/v1/health    # sanity
bash smoke_test.sh                            # full E2E
```

---

## Inspect a failed lead

Scenario: HR says "ứng viên vừa đăng ký lúc 10:30 AM nhưng chưa thấy thông báo Telegram".

### Step 1 — locate the lead

```bash
railway connect Postgres     # opens psql
```
```sql
-- By phone
SELECT id, full_name, created_at, source_channel, tracking_id
FROM leads
WHERE phone_e164 = '+84909123456'
ORDER BY created_at DESC LIMIT 5;

-- By window (last 30 min)
SELECT id, full_name, phone_e164, created_at
FROM leads
WHERE created_at > now() - interval '30 minutes'
ORDER BY created_at DESC;
```

### Step 2 — check session state

```sql
SELECT id, status, turn_count, extracted_data, last_turn_at, completed_at
FROM screening_sessions
WHERE lead_id = '<lead_id>';
```

- `status='in_progress'` + `last_turn_at` > 10 min ago → candidate abandoned. No notification expected.
- `status='completed'` but no match row → see step 3.

### Step 3 — check match + notification

```sql
SELECT id, score_total, tier, notified_hr, notified_at, explanation_vi
FROM matches
WHERE lead_id = '<lead_id>';

SELECT channel, status, error_message, sent_at, payload->>'text' AS msg_preview
FROM notifications_log
WHERE lead_id = '<lead_id>'
ORDER BY sent_at DESC;
```

- `notified_hr=false` → backend never found an HR with `telegram_chat_id` for that company. Fix: run TELEGRAM_SETUP §3.3 for that HR.
- `status='failed'` + `error_message` contains `403` → user blocked the bot. Ask HR to re-send `/start`.
- `status='sent'` but HR says they didn't see it → check Telegram's "archived chats" / notification settings on HR's phone.

### Step 4 — check AI calls

```sql
SELECT call_site, error_code, latency_ms, created_at
FROM ai_calls
WHERE related_id = '<session_id or job_id>'
ORDER BY created_at DESC;
```

`error_code` populated → Claude failed that turn; fallback parser kicked in (see `fallback_used` in API response).

### Step 5 — check logs

Logtail → query:
```
lead_id:<lead_id> OR session_id:<session_id>
```
Look for ERROR or WARN lines. Correlate timestamps with steps above.

---

## On-call alert response — top 5 alerts

### Alert 1: `recruit-backend prod health — DOWN`

**Source:** UptimeRobot. **SLA:** act within 10 min.

1. Check Railway → backend service → **Deployments** tab. Is it crashing?
2. **Deploy Logs** tab → scan last 100 lines for stacktrace.
3. If DB connection errors → check Postgres service is running in same project.
4. If OOM (out-of-memory) → bump Railway plan one tier, redeploy.
5. If unknown → roll back to last green deploy (see "Rollback backend").
6. Update status page (UptimeRobot status page auto-updates).
7. Post in `#recruit-alerts`: cause + ETA.

### Alert 2: Sentry — `ClaudeUnavailableError` spike

**Source:** Sentry rule. **SLA:** act within 15 min.

1. Open Anthropic Console status page: https://status.anthropic.com
2. If Anthropic incident in progress: wait + note in Slack. Backend fallback parser serves degraded but functional UX.
3. If Anthropic is green: verify `ANTHROPIC_API_KEY` in Railway (might be revoked/expired).
4. Check `ai_calls` for 4xx vs 5xx in last 10 min:
   ```sql
   SELECT error_code, count(*) FROM ai_calls
    WHERE created_at > now() - interval '10 min'
    GROUP BY error_code;
   ```
5. `http_401` or `http_403` → key issue. Rotate (see procedure above).
6. `http_429` → hit Anthropic rate limit. Log into console, check usage, file support ticket if unexpected.

### Alert 3: Sentry — DB connection errors burst

1. Railway → Postgres → **Metrics** — CPU at 100%? Connections at max?
2. If connection count > pool size × 2 → pool leak. Redeploy backend to reset.
3. If CPU pegged → a rogue query. Check Logtail for slow queries > 3s.
4. If disk full → Postgres plan upgrade.

### Alert 4: Rate-limited leads flood

**Source:** Logtail alert `message:"RATE_LIMITED" count>50 in 5min`.

1. Someone is scraping or a legitimate viral post happened.
2. `railway run` into Postgres:
   ```sql
   SELECT source_channel, source_id, count(*)
   FROM leads
   WHERE created_at > now() - interval '1 hour'
   GROUP BY 1, 2
   ORDER BY count(*) DESC LIMIT 10;
   ```
3. If one `source_id` spiked 10× normal → real viral event, raise rate limit temporarily:
   ```bash
   railway variables set RATE_LIMIT_IP_PER_10MIN=20
   ```
4. If traffic looks bot-like (same UA, no phone normalization pattern) → ban via Cloudflare WAF or leave rate limit as-is.

### Alert 5: Frontend error spike (Sentry `recruit-frontend`)

1. Sentry → Issues → identify top error.
2. Common: `Failed to fetch` → backend is unhealthy, see Alert 1.
3. Uncommon: hydration mismatch → new deploy regression → rollback frontend.
4. `ChunkLoadError` → Vercel removed an old chunk user had cached. Non-actionable; user will reload.

---

## Communication templates (copy-paste)

### Incident start (Slack)
> 🔴 **INCIDENT** `<timestamp ICT>` — <short description>.
> Impact: <who/what>. Investigating. ETA first update: 15 min.

### Incident resolved
> ✅ **RESOLVED** `<timestamp>`. Root cause: <one line>. Fix: <one line>. Postmortem: <link or "EOW">.

### HR-facing (if customer impact)
> Xin lỗi, hệ thống đang gặp sự cố. Bên em đang khắc phục, sẽ có thông báo trong X phút.

---

## Non-urgent maintenance — how to test this runbook

Every quarter, do a "game day":

- [ ] Rollback frontend (no real user impact)
- [ ] Rotate Anthropic key
- [ ] Restore a backup into a throwaway DB
- [ ] Revoke Telegram bot token, reissue, verify flow

Mark ✓ tested + date next to each procedure header above.
