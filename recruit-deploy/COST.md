# Cost projection — Roman Recruit MVP

Target: **< $50/month infra** at 1000 leads/day (30k/month).
Claude API is treated as **COGS (cost of goods sold)**, not infra — tracked separately.

Update this table monthly. Last refresh: 2026-04-22.

---

## Infra cost (platform bills)

| Line item | Plan | Monthly | Free allowance | Why this tier | Swap if over budget |
|---|---|---:|---|---|---|
| **Vercel** (frontend) | Hobby | **$0** | 100GB bandwidth, unlimited hobby projects | MVP traffic well under cap | — |
| **Railway app** (backend) | Hobby | **$5** | $5 usage included | Needed for 24/7 non-sleep. Free trial sleeps after 30 days. | Render free (sleeps) → $0 but cold-start > 10s |
| **Railway Postgres** (addon) | Starter | **$5** | $5 usage included (shared) | Bundled discount with app on same project. Auto-backups 7d. | Neon free tier → $0 but limited to 512MB; fine for early |
| **Sentry** (FE + BE) | Developer | **$0** | 5k errors/mo across orgs | Two projects share the quota | Self-host Sentry → $0 + ops burden |
| **Logtail / BetterStack** (logs) | Free | **$0** | 1GB/mo, 3-day retention | PDPD-compliant (server-side in EU/US) | Self-host Grafana Loki on Railway → ~$5/mo |
| **UptimeRobot** (monitoring) | Free | **$0** | 50 monitors, 5-min interval | Enough for MVP | — |
| **AdminMongo / pgAdmin** | N/A | **$0** | use Railway's built-in psql console | — | — |
| **Custom domains** (Cloudflare) | Free | **$0** | CNAME + SSL | DNS only | — |
| | | | | | |
| **Infra subtotal** | | **$10** | | | **Well under $50 ✅** |

Headroom: **$40/mo** for traffic spikes → Railway usage overage, Sentry tier bump, etc.

---

## COGS — Claude API (per-lead variable)

From Phase 1 design estimate (validated Phase 1 §6):

| Call | Model | Per call | Calls/1000 leads | Sub-total |
|---|---|---|---|---:|
| Job post gen (5 variants bundled) | Sonnet 4.6 | $0.028 | 10 (1 job ≈ 100 leads) | $0.28 |
| Screening (avg 3 turns/lead w/ cache) | Haiku 4.5 | $0.00094/turn | 3000 | $2.55 |
| Scoring | Haiku 4.5 | $0.0016 | 1000 | $1.60 |
| | | | **Per 1000 leads:** | **$4.43** |

At 30k leads/month:
- **$132.90/month** Claude spend
- **$0.0044 / raw lead**
- **$0.0089 / qualified lead** (assume 50% complete screening)
- Under Phase 1 budget of $0.01/qualified lead ✅

---

## Grand total at 1000 leads/day

| Bucket | Monthly |
|---|---:|
| Infra | $10 |
| COGS (Claude) | $133 |
| **Total** | **$143** |

⚠️ **Flag for CFO**: the Claude spend dwarfs infra. Monitoring + optimization focus should be on Claude cost-per-lead first, not infra cost.

---

## Overage watchlist (alerts if crossed)

Set up Logtail / email alerts for these thresholds:

| Metric | Alert threshold | Action if breached |
|---|---|---|
| Claude spend/day | > $10 | Check `ai_calls` for retry storms or cache misses |
| Railway usage | > $15/mo | Check for memory bloat or misconfigured workers |
| Logtail volume | > 800 MB/mo | Drop DEBUG logs; add `PIIScrubber` if not set |
| Sentry events | > 4000/mo | Identify noisy issue; add `before_send` filter |
| Vercel bandwidth | > 80 GB/mo | Investigate bot traffic, add rate limit at edge |

---

## If budget exceeded — cut list (in order)

1. **Switch screening model 4.5 → 3.5 Haiku** (if still available). Saves ~40% on screening leg. Quality degradation: tolerable for blue-collar flow.
2. **Cap screening at 3 turns hard** (drop L4–L5). Saves 40% of screening $.
3. **Pre-filter scoring: skip Haiku if `fields_captured ≤ 2`**. Code-only score for junk leads. Saves ~$0.40/1k.
4. **Self-host Logtail** (Grafana Loki on same Railway project). Saves $0 today but unlocks headroom if we exceed free tier.
5. **Move to Anthropic batch API** for non-realtime scoring (batch every 5 min). 50% Haiku discount. Adds ~5 min latency to HR notification — acceptable.

---

## How to measure — recurring task

First Monday of each month, run:

```sql
-- AI spend last 30 days
SELECT DATE(created_at) AS d, call_site,
       ROUND(SUM(cost_usd)::numeric, 2) AS usd,
       COUNT(*) AS calls,
       ROUND(AVG(latency_ms))::int AS avg_ms
FROM ai_calls
WHERE created_at > now() - interval '30 days'
GROUP BY 1, 2 ORDER BY 1 DESC;

-- Leads last 30 days
SELECT DATE(created_at) AS d, COUNT(*) AS leads
FROM leads
WHERE is_duplicate_of IS NULL AND created_at > now() - interval '30 days'
GROUP BY 1 ORDER BY 1 DESC;
```

Paste numbers into this doc under a new "Actual — $month" section. Compare to projection.
