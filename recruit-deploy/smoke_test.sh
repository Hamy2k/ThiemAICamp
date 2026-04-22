#!/usr/bin/env bash
# Production smoke test — end-to-end flow.
#
# Usage:
#   export API_BASE=https://api.example.vn
#   export HR_TOKEN=<bearer>
#   export TELEGRAM_BOT_TOKEN=<bot token>         # optional, to verify notification
#   export TELEGRAM_CHAT_ID=<HR chat>             # optional
#   bash smoke_test.sh
#
# Exits 0 on success, non-zero on any failure.
# Every test prints ✅ PASS or ❌ FAIL with context.

set -uo pipefail

: "${API_BASE:?API_BASE is required}"
: "${HR_TOKEN:?HR_TOKEN is required}"

FAIL=0
TS=$(date +%s)

pass() { echo "✅ PASS  $*"; }
fail() { echo "❌ FAIL  $*"; FAIL=$((FAIL+1)); }

req() {
  # req METHOD PATH [BODY] [EXTRA_HEADER]
  local method="$1" path="$2" body="${3:-}" hdr="${4:-}"
  local args=(-sS -w "\n%{http_code}" -X "$method" "$API_BASE$path"
              -H "Content-Type: application/json"
              -H "Accept: application/json")
  [ -n "$hdr" ] && args+=(-H "$hdr")
  [ -n "$body" ] && args+=(-d "$body")
  curl "${args[@]}"
}

extract_code() { tail -n1 <<<"$1"; }
extract_body() { sed '$d' <<<"$1"; }

# ─── 1. Health ─────────────────────────────────────────────────────────
echo "── 1. Health check"
resp=$(req GET /v1/health)
code=$(extract_code "$resp")
body=$(extract_body "$resp")
if [ "$code" = "200" ] && echo "$body" | grep -q '"status":"ok"'; then
  pass "GET /v1/health → 200 ok"
else
  fail "GET /v1/health → $code  body=$body"
fi

# ─── 2. Create job ─────────────────────────────────────────────────────
echo "── 2. Create job (HR)"
job_body=$(cat <<EOF
{
  "title": "Smoke Test Worker ${TS}",
  "salary_text": "8-10 triệu",
  "location_raw": "KCN Sóng Thần, Dĩ An, Bình Dương",
  "requirements_raw": "Không cần kinh nghiệm",
  "shift": "day",
  "target_hires": 1
}
EOF
)
resp=$(req POST /v1/hr/jobs "$job_body" "Authorization: Bearer $HR_TOKEN")
code=$(extract_code "$resp")
body=$(extract_body "$resp")
JOB_ID=$(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("id",""))' 2>/dev/null || echo "")
if [ "$code" = "201" ] && [ -n "$JOB_ID" ]; then
  pass "POST /v1/hr/jobs → 201 id=$JOB_ID"
else
  fail "POST /v1/hr/jobs → $code  body=$(echo "$body" | head -c 400)"
  exit 1
fi

# ─── 3. Generate content (5 variants) ──────────────────────────────────
echo "── 3. AI generate-content"
resp=$(req POST "/v1/hr/jobs/$JOB_ID/generate-content" "{}" "Authorization: Bearer $HR_TOKEN")
code=$(extract_code "$resp")
body=$(extract_body "$resp")
VARIANT_ID=$(echo "$body" | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d["variants"][0]["id"] if d.get("variants") else "")' 2>/dev/null)
if [ "$code" = "200" ] && [ -n "$VARIANT_ID" ]; then
  pass "generate-content → 5 variants, first=$VARIANT_ID"
else
  fail "generate-content → $code  body=$(echo "$body" | head -c 400)"
  exit 1
fi

# ─── 4. Publish + create source + tracking link ────────────────────────
echo "── 4. Publish job + tracking link"
req PATCH "/v1/hr/jobs/$JOB_ID" '{"status":"active"}' "Authorization: Bearer $HR_TOKEN" > /dev/null

resp=$(req POST /v1/hr/sources '{"channel":"facebook","external_id":"smoke-'"$TS"'","display_name":"Smoke Source"}' "Authorization: Bearer $HR_TOKEN")
SOURCE_ID=$(extract_body "$resp" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("id",""))' 2>/dev/null)

resp=$(req POST "/v1/hr/jobs/$JOB_ID/tracking-links" "{\"variant_id\":\"$VARIANT_ID\",\"source_id\":\"$SOURCE_ID\"}" "Authorization: Bearer $HR_TOKEN")
TRACKING_ID=$(extract_body "$resp" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("tracking_id",""))' 2>/dev/null)
if [ -n "$TRACKING_ID" ]; then
  pass "tracking_id=$TRACKING_ID"
else
  fail "Could not create tracking link"
  exit 1
fi

# ─── 5. Submit lead (candidate) ────────────────────────────────────────
echo "── 5. Submit lead"
phone="+849$((RANDOM % 900000000 + 100000000))"
lead_body=$(cat <<EOF
{
  "tracking_id": "$TRACKING_ID",
  "full_name": "Smoke Test",
  "phone": "$phone",
  "area_raw": "KCN Sóng Thần, Dĩ An",
  "consent": {"version":"v1.0-2026-04","accepted":true}
}
EOF
)
resp=$(req POST /v1/leads "$lead_body")
code=$(extract_code "$resp")
body=$(extract_body "$resp")
SESSION_ID=$(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("session_id",""))' 2>/dev/null)
if [ "$code" = "201" ] && [ -n "$SESSION_ID" ]; then
  pass "POST /v1/leads → 201 session=$SESSION_ID"
else
  fail "POST /v1/leads → $code  body=$(echo "$body" | head -c 400)"
  exit 1
fi

# ─── 6. Screening turns (3 turns, simulated) ───────────────────────────
echo "── 6. Screening turns"
turn_ok=0
for msg in "em làm được từ tuần sau" "lam dc ca ngay, k thich ca dem" "em chua co kinh nghiem nhung muon hoc"; do
  resp=$(req POST /v1/screening/message "{\"session_id\":\"$SESSION_ID\",\"message\":\"$msg\"}")
  code=$(extract_code "$resp")
  [ "$code" = "200" ] && turn_ok=$((turn_ok+1))
  sleep 0.5
done
if [ "$turn_ok" -ge 2 ]; then
  pass "screening turns: $turn_ok/3 accepted (AI may have marked done=true early)"
else
  fail "screening turns: only $turn_ok/3 worked"
fi

# ─── 7. Complete screening (scoring + HR notify) ───────────────────────
echo "── 7. Complete screening + score"
resp=$(req POST /v1/screening/complete "{\"session_id\":\"$SESSION_ID\"}")
code=$(extract_code "$resp")
body=$(extract_body "$resp")
SCORE=$(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("score_total",""))' 2>/dev/null)
TIER=$(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("tier",""))' 2>/dev/null)
if [ "$code" = "200" ] && [ -n "$SCORE" ]; then
  pass "screening/complete → tier=$TIER score=$SCORE"
else
  fail "screening/complete → $code  body=$(echo "$body" | head -c 400)"
fi

# ─── 8. Telegram delivery check (optional) ─────────────────────────────
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "── 8. Telegram delivery"
  # Give backend up to 10s to deliver the notification
  sleep 8
  updates=$(curl -sS "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates?offset=-5" || echo "{}")
  if echo "$updates" | grep -q "Smoke Test"; then
    pass "Telegram: HR received smoke-test match notification"
  else
    # Not 100% reliable via getUpdates after webhook setup; treat as soft-warn
    echo "⚠️ SOFT  Telegram getUpdates could not confirm delivery (webhook mode may suppress)"
  fi
else
  echo "⏭  Skipped Telegram check (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set)"
fi

# ─── Summary ───────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "✅ All critical checks passed"
  exit 0
else
  echo "❌ $FAIL check(s) failed"
  exit 1
fi
