# User actions needed to ship recruit-backend/frontend

Everything that requires your credentials or real-world action. Nothing here the app itself can do.

## 1. Claude API key (5 min, ~$5 nạp Anthropic)

Without this: AI generates 1 stub variant (hardcoded), screening falls back to regex parser (works but less natural).

1. Đi https://console.anthropic.com → Sign up (email + phone verify)
2. **Billing** → Add credit card → Top up $5 (~150k leads worth of screening)
3. **API Keys** → **Create Key** → Label: `recruit-prod` → copy
4. Set trong `recruit-backend/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
5. Restart backend → AI sinh nội dung thật.

Cost signal: ~$4.43 per 1000 leads (Sonnet gen + Haiku screening + scoring).

---

## 2. Telegram bot (10 min)

Without this: HR notification logs `status='failed'` (no chat_id to send to). Flow still works, HR must manually check `/admin/leads`.

Follow `TELEGRAM_SETUP.md` step-by-step:
1. Chat @BotFather → `/newbot` → copy token
2. Có HR cần notification: mở bot DM → bấm `/start`
3. Call `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy chat_id
4. Set backend env:
   ```
   TELEGRAM_BOT_TOKEN=123456:...
   ```
5. Update `hr_users` row với `telegram_chat_id`:
   ```sql
   UPDATE hr_users SET telegram_chat_id='<chat_id>' WHERE email='hr@your.vn';
   ```
6. Test: submit 1 lead → complete screening → HR receives Telegram push.

---

## 3. Deploy production (30 min, ~$10/month)

Without this: app chỉ chạy trên máy bạn. Đóng máy = app chết.

Follow `DEPLOY.md` step-by-step. Highlights:
1. Signup Railway + Vercel (both support GitHub login)
2. Railway: provision Postgres addon + import `recruit-backend` repo → set env vars (copy from `.env`) → deploy
3. Vercel: import `recruit-frontend` repo → set `NEXT_PUBLIC_API_BASE_URL=<Railway domain>` → deploy
4. Optional: point `careers.example.vn` + `api.example.vn` DNS
5. Run `recruit-deploy/smoke_test.sh` to verify

Cost: $5/mo Railway Hobby + $5 Postgres = $10. Vercel Hobby free.

---

## 4. Real FB group admin access

Without this: you can't actually post to groups.

1. Join or create the FB group your candidates read ("Việc làm TPHCM")
2. Get posting permission (admin approval if member; immediate if you own)
3. In `/admin/sources`, add the group with display_name matching the real group

Important: Facebook may flag frequent posting with same link across groups as spam. Recommendations:
- Use different variants if posting >5 groups (current design: 1 variant + multiple tracking links gives same risk)
- Vary posting times (don't bulk post)
- Include a native-looking intro sentence per group (not identical copy-paste)

---

## 5. Real-world pilot (1-2 weeks)

Without this: you don't know if the app actually converts.

Minimum pilot:
- 1 real job (e.g., partner with a real HR contact)
- Post to 3 real FB groups via `/admin/sources` → `/admin/jobs/new`
- Track for 7 days
- Review `/admin/analytics` to see which source/variant won
- Adjust pricing model (per-qualified-lead) based on HR feedback

Target metrics for go/no-go:
- Conversion click → lead: >15% (blue-collar FB group benchmark)
- Conversion lead → qualified: >40%
- HR satisfaction: would they pay $50/hire?

---

## Summary — what the app CAN do autonomously vs NEEDS you

| Task | App does | You do |
|---|---|---|
| Write FB post | ✅ Claude/stub | — |
| Generate poster image | ✅ Pillow | — |
| Track clicks per group | ✅ auto | — |
| Screen candidates | ✅ AI chat | — |
| Score + notify | ✅ deterministic + Telegram | — |
| Create jobs | ✅ UI form | — |
| List ứng viên + analytics | ✅ /admin | — |
| Create Anthropic account | ❌ | ✅ |
| Buy Claude credits | ❌ | ✅ |
| Create Telegram bot via @BotFather | ❌ | ✅ |
| Join FB groups | ❌ | ✅ |
| Post to FB groups | ❌ (API locked by Meta) | ✅ |
| Sign up Railway + Vercel | ❌ | ✅ |
| Point DNS | ❌ | ✅ |
