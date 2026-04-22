interface Props {
  params: Promise<{ lead_id: string }>;
}

export default async function SuccessPage({ params }: Props) {
  await params; // reserved for Phase 5 (show lead-specific details)

  return (
    <main className="mx-auto flex min-h-[100dvh] max-w-md flex-col items-center justify-center px-6 py-10 text-center">
      <div
        aria-hidden="true"
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100 text-4xl"
      >
        ✓
      </div>

      <h1 className="mb-3 text-2xl font-bold text-[var(--color-ink)]">
        Cảm ơn anh/chị!
      </h1>

      <p className="mb-5 text-base leading-relaxed text-[var(--color-ink-muted)]">
        Hồ sơ đã được gửi tới nhà tuyển dụng. Nhà tuyển dụng sẽ gọi lại trong vòng{" "}
        <strong className="text-[var(--color-ink)]">24 giờ</strong>.
      </p>

      <div className="mb-8 w-full rounded-2xl border border-slate-200 bg-white p-4 text-left">
        <h2 className="mb-2 text-sm font-semibold text-[var(--color-ink)]">
          Trong lúc chờ
        </h2>
        <ul className="space-y-1.5 text-sm text-[var(--color-ink-muted)]">
          <li>📱 Để ý điện thoại (có thể hiện số lạ).</li>
          <li>📝 Chuẩn bị giấy tờ: CCCD/CMND, sơ yếu (nếu có).</li>
          <li>💬 Nếu nhà tuyển dụng không gọi, anh/chị đăng ký việc khác giúp em.</li>
        </ul>
      </div>

      <a
        href="/apply"
        className="text-sm font-medium text-[var(--color-brand-dark)] underline"
      >
        Xem thêm việc khác
      </a>
    </main>
  );
}
