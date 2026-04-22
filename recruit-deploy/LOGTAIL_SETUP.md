# Log drain — Railway → BetterStack (Logtail)

Free tier: **1 GB/month logs, 3 days retention**. Enough for MVP at 1000 leads/day.
Sign up: https://betterstack.com/logtail

Phase 2 backend already emits JSON to stdout (see `app/utils/logging.py`). This pipes that stream into a searchable UI.

---

## 1. Create source in Logtail

1. Logtail dashboard → **Sources** → **Connect Source**.
2. Platform: **Railway**.
3. Name: `recruit-backend-prod`.
4. Copy the **Source Token** (e.g., `abcd1234...`).

## 2. Attach to Railway service

1. Railway → backend service → **Settings** → **Observability** → **Log Drains** (feature flag may need enabling; if absent, use HTTP drain workaround below).
2. Add drain:
   - **Type:** HTTP
   - **URL:** `https://in.logs.betterstack.com/`
   - **Token:** `Bearer <source token>`
3. Save → new drain is active immediately.

**If log drain UI missing on your plan:** install the Logtail logger directly in Python as a fallback:

```python
# app/utils/logging.py — add to setup_logging()
if token := os.getenv("LOGTAIL_SOURCE_TOKEN"):
    from logtail import LogtailHandler
    root.addHandler(LogtailHandler(source_token=token))
```

Add env var `LOGTAIL_SOURCE_TOKEN=<token>` in Railway.

## 3. PDPD — scrub PII before send

**Critical.** The JSON log formatter may include message fields that contain phone/name. Add a filter:

```python
# app/utils/logging.py
import logging

class PIIScrubber(logging.Filter):
    """Redact phone-like and email-like substrings from log messages."""
    import re
    PHONE = re.compile(r"(\+?84|0)\d{9,10}")
    EMAIL = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    def filter(self, record):
        msg = str(record.msg)
        msg = self.PHONE.sub("[PHONE_REDACTED]", msg)
        msg = self.EMAIL.sub("[EMAIL_REDACTED]", msg)
        record.msg = msg
        return True

root.addFilter(PIIScrubber())
```

## 4. Useful saved views

Create in Logtail → **Views** → **Save**:

| View name | Query | Purpose |
|---|---|---|
| Errors only | `level:ERROR OR level:CRITICAL` | Triage page |
| Claude calls | `message:"claude.call"` | Track retry rate, latency |
| AI fallback | `message:"screener.fallback" OR message:"scorer.fallback"` | Detect degraded AI |
| Rate limit | `message:"RATE_LIMITED"` | Spot abuse |
| Slow requests | `latency_ms:>3000` | Performance regressions |

## 5. Alert — error rate spike

Logtail → **Alerts** → **New**:

- **Query:** `level:ERROR`
- **Condition:** `count > 10 in 5 minutes`
- **Channel:** Slack / email

---

## Free-tier ceiling

At 1000 leads/day and current log volume (~50 lines per lead):
- ~50k log lines/day × 30 = 1.5M lines/month
- Avg 400 bytes/line = **~600 MB/month** → fits 1 GB free tier.

If you exceed: drop `DEBUG` logs to file-only, keep `INFO+` in drain. See `app/config.py` `log_level`.
