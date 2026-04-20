# SESSION.md — Checkpoint phiên làm việc

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** MES Proterial — hoàn tất 5/5 cải tiến top-app cho Kho thông minh

## 📍 Project location

```
C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend
```

- Node.js (Express) + PostgreSQL + WebSocket
- Git repo local (KHÔNG có remote)
- Commit cuối: `f640a7a feat(purchasing): replenishment engine — dynamic ROP + days-of-supply + auto-PR`

## ✅ 5 cải tiến top-app đã làm trong phiên này

| # | Feature | Commit | Ghi chú |
|---|---------|--------|---------|
| 2 | **Barcode scanner** | `6c02673` | `_scanner.js` reusable, native BarcodeDetector + ZXing CDN fallback, nút 📷 cạnh input lot/material trong 2 modal |
| 1 | **FIFO/FEFO + lot-level issue** | (pre-#3) | Migration 027 `stock_lots` + `v_stock_lots_fefo`, backfill từ GR+IQC, material-issues pick lot theo FEFO |
| 3 | **ASN + ETA + dock** | `34ce073` | Migration 028 cột ETA/dock/driver/plate + PATCH /asn + widget countdown real-time |
| 4 | **Expiry alert dashboard** | `421d133` | GET /wms/expiring (v_expiring_lots), widget dashboard 🔴🟠🟡 theo bucket |
| 5 | **Replenishment engine** | `f640a7a` | dynamic ROP, days-of-supply, auto-PR gộp theo supplier |

## Các commits khác trong phiên

- `6068043` checkpoint đầu
- `a5ef13b` IQC fail → NG-01 inventory + E2E test 14 bước xanh
- `9707ffa` seed WMS 5 luồng + fix bug stock-counts HAVING
- `06ef158` fix low-stock `m.material_id`
- `afcfad4` real-time PO widget + modal nhận hàng
- `77f52ae` nav: Kho thông minh ⭐ lên đầu, redirect login
- `080b4db` fix banner mod02 target=_blank
- `4171fce` fix modal openM()
- `363c457` fix QC_HOLD stuck warehouse=QC_HOLD

## 🔥 Còn đang dở / backlog

Chưa làm UI cho:
- Panel replenishment suggestions trong mod_warehouse (API đã sẵn sàng)
- Modal chọn lot cụ thể khi material-issue (picker FEFO hiện sort auto)
- Putaway suggestion (gợi ý location khi nhập)
- Mobile/PWA UI cho warehouse worker
- Cycle count schedule theo ABC
- Supplier portal + EDI

## Lệnh resume

```bash
cd "C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend"
git log --oneline -10                    # xem commits
npm start                                # run server
```

Nói với Claude: **"tiếp tục MES"** → em đọc SESSION.md.

## Context

- Factory: Proterial Vietnam
- Admin: `admin` / `123456`
- Port: 3000
- DB: `mes_proterial` PostgreSQL local
- Deploy target: Ubuntu + PM2 + Cloudflare Tunnel (KHÔNG Vercel)
- Docs: `docs/DATA_FLOW.md`
