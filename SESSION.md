# SESSION.md — Checkpoint phiên làm việc

> Claude tự đọc file này đầu mỗi phiên để biết việc đang dở.

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** MES Proterial — vừa thêm migration 026 (stock views + trace), vá lỗ hổng WMS material-issues, thêm API truy vết

## 📍 Project location (KHÔNG phải trong C:\ThiemAICamp)

```
C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend
```

- Stack: Node.js (Express) + PostgreSQL + WebSocket
- Git repo riêng, branch master
- Commit cuối (trước phiên này): `3085ba0 fix(mod09): wire purchasing UI to real API`

## 🔥 Đã làm trong phiên này (chưa commit)

### Mới: Docs cấu trúc dữ liệu
- [x] `docs/DATA_FLOW.md` — sơ đồ + quan hệ bảng PR→PO→GR→IQC→NCR→WMS, quy ước location, transaction_type, luồng trạng thái, API chính

### Mới: Migration 026 — stock views
- [x] `db/migrations/026_stock_views_and_trace.sql`:
  - `v_material_stock` — tách `available_qty` (loại QC_HOLD + NG-01) / `qc_hold_qty` / `ng_qty` / `total_qty` + stock_level (ok/low/critical/out)
  - `v_supply_chain_trace` — 1 row per GR line với chain PR→PO→GR→IQC→NCR→NG
  - `v_stock_movement_30d` — luân chuyển kho 30 ngày theo loại transaction
  - `assert_issuable_location()` — function chặn xuất từ QC_HOLD/NG-01 (tuỳ chọn gọi ở backend)
  - 5 index tăng tốc

### Patch: `routes/wms.js`
- [x] `POST /material-issues`:
  - Bắt buộc `from_location`, chặn QC_HOLD / NG-01
  - Trừ `inventory_stocks` có filter `location = from_location` (không còn trừ toàn bộ)
  - Throw `INSUFFICIENT_STOCK` → 409 nếu không đủ
  - Ghi `location` vào `inventory_transactions`
- [x] `GET /stock?breakdown=1` — trả về data từ `v_material_stock`
- [x] `GET /qc-hold` (mới) — lô đang chờ IQC
- [x] `GET /ng` (mới) — kho NG-01
- [x] `GET /dashboard` — breakdown `raw_available`, `raw_qc_hold`, `raw_ng`, `raw_total`, `qc_hold_batches`
- [x] `GET /low-stock` — dùng `v_material_stock.available_qty` thay vì tổng thô

### Patch: `routes/purchasing.js`
- [x] `GET /traceability/:gr_id?` (mới) — truy vết end-to-end 1 lô
  - Query param: `gr_number`, `lot_no`, `material_code`
  - Trả `v_supply_chain_trace` + snapshot `v_material_stock`

### Patch: `scripts/apply_new_migrations.js`
- [x] Thêm `026_stock_views_and_trace.sql` vào TARGETS

## 🔥 Còn đang dở — cần check sau

### Từ phiên trước (vẫn chưa xử lý):
- [ ] `db/migrations/025_iqc_ncr.sql` — chưa rõ đã chạy vào DB PostgreSQL chưa?
- [ ] `routes/iqc.js` — IQC workflow
- [ ] `routes/ncr.js` — NCR workflow
- [ ] `public/mod_iqc.html` — UI IQC
- [ ] `public/_nav.js` + `public/mod09_purchasing.html` + `public/mod_warehouse.html` — UI đang dở

### Cần làm tiếp
1. Chạy migration 025 + 026 vào PostgreSQL: `npm run db:init` hoặc `node scripts/apply_new_migrations.js`
2. UI hiển thị breakdown QC_HOLD / NG / Available trong dashboard WMS
3. Test end-to-end: tạo PR → duyệt PO → nhập GR → IQC pass/fail → verify stock tách đúng
4. Ngó lại `public/mod09_purchasing.html` thêm tab "Truy vết" gọi `/api/purchasing/traceability`

## Blocker / Câu hỏi cần user quyết

1. ⏳ Đã chạy migration 025 + 026 vào PostgreSQL chưa? (cần `node scripts/apply_new_migrations.js`)
2. ⏳ Test end-to-end IQC flow đã chạy chưa?
3. ⏳ Khi nào commit batch? Giờ có 5 file mới + 5 file modified.

## Lệnh resume

```bash
cd "C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend"
git status                          # xem file đang modify
node scripts/apply_new_migrations.js  # áp migration 025 + 026
npm start                           # chạy server
```

Nói với Claude: **"tiếp tục MES"** → em đọc SESSION.md.

## Context tham khảo

- Factory: Proterial Vietnam
- Tài khoản default: `admin` / `123456`
- Port: 3000
- DB: `mes_proterial` trên PostgreSQL local
- Deploy target: Ubuntu server + PM2 + Cloudflare Tunnel (KHÔNG phải Vercel)
- Docs cấu trúc dữ liệu: `docs/DATA_FLOW.md`

---

## Template cho lần sau (đừng xóa)

```markdown
## Lần cập nhật cuối
**Ngày:** YYYY-MM-DD
**Trạng thái:** [1 câu mô tả]

## Đang làm dở
- [ ] Task 1 — mô tả
- [x] Task đã xong

## File vừa sửa
- path/to/file.ts — đã làm gì

## Lệnh tiếp theo khi resume
```bash
lệnh cụ thể
```
```
