# Telegram bot setup — HR notifications

Backend uses Telegram Bot API to push "new qualified candidate" messages to HR chats. Free. No approval needed.

---

## 1. Create bot

1. Open Telegram. Search `@BotFather`. Tap **Start**.
2. Send `/newbot`.
3. Name prompt: enter `Recruit HR Alerts`.
4. Username prompt: enter `recruit_hr_alerts_bot` (must end in `_bot`, globally unique — append numbers if taken).
5. BotFather replies with:
   - **Bot URL** (`t.me/recruit_hr_alerts_bot`)
   - **HTTP API token** — copy this, you'll set `TELEGRAM_BOT_TOKEN` with it.

## 2. Set bot description + avatar (optional)

Still in @BotFather:
```
/setdescription → select your bot → "Nhận thông báo ứng viên mới từ Roman Recruit."
/setabouttext → "Bot nội bộ — chỉ HR đã được mời."
/setuserpic → upload a 512×512 png
```

## 3. Collect HR `chat_id`

Each HR staff needs to open a DM with the bot so the bot has a `chat_id` to send to.

### 3.1 HR onboarding flow (send to HR staff)

Email them:
> 1. Mở Telegram → tìm `@recruit_hr_alerts_bot`
> 2. Bấm **Start** (gửi tin `/start`)
> 3. Chụp màn hình gửi lại cho admin — admin sẽ thêm bạn vào hệ thống.

### 3.2 Admin fetches chat_id

```bash
# Replace with your token
TOKEN=123456:ABC-DEF
curl "https://api.telegram.org/bot$TOKEN/getUpdates" | python3 -m json.tool

# Find the chat object for each HR who /start'd:
#   "chat": { "id": 987654321, "first_name": "HR One", "type": "private" }
# 987654321 is their chat_id.
```

### 3.3 Persist `telegram_chat_id` on `hr_users`

```bash
railway run python - <<'PY'
import asyncio
from sqlalchemy import update
from app.db.session import AsyncSessionLocal
from app.db.models import HRUser

async def main():
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(HRUser)
            .where(HRUser.email == "hr@acme.vn")
            .values(telegram_chat_id="987654321")
        )
        await s.commit()
asyncio.run(main())
PY
```

## 4. Verify delivery

From backend shell (no code change — use Telegram REST directly):
```bash
TOKEN=$TELEGRAM_BOT_TOKEN
CHAT_ID=987654321
curl -sS "https://api.telegram.org/bot$TOKEN/sendMessage" \
  -d "chat_id=$CHAT_ID" \
  -d "text=🧪 Test delivery from smoke $(date +%T)"
# → {"ok":true,"result":{...}}
```

✅ HR receives the message = ready.

## 5. Set backend env

Railway → backend → **Variables**:
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

Backend redeploys. Next `screening/complete` → backend posts to bot → HR receives "🔔 Ứng viên mới — HOT" card.

---

## Operational notes

- **Rate limits** (Telegram): 30 messages/second/bot globally, 1 msg/sec to same chat. Backend sends ≤1 msg/lead × 1000 leads/day = **negligible**.
- **Message format**: backend uses `parse_mode=HTML`. Don't embed user-supplied HTML (XSS via lead name). Phase 2 code escapes via f-string — safe.
- **Revocation**: `@BotFather` → `/token` → revoke → rotate `TELEGRAM_BOT_TOKEN` in Railway → redeploy.
- **Bot blocked by user**: `sendMessage` returns `403`. Backend logs it, `notifications_log.status='failed'`. No retry — user must manually `/start` again.
