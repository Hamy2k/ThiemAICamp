import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { LandingForm } from "@/components/forms/LandingForm";
import type { PublicJobLanding } from "@/types/api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

interface Props {
  searchParams: Promise<{ tracking_id?: string; job_id?: string; source?: string }>;
}

async function fetchJob(trackingId: string): Promise<PublicJobLanding | { error: string }> {
  try {
    return await api.getPublicJob(trackingId);
  } catch (err) {
    if (err instanceof ApiError) return { error: err.message };
    return { error: "Không tải được thông tin việc làm." };
  }
}

export default async function ApplyPage({ searchParams }: Props) {
  const params = await searchParams;
  const trackingId = params.tracking_id ?? null;
  const consentVersion =
    process.env.NEXT_PUBLIC_CONSENT_VERSION ?? "v1.0-2026-04";

  const job = trackingId ? await fetchJob(trackingId) : null;

  return (
    <main className="mx-auto w-full max-w-md px-4 pb-28 pt-6 md:max-w-lg md:pb-10">
      <header className="mb-4">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          Đăng ký việc làm
        </p>
      </header>

      {/* Job summary */}
      <section
        aria-label="Thông tin việc làm"
        className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        {!job || "error" in job ? (
          <JobUnavailable message={job && "error" in job ? job.error : undefined} />
        ) : (
          <JobCard job={job} />
        )}
      </section>

      {/* Form */}
      <section aria-label="Mẫu đăng ký" className="rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-lg font-bold text-[var(--color-ink)]">
          Điền thông tin — chỉ 3 ô, 30 giây
        </h2>
        <LandingForm trackingId={trackingId} consentVersion={consentVersion} />
      </section>

      <footer className="mt-6 text-center text-xs text-[var(--color-ink-muted)]">
        Bằng việc đăng ký, anh/chị đồng ý cho chúng tôi liên hệ qua số điện thoại
        đã cung cấp.
      </footer>
    </main>
  );
}

function JobCard({ job }: { job: PublicJobLanding }) {
  return (
    <div>
      <h1 className="mb-3 text-xl font-bold leading-snug text-[var(--color-ink)]">
        {job.title}
      </h1>
      <dl className="space-y-2 text-sm">
        {job.salary_text && (
          <Row icon="💰" label="Lương" value={job.salary_text} />
        )}
        <Row icon="📍" label="Địa điểm" value={job.location_short} />
        {job.start_date && (
          <Row icon="📅" label="Bắt đầu" value={formatDate(job.start_date)} />
        )}
      </dl>
      {job.copy_vietnamese && (
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-[var(--color-ink-muted)]">
          {truncate(job.copy_vietnamese, 180)}
        </p>
      )}
    </div>
  );
}

function Row({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span aria-hidden="true" className="text-base">
        {icon}
      </span>
      <div>
        <dt className="sr-only">{label}</dt>
        <dd className="text-[var(--color-ink)]">{value}</dd>
      </div>
    </div>
  );
}

function JobUnavailable({ message }: { message?: string }) {
  return (
    <div className="text-sm text-[var(--color-ink-muted)]">
      <p className="mb-2 font-medium text-[var(--color-ink)]">
        Không thấy thông tin việc làm.
      </p>
      <p>{message ?? "Vui lòng kiểm tra lại link anh/chị nhận được."}</p>
      <p className="mt-3">
        Xem thêm việc tại{" "}
        <Link href="/" className="font-semibold text-[var(--color-brand-dark)] underline">
          trang chủ
        </Link>
        .
      </p>
    </div>
  );
}

function truncate(s: string, n: number): string {
  return s.length <= n ? s : s.slice(0, n - 1) + "…";
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return `${String(d.getDate()).padStart(2, "0")}/${String(
      d.getMonth() + 1
    ).padStart(2, "0")}/${d.getFullYear()}`;
  } catch {
    return iso;
  }
}
