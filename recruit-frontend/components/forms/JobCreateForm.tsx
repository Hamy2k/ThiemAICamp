"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { api, ApiError } from "@/lib/api";
import { jobCreateSchema, type JobCreateFormValues } from "@/lib/validation";
import type { JobResponse, ShareKitItem } from "@/types/api";
import { Button } from "@/components/ui/Button";
import { FieldError } from "@/components/ui/FieldError";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

interface Props {
  token: string;
}

export function JobCreateForm({ token }: Props) {
  const [createdJob, setCreatedJob] = useState<JobResponse | null>(null);
  const [shareKit, setShareKit] = useState<ShareKitItem[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<JobCreateFormValues>({
    resolver: zodResolver(jobCreateSchema),
    defaultValues: {
      company_name_override: "",
      title: "",
      salary_text: "",
      location_raw: "",
      requirements_raw: "",
      target_hires: 1,
    },
  });

  async function onSubmit(values: JobCreateFormValues) {
    setServerError(null);
    try {
      const job = await api.createJob(
        {
          company_name_override: values.company_name_override || undefined,
          title: values.title,
          salary_text: values.salary_text || undefined,
          location_raw: values.location_raw,
          requirements_raw: values.requirements_raw || undefined,
          shift: values.shift,
          start_date: values.start_date || undefined,
          target_hires: values.target_hires,
        },
        token
      );
      setCreatedJob(job);
      setGenerating(true);
      const res = await api.generateContent(job.id, token);
      setShareKit(res.share_kit);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Không tạo được việc làm.");
    } finally {
      setGenerating(false);
    }
  }

  if (createdJob) {
    return <JobCreatedView job={createdJob} shareKit={shareKit} generating={generating} />;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div>
        <Label htmlFor="company_name_override">
          Tên công ty / thương hiệu (tùy chọn)
        </Label>
        <Input
          id="company_name_override"
          placeholder="VD: Công ty TNHH ABC Plastics"
          hasError={!!errors.company_name_override}
          {...register("company_name_override")}
        />
        <p className="mt-1 text-xs text-[var(--color-ink-muted)]">
          Để trống = dùng tên công ty của bạn. Điền nếu đang tuyển hộ khách hàng khác.
        </p>
        <FieldError message={errors.company_name_override?.message} />
      </div>

      <div>
        <Label htmlFor="title" required>
          Chức danh
        </Label>
        <Input
          id="title"
          placeholder="VD: Công nhân vận hành máy ép nhựa"
          hasError={!!errors.title}
          {...register("title")}
        />
        <FieldError message={errors.title?.message} />
      </div>

      <div>
        <Label htmlFor="salary">Lương (tự do, AI sẽ parse)</Label>
        <Input
          id="salary"
          placeholder="VD: 8-10 triệu + tăng ca"
          hasError={!!errors.salary_text}
          {...register("salary_text")}
        />
        <FieldError message={errors.salary_text?.message} />
      </div>

      <div>
        <Label htmlFor="location" required>
          Địa điểm
        </Label>
        <Input
          id="location"
          placeholder="VD: KCN Sóng Thần, Dĩ An, Bình Dương"
          hasError={!!errors.location_raw}
          {...register("location_raw")}
        />
        <FieldError message={errors.location_raw?.message} />
      </div>

      <div>
        <Label htmlFor="shift">Ca làm</Label>
        <select
          id="shift"
          className="h-12 w-full rounded-lg border border-slate-300 bg-white px-4 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
          {...register("shift")}
        >
          <option value="">(không chọn)</option>
          <option value="day">Ca ngày</option>
          <option value="night">Ca đêm</option>
          <option value="rotating">Ca xoay</option>
          <option value="flexible">Linh hoạt</option>
        </select>
      </div>

      <div>
        <Label htmlFor="requirements">Yêu cầu thêm</Label>
        <textarea
          id="requirements"
          rows={3}
          placeholder="VD: Nam 18-35t, không cần kinh nghiệm, đi làm ca đêm được"
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
          {...register("requirements_raw")}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="start_date">Ngày bắt đầu</Label>
          <Input id="start_date" type="date" {...register("start_date")} />
        </div>
        <div>
          <Label htmlFor="target">Số lượng tuyển</Label>
          <Input
            id="target"
            type="number"
            inputMode="numeric"
            min={1}
            max={500}
            hasError={!!errors.target_hires}
            {...register("target_hires", { valueAsNumber: true })}
          />
          <FieldError message={errors.target_hires?.message} />
        </div>
      </div>

      {serverError && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--color-danger)]/30 bg-red-50 p-3 text-sm text-[var(--color-danger)]"
        >
          {serverError}
        </div>
      )}

      <Button type="submit" variant="primary" size="lg" fullWidth disabled={isSubmitting}>
        {isSubmitting ? "Đang tạo…" : "TẠO VIỆC LÀM + SINH BÀI ĐĂNG"}
      </Button>
    </form>
  );
}

function JobCreatedView({
  job,
  shareKit,
  generating,
}: {
  job: JobResponse;
  shareKit: ShareKitItem[] | null;
  generating: boolean;
}) {
  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-green-200 bg-green-50 p-4">
        <p className="text-sm font-medium text-green-800">
          ✓ Đã tạo việc làm: <strong>{job.title}</strong>
        </p>
        <p className="mt-1 text-xs text-green-700">
          {job.location_district}, {job.location_city} · trạng thái: {job.status}
        </p>
        {job.ai_warnings && job.ai_warnings.length > 0 && (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
            <p className="font-semibold">Lưu ý từ AI:</p>
            <ul className="mt-1 list-disc pl-5">
              {job.ai_warnings.map((w, i) => (
                <li key={i}>{w.message}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">Share Kit</h2>
          {shareKit && (
            <span className="text-xs text-[var(--color-ink-muted)]">
              {shareKit.length} link theo dõi
            </span>
          )}
        </div>
        <p className="mb-4 text-sm text-[var(--color-ink-muted)]">
          Mỗi card dưới là 1 bài đăng + link theo dõi riêng cho từng nhóm/nguồn.
          Bấm <strong>Copy</strong> → sang Facebook/Zalo → paste → đăng.
        </p>

        {generating && (
          <p className="rounded-lg bg-white p-4 text-sm text-[var(--color-ink-muted)] ring-1 ring-slate-200">
            AI đang viết bài + tạo link… (~5-15s)
          </p>
        )}

        {shareKit && (
          <div className="space-y-3">
            {shareKit.map((item) => (
              <ShareCard key={item.tracking_id} item={item} />
            ))}
          </div>
        )}

        {!generating && shareKit && shareKit.length === 0 && (
          <p className="rounded-lg bg-amber-50 p-4 text-sm text-amber-900">
            Chưa có nguồn nào đăng ký. Đăng ký FB group / Zalo source trước khi tạo việc.
          </p>
        )}
      </section>

      <a
        href="/admin/jobs"
        className="inline-block text-sm font-medium text-[var(--color-brand-dark)] underline"
      >
        ← Về danh sách việc làm
      </a>
    </div>
  );
}

function ShareCard({ item }: { item: ShareKitItem }) {
  const [copied, setCopied] = useState(false);

  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const landingUrl = `${origin}/apply?tracking_id=${encodeURIComponent(item.tracking_id)}`;
  const finalText = item.copy_with_placeholder.replaceAll("{link}", landingUrl);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  const posterAbsoluteUrl = item.poster_url ? `${apiBase}${item.poster_url}` : null;

  async function copyToClipboard() {
    try {
      await navigator.clipboard.writeText(finalText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      /* noop */
    }
  }

  async function downloadPoster() {
    if (!posterAbsoluteUrl) return;
    try {
      const r = await fetch(posterAbsoluteUrl);
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `poster-${item.tracking_id}.png`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      window.open(posterAbsoluteUrl, "_blank");
    }
  }

  const channelIcon: Record<string, string> = {
    facebook: "📘",
    zalo: "💬",
    direct: "🔗",
    unknown: "📍",
    other: "📍",
  };

  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <header className="flex items-center justify-between gap-3 border-b border-slate-100 bg-slate-50 px-4 py-2.5">
        <div className="flex items-center gap-2 min-w-0">
          <span aria-hidden="true" className="text-lg leading-none flex-shrink-0">
            {channelIcon[item.source_channel] ?? "📍"}
          </span>
          <span className="truncate text-sm font-semibold text-[var(--color-ink)]">
            {item.source_display_name}
          </span>
        </div>
        <div className="flex flex-shrink-0 items-center gap-1.5">
          {posterAbsoluteUrl && (
            <button
              type="button"
              onClick={downloadPoster}
              className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-[var(--color-ink)] hover:bg-slate-50"
              title="Tải poster về máy để đính kèm khi đăng bài"
            >
              🖼 Tải ảnh
            </button>
          )}
          <button
            type="button"
            onClick={copyToClipboard}
            className={
              copied
                ? "rounded-md border border-green-600 bg-green-600 px-3 py-1.5 text-xs font-semibold text-white"
                : "rounded-md border border-[var(--color-brand-dark)] bg-[var(--color-brand-dark)] px-3 py-1.5 text-xs font-semibold text-white hover:brightness-110"
            }
          >
            {copied ? "✓ Đã copy" : "📋 Copy bài"}
          </button>
        </div>
      </header>

      {posterAbsoluteUrl && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={posterAbsoluteUrl}
          alt={`Poster ${item.source_display_name}`}
          className="w-full aspect-[1200/630] object-cover border-b border-slate-100"
        />
      )}

      <pre className="whitespace-pre-wrap break-words font-sans px-4 py-3 text-sm leading-relaxed text-[var(--color-ink)]">
        {finalText}
      </pre>
      <footer className="border-t border-slate-100 bg-slate-50 px-4 py-2 text-[11px] text-[var(--color-ink-muted)] font-mono">
        Link: <a href={landingUrl} target="_blank" rel="noreferrer" className="underline">
          {landingUrl}
        </a>
      </footer>
    </article>
  );
}
