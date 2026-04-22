/**
 * HR jobs list. MVP: server-side rendered using stored token via cookie (Phase 4)
 * or client-side fetch with token from localStorage.
 *
 * Phase 3 MVP keeps it simple: static shell + client list, since HR backend
 * list endpoint is not in Phase 1 spec (API_MISMATCH flagged).
 */
export default function JobsListPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Việc làm</h1>
        <a
          href="/admin/jobs/new"
          className="rounded-lg bg-[var(--color-brand-dark)] px-4 py-2 text-sm font-semibold text-white"
        >
          + Tạo mới
        </a>
      </header>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center">
        <p className="mb-2 text-sm font-medium text-[var(--color-ink)]">
          Danh sách việc làm
        </p>
        <p className="text-sm text-[var(--color-ink-muted)]">
          API_MISMATCH: Phase 1 chưa có endpoint GET /v1/hr/jobs. Phase 4 sẽ thêm.
          <br />
          Hiện tại, dùng đường dẫn trực tiếp{" "}
          <code className="rounded bg-slate-100 px-1">/admin/leads/[id]</code> khi có id.
        </p>
      </div>
    </main>
  );
}
