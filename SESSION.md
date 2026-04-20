# SESSION.md — Checkpoint phiên làm việc

> Claude tự đọc file này đầu mỗi phiên để biết việc đang dở.

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** MES Proterial — luồng nhập kho đã xanh E2E 14/14 bước, IQC fail ghi NG-01 đúng, đã commit

## 📍 Project location (KHÔNG phải trong C:\ThiemAICamp)

```
C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend
```

- Stack: Node.js (Express) + PostgreSQL + WebSocket
- Git repo local (KHÔNG có remote origin)
- Commit cuối: `a5ef13b feat(iqc): QC fail ghi NG-01 vào inventory + transaction log; E2E test luồng nhập kho xanh 14/14 bước`

## ✅ Đã xong trong phiên này (đã commit `a5ef13b`)

- Migration 026 đã apply vào DB (`v_material_stock`, `v_supply_chain_trace`, `v_stock_movement_30d`, `assert_issuable_location()`)
- `routes/iqc.js`: IQC fail → trừ QC_HOLD, cộng `NG-01` vào `inventory_stocks`, log `inventory_transactions (QC_FAIL_TO_NG)` → `v_material_stock.ng_qty` phản ánh đúng
- `scripts/apply_026_only.js`: helper áp migration 026 idempotent
- `scripts/test_e2e_receiving.js`: E2E test 14 bước chạy PASS:
  - Low-stock → PR tự tạo → duyệt → PO → GR (QC_HOLD) → IQC pass (vào kho chính) / IQC fail (NG-01 + NCR) → NCR workflow close → direct-receive bypass → truy vết

## 🔥 Còn đang dở — cần làm tiếp

1. **UI dashboard WMS** — hiển thị breakdown `available / qc_hold / ng` (API `/api/wms/stock?breakdown=1` đã sẵn)
2. **UI `public/mod_iqc.html`** — chưa chắc đã nối đúng với các endpoint mới (start/items/result)
3. **UI `public/mod09_purchasing.html`** — thêm tab "Truy vết" gọi `/api/purchasing/traceability`
4. **UI `public/_nav.js` + `public/mod_warehouse.html`** — từ phiên cũ, cần rà lại
5. Tính năng cảnh báo real-time qua WebSocket khi stock xuống dưới reorder_point (nice-to-have)

## Blocker / Câu hỏi cần user quyết

Không có blocker. Backend ổn, cần push UI lên phase tiếp theo.

## Lệnh resume

```bash
cd "C:\Users\LEGION\Downloads\mes-complete-v2\mes-backend"
git log --oneline -5                          # xem commit mới nhất a5ef13b
npm start                                     # chạy server
node scripts/test_e2e_receiving.js            # chạy lại E2E (cần server up)
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
