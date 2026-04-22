# SESSION.md — Checkpoint phiên làm việc

## Lần cập nhật cuối

**Ngày:** 2026-04-22
**Trạng thái:** MES Proterial stable + **chess_game/** (Flutter APK đã build) + **roman-legion-chess/** (Phase 2 xong, chờ duyệt Phase 3)

## 🆕 Project: roman-legion-chess/ (ACTIVE — paused chờ Phase 3)

- **Path:** `C:\ThiemAICamp\roman-legion-chess`
- **Stack LOCKED:** TypeScript strict + Phaser 3 + chess.js + Vite + Capacitor 6 + Tailwind + Zustand + Howler + GSAP + Vitest + pnpm. AI: Easy (random+capture), Medium (minimax d=3 + alpha-beta, chưa build), Hard (Stockfish WASM, chưa install)
- **Tiến độ:**
  - ✅ Phase 1 — Playable core: ChessEngine (wrap chess.js), AIEasy, Phaser GameScene, human vs AI Easy browser. 24/24 tests pass.
  - ✅ Phase 2 — Visual theme: exact palette (gold #D4AF37, crimson #C8102E, marble #F5F1E8, obsidian #1A1A2E/#0F0F17), Cinzel+Orbitron fonts, MenuScene (4 buttons), Button/Banner/Logo/CurrencyBar reusable components, board gold frame + glow + tile veining + gold pulse legal indicator. 24/24 tests still green.
- **Workflow RULES user định (quan trọng):**
  - 1 phase → STOP → report (đã build gì + deviation + lý do) → chờ duyệt
  - Không thêm dep ngoài list locked mà không hỏi
  - Spec mơ hồ: đề xuất 2 phương án, không silent chọn
  - Magic number → `src/data/tuning.ts` (SSOT)
  - Asset paths → `src/data/assetConfig.ts` (SSOT)
  - Delete > complicate
  - Không generate final art/audio bằng code — user drop file sau
- **Phase 3 options** (user chưa chọn):
  - (a) Promotion UI + pause + sound
  - (b) Medium AI (minimax d=3)
  - (c) Capacitor init + APK chain
  - (d) 3 Bosses v1.0 (cần user cung cấp spec name + rule-break)
  - (e) Asset pipeline polish
- **Deviations chờ user confirm:**
  - D1 CAMPAIGN button = Coming Soon (thay vì wire ARENA duplicate)
  - D2 Back button ← top-left GameScene (spec không yêu cầu, tôi thêm)
  - D3 Board frame 4px (spec nói 3px)
- **Dev server:** `pnpm dev` → http://localhost:5173 (cũng expose Network cho mobile test)

## 🎮 Project: chess_game/ (DONE Phase 1 MVP)

- **Path:** `C:\ThiemAICamp\chess_game`
- **Stack:** Flutter 3.41.7, Dart, google_mobile_ads, provider, shared_preferences
- **APK đã build:** `build\app\outputs\flutter-apk\app-release.apk` (52.3MB)
- **Dev env đã setup ổ E:** Flutter `C:\flutter`, JDK 17 `C:\Program Files\Microsoft\jdk-17...`, Android SDK `E:\AndroidDev\Sdk`, Gradle cache `E:\AndroidDev\gradle`, pub-cache `E:\AndroidDev\pub-cache`. User env vars ANDROID_HOME/GRADLE_USER_HOME/PUB_CACHE đã set permanent.
- **Scope:** Quick Play, Daily Challenge, Puzzle, Boss Battle (6 boss), Shop, XP/coin, rewarded ads (test IDs)
- **Backlog:** Stockfish, IAP thật, sound files drop, Capacitor/AdMob production IDs

## 📍 Project location

```
C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend
```

- Node.js (Express) + PostgreSQL + WebSocket
- Git repo local (KHÔNG có remote)
- Commit cuối: `f1e377b feat(planning): UI wizard chia batch PO lớn + tree view parent-child`

## ✅ Đã làm trong chuỗi session gần đây (theo thứ tự commit)

| Phạm vi | Commit | Mô tả |
|---|---|---|
| SSOT stock | MIG 032 | `stock_lots` là source of truth, trigger tự sync `inventory_stocks` |
| Demand-aware stock | MIG 033 | `v_material_stock` thêm `reserved_open_qty` + `net_available_qty` (trừ PO đang chạy) |
| MRP Net Requirement | MIG 034 | `v_mrp_suggestion` dùng Available-to-Promise pattern |
| MRP Planning Workbench | MIG 035 | `mrp_forecast(days)` gộp toàn PO kế hoạch → đề xuất mua bulk, UI tab mod09 |
| BTP consumption | MIG 036 | `btp_consumption` table, pick BTP giữa stages (Đùn→UV→Hèm→Đóng gói) |
| PO split parent-child | MIG 037 | `parent_po_id`, `batch_no`, endpoint split + wizard UI mod08 |
| Pick list NVL cho SX | MIG 030-031 | `v_pick_list` + endpoint + tab `🔔 Cấp NVL SX` |
| SX confirm nhận NVL | — | Banner mod02 `✓ Đã nhận`, WS `production.nvl_received` |
| Two-step putaway | — | IQC pass → `released` → kho scan + chọn kho đích → `available` |
| QR code cho lot | MIG 029 | `stock_lots.qr_code`, `scan_events`, scanner reusable, `/l/:qr` public, mobile PWA |
| Demand-aware low-stock UI | — | Widget dashboard hiện NET = avail − reserved + công thức mua (MRP) |
| Role separation Planner/Supervisor | — | mod08 chỉ release, mod02 mới start/pause |
| Fix lỗi submit PR UUID | — | POST /requests + savePR gọi API, bỏ localStorage legacy |

## 🔥 Đang làm dở / backlog

- **Auto split từ SO:** khi SO có qty lớn (container) → tự tạo parent PO + split 15 child
- **Bulk release children:** release 1 phát cho cả 15 batch của parent
- **Timeline Gantt parent-child:** hiển thị 15 batch trên timeline
- **Multi-level BOM:** sản phẩm có sub-assembly
- **Supplier portal:** NCC tự confirm PO, push ASN
- **Cycle count schedule theo ABC:** A/tuần, B/tháng, C/quý
- **Analytics nâng cao:** turnover, dead-stock, shrinkage
- **Fix cosmetic:** putaway unit hiện capacity_unit thay vì unit vật tư

## Lệnh resume

```bash
cd "C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend"
git log --oneline -15           # xem các commit gần đây
npm start                       # chạy server port 3000
```

Sau đó nói với Claude: **"tiếp tục MES"** hoặc chỉ định việc cụ thể (VD "làm tiếp auto split từ SO", "bulk release children").

## Context tham khảo

- Factory: Proterial Vietnam
- Admin: `admin` / `123456`
- Port: 3000
- DB: `mes_proterial` PostgreSQL local
- Migrations đã chạy: 000 → 037
- Deploy target: Ubuntu + PM2 + Cloudflare Tunnel (KHÔNG Vercel)
- Docs: `docs/DATA_FLOW.md`
