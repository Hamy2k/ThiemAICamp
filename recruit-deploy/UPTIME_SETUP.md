# Uptime monitoring — UptimeRobot

Free tier: **50 monitors, 5-min check interval, 3 months of log retention**.
Sign up: https://uptimerobot.com

---

## 1. Add monitors

Dashboard → **+ Add New Monitor**:

### Monitor 1 — backend health

- **Monitor Type:** HTTP(s)
- **Friendly Name:** `recruit-backend prod health`
- **URL:** `https://api.example.vn/v1/health`
- **Monitoring Interval:** 5 minutes
- **Alert Contacts:** your email + Telegram (see step 3)
- **Keyword Monitoring** (enable): expect keyword `"status":"ok"` — catches "200 OK with broken DB" false positives.

### Monitor 2 — frontend landing

- **Monitor Type:** HTTP(s)
- **Friendly Name:** `recruit-frontend prod landing`
- **URL:** `https://careers.example.vn/apply`
- **Monitoring Interval:** 5 minutes
- **Expected HTTP status codes:** 200 (or 400 if landing without tracking_id → adjust URL with a stable demo tracking_id)

### Monitor 3 — full flow (optional, manual cron)

Use BetterUptime / Checkly / GitHub Actions cron to run `smoke_test.sh` daily at 08:00 ICT.
UptimeRobot does not execute multi-step scripts.

---

## 2. Side effect — warm Railway

The 5-min ping pattern **also keeps Railway instance warm**, preventing cold start > 3s. No config needed.

---

## 3. Alert channels

### 3.1 Telegram bot alerts

1. UptimeRobot → **My Settings** → **Alert Contacts** → **Add Alert Contact**.
2. Type: **Telegram**.
3. Open Telegram, search `@UptimeRobotBot`, send `/start`.
4. Bot replies with chat ID → paste into UptimeRobot.
5. Send test → confirm receipt.

### 3.2 Status page (optional, free)

UptimeRobot → **Status Pages** → **Add**.
- **Name:** Recruit Status
- **URL:** auto-generated subdomain (e.g., `stats.uptimerobot.com/xxxx`)
- **Monitors to include:** backend health + frontend landing
- Share link with HR team as support reference.

---

## 4. Alert response SLA (update in your runbook)

| Severity | Monitor down for | Response |
|---|---|---|
| P1 | >10 min | Page on-call (see `RUNBOOK.md` → on-call) |
| P2 | >30 min during business hours | Slack @recruit-eng |
| P3 | >2 hours overnight | Email inbox, handle next morning |

---

## Validation

```bash
# Intentionally break health
railway variables set DATABASE_URL=postgresql+asyncpg://broken/x

# Wait 10-15 min
# Expect: UptimeRobot → DOWN alert + Telegram + email

# Restore
railway variables set DATABASE_URL=${{Postgres.DATABASE_URL}}
# Expect: UP alert within 10 min
```

✅ Pass = both down + up alerts received.
