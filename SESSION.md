# SESSION.md — Checkpoint phiên làm việc

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** MES Proterial stable + **chess_game/** mới (Flutter mobile game — retention + monetization)

## 🆕 Project mới trong workspace: chess_game/

- **Path:** `C:\ThiemAICamp\chess_game`
- **Stack:** Flutter 3.24+, Dart, google_mobile_ads, provider, shared_preferences
- **Scope MVP:** Quick Play, Daily Challenge, Puzzle, Boss Battle, Shop, XP/coin economy
- **Engine:** minimax + alpha-beta (depth 1-4), PST eval, style-aware boss AI
- **Build:** chạy `flutter create --platforms=android .` → `flutter pub get` → `flutter build apk --release`
- **Backlog:** thêm Stockfish cho Master mode, IAP thật, sound files, leaderboard backend

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
