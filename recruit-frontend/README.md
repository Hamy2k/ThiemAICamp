# Recruit Frontend

Next.js 15 + React 19 + Tailwind 4 frontend for AI job distribution (Vietnam).
Consumes Phase 2 FastAPI backend. Mobile-first, low-bandwidth, Vietnamese-only.

## Quick start

```bash
npm install
cp .env.example .env.local   # point NEXT_PUBLIC_API_BASE_URL at backend
npm run dev                  # http://localhost:3000
```

Then open a tracking link (one created by HR via backend):

```
http://localhost:3000/apply?tracking_id=<id>
```

## Build / deploy

```bash
npm run build && npm run start
```

Static output per route via Next.js 15 App Router. No server runtime needed beyond Node.

## Routes

| Path | Role | Type | Purpose |
|---|---|---|---|
| `/apply?tracking_id=…` | candidate | Server | Job summary + 3-field form |
| `/screening/[lead_id]?session_id=…&first_msg=…` | candidate | Client | Chat with AI, ≤5 turns, save/resume |
| `/success/[lead_id]` | candidate | Server | Confirmation + "HR gọi trong 24h" |
| `/admin/jobs` | HR | Server | Jobs list (scaffold — see API_MISMATCH below) |
| `/admin/jobs/new` | HR | Client | 4-field form → AI generates 5 variants → copy to FB |
| `/admin/leads/[id]` | HR | Server | Transcript + score + attribution (scaffold) |

## Env vars

| Var | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_CONSENT_VERSION` | Consent version shown on landing (must match backend) | `v1.0-2026-04` |

## Perf budget

- Landing route JS: ~60KB gzipped (landing form is the only client island)
- Screening route JS: ~75KB (chat state + form)
- FCP on 3G Fast: <2s (verified via Lighthouse in Phase 3 acceptance)
- Total fonts downloaded: **0** (system font stack)
- No image assets required (uses emoji for icons)

## API_MISMATCH log (Phase 3 observations)

Design/spec gaps from Phase 1 that Phase 3 flagged:

1. **`GET /v1/screening/:id` missing.** Save-and-resume on the screening chat is
   implemented via `localStorage` only. Clearing storage loses local chat
   history; backend session state persists for scoring purposes. Phase 4 should
   expose session-state endpoint.
2. **`GET /v1/hr/jobs` (list) missing.** `/admin/jobs` renders a scaffold until
   Phase 4 adds this endpoint.
3. **`GET /v1/hr/leads/:id` missing.** Same — scaffold in `/admin/leads/[id]`.
4. **URL shape:** Phase 3 spec is `/apply?tracking_id=…`; Phase 1 design originally
   wrote `/j/:tracking_id`. Implementing Phase 3 spec and calling backend
   `GET /v1/j/:tracking_id` server-side.

## Accessibility

- Every input has `<label>` (no placeholder-only)
- Every form error: `role="alert" aria-live="polite"` + red + icon
- Progress bar on chat: `role="progressbar"` with aria-value{min,now,max}
- Keyboard: all interactive elements are native `button` / `input` / `<a>`
- Touch targets ≥44px on pointer:coarse devices
- No hover-only interactions
- Tap-highlight disabled; reduced-motion honored

## Stack

- **Next.js 15** (App Router, Server Components by default)
- **React 19** — implicit in package.json peer
- **Tailwind 4** (CSS-first `@theme` in `app/globals.css`)
- **TypeScript strict** (`noUncheckedIndexedAccess`)
- **react-hook-form + zod** for forms
- No component library (raw Tailwind primitives in `components/ui/`)
- No state manager (local component state + native fetch)

## Structure

```
frontend/
├── app/
│   ├── layout.tsx              # root, VN lang, system font, viewport
│   ├── globals.css             # @import "tailwindcss" + @theme
│   ├── apply/page.tsx          # Server — fetch job, render landing + LandingForm
│   ├── screening/[lead_id]/page.tsx
│   ├── success/[lead_id]/page.tsx
│   └── admin/
│       ├── jobs/page.tsx
│       ├── jobs/new/page.tsx   # Client — form + AI variants preview
│       └── leads/[id]/page.tsx
├── components/
│   ├── forms/
│   │   ├── LandingForm.tsx     # "use client"
│   │   └── JobCreateForm.tsx   # "use client"
│   ├── chat/
│   │   ├── MessageBubble.tsx
│   │   ├── TurnProgress.tsx
│   │   └── ScreeningChat.tsx   # "use client" — save/resume via localStorage
│   └── ui/                     # Button, Input, Label, FieldError, Skeleton
├── lib/
│   ├── api.ts                  # Typed fetch wrapper, ApiError class
│   ├── validation.ts           # zod schemas with VN error messages
│   ├── phone.ts                # Client E.164 normalization (mirror of backend)
│   └── storage.ts              # localStorage save/resume for screening
├── types/
│   └── api.ts                  # Matches Phase 1 contract verbatim
├── .env.example
├── next.config.js              # Security headers, image optim off, pkg import optim
├── tailwind.config.ts          # Stub for Tailwind v4 (config is CSS-first)
├── postcss.config.mjs          # @tailwindcss/postcss
└── tsconfig.json               # strict + noUncheckedIndexedAccess
```

## Verification (Phase 3 acceptance)

```bash
npm install
npm run build          # 0 errors, 0 warnings expected
npm run typecheck      # 0 errors
npm run dev            # smoke: open /apply?tracking_id=<valid>
```

Lighthouse mobile (Chrome DevTools → Network: Fast 3G, CPU 4×):

- Performance ≥ 90 (budget assumes backend response <500ms)
- Accessibility ≥ 90 (labels, contrast, aria-live alerts)

## Next phases

- **Phase 4:** deployment config (Vercel), HR auth (NextAuth), missing backend
  endpoints (GET session/state, GET jobs list, GET lead detail).
- **Phase 5:** HR analytics dashboard with charts (Recharts), dark mode, i18n.
