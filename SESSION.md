# SESSION.md — Checkpoint phiên làm việc

> Claude tự đọc file này đầu mỗi phiên để biết việc đang dở.

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** Đang xây MES cho Proterial Vietnam — 3 module: Kho, Mua hàng, IQC

## 📍 Project location (KHÔNG phải trong C:\ThiemAICamp)

```
C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend
```

- Stack: Node.js (Express) + PostgreSQL + WebSocket
- Git repo riêng, branch master
- Commit cuối: `3085ba0 fix(mod09): wire purchasing UI to real API`

## 🔥 Đang làm dở — có uncommitted changes

### Module IQC (Incoming Quality Control) — HOÀN TOÀN MỚI, chưa commit
- [ ] `db/migrations/025_iqc_ncr.sql` — schema: qc_sampling_config, qc_inspections, qc_inspection_items, coa_documents, ncr_reports, ncr_history, ng_inventory, view v_supplier_scorecard. Thêm QC_HOLD + NG-01 vào warehouse_locations.
- [ ] `routes/iqc.js` (473 dòng) — endpoints: GET /pending, /inspections, /inspections/:id, PATCH /inspections/:id, POST /inspections/:id/start, PUT /inspections/:id/items, POST /inspections/:id/result (pass/fail/partial_pass — auto-split inventory + tạo NCR), POST /inspections/:id/coa, /sampling-config, /scorecard, /dashboard
- [ ] `routes/ncr.js` — NCR workflow (draft→sent→ack→disposition→closed)
- [ ] `public/mod_iqc.html` — UI IQC

**Luồng IQC:**
1. GR về → stock vào QC_HOLD, qc_status='pending'
2. qc_inspections auto-tạo per GR line, priority tính tự động
3. IQC kiểm → pass: transfer QC_HOLD → kho chính; fail: → NG + auto-tạo NCR
4. NCR: draft → sent (IQC tự gửi) → supplier_ack → (return_supplier | conditional_accept) → closed
5. supplier_scorecard view update realtime (grade A/B/C/D theo ncr_rate_pct)

### Module WMS (Quản lý kho) — modified, chưa commit
- [ ] `routes/wms.js` (656 dòng)
- [ ] `public/mod_warehouse.html`

### Module Purchasing (Mua hàng) — modified, chưa commit
- [ ] `routes/purchasing.js` (919 dòng)
- [ ] `public/mod09_purchasing.html`

### File chung modified
- [ ] `public/_nav.js` — thêm menu IQC
- [ ] `server.js` — wire iqcRoutes + ncrRoutes (đã có, cần verify)
- [ ] `scripts/apply_new_migrations.js`

## Lệnh resume

```bash
cd "C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend"
git status                    # xem file đang modify
claude --continue             # tiếp tục phiên Claude
```

Nói với Claude: **"tiếp tục MES — phần đang dở"** → em đọc SESSION.md.

## Blocker / Câu hỏi cần user quyết

1. Đã chạy migration 025 vào PostgreSQL chưa? (nếu chưa cần `npm run db:init` hoặc chạy thủ công)
2. Test end-to-end IQC flow đã chạy chưa?
3. Khi nào commit batch IQC module? (4 file mới + migration)

## Context tham khảo

- Factory: Proterial Vietnam
- Tài khoản default: `admin` / `123456`
- Port: 3000
- DB: `mes_proterial` trên PostgreSQL local
- Deploy target: Ubuntu server + PM2 + Cloudflare Tunnel (KHÔNG phải Vercel)

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
