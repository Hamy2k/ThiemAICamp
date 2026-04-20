# SESSION.md — Checkpoint phiên làm việc

> File này giúp Claude tiếp tục đúng chỗ sau khi tắt máy.
> Claude sẽ tự đọc file này đầu mỗi phiên.

## Lần cập nhật cuối

**Ngày:** 2026-04-20
**Trạng thái:** Setup hệ thống lưu phiên — chưa bắt đầu MES

## Đang làm dở

- [ ] **MES (Manufacturing Execution System)** — chờ user cung cấp spec:
  - Quản lý gì? (đơn hàng / máy móc / công nhân / kho / chất lượng)
  - Stack? (Next.js + Postgres hay Python FastAPI)
  - Deploy Vercel hay self-host

## File vừa sửa

- `C:\Users\LEGION\.claude\projects\C--ThiemAICamp\memory\*.md` — khởi tạo memory system
- `SESSION.md` — file này

## Lệnh tiếp theo khi resume

```bash
cd C:\ThiemAICamp
claude --continue
```

Sau đó nói với Claude: **"tiếp tục MES"** — em sẽ đọc SESSION.md và hỏi spec.

## Blocker / Ghi chú

- Chưa có code MES nào trong workspace (đã kiểm tra git log, filesystem, conversation logs)
- User cần quyết định scope và stack trước khi code

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

## Blocker / Ghi chú
- ...
```
