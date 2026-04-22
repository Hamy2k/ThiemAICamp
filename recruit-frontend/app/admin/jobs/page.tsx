"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { JobListItem } from "@/types/api";
import { AdminNav } from "@/components/admin/AdminNav";

const STATUS_STYLE: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-amber-100 text-amber-700",
  closed: "bg-slate-100 text-slate-500",
};

export default function JobsListPage() {
  const [token, setToken] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobListItem[] | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      setToken(window.localStorage.getItem("rl.hr.token"));
    } catch {}
  }, []);

  useEffect(() => {
    if (!token) return;
    api
      .listJobs(token, { status: filter === "all" ? undefined : filter })
      .then((r) => setJobs(r.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Không tải được danh sách."));
  }, [token, filter]);

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-4 py-10">
        <p className="text-sm text-[var(--color-ink-muted)]">
          Cần đăng nhập HR tại{" "}
          <a href="/admin/jobs/new" className="underline text-[var(--color-brand-dark)]">
            /admin/jobs/new
          </a>
          .
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <AdminNav />
      <header className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Việc làm</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            {jobs ? `${jobs.length} việc` : "Đang tải…"}
          </p>
        </div>
        <a
          href="/admin/jobs/new"
          className="flex-shrink-0 rounded-lg bg-[var(--color-brand-dark)] px-4 py-2 text-sm font-semibold text-white"
        >
          + Tạo mới
        </a>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {["all", "active", "draft", "paused", "closed"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={
              filter === s
                ? "rounded-lg bg-[var(--color-brand-dark)] px-4 py-2 text-sm font-semibold text-white"
                : "rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm"
            }
          >
            {s === "all" ? "Tất cả" : s}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {jobs === null && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {jobs && jobs.length === 0 && (
        <div className="rounded-2xl bg-white p-8 text-center">
          <p className="text-sm text-[var(--color-ink-muted)]">Chưa có việc làm.</p>
        </div>
      )}

      {jobs && jobs.length > 0 && (
        <ul className="space-y-2">
          {jobs.map((j) => (
            <li
              key={j.id}
              className="rounded-xl border border-slate-200 bg-white p-4 hover:border-[var(--color-brand-dark)] transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="truncate font-semibold text-[var(--color-ink)]">{j.title}</h3>
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${STATUS_STYLE[j.status] ?? ""}`}
                    >
                      {j.status}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-[var(--color-ink-muted)]">
                    📍 {j.location_short} · 💰 {j.salary_text ?? "—"}
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-ink-muted)]">
                    Cần tuyển: <strong>{j.target_hires}</strong> · tạo{" "}
                    {new Date(j.created_at).toLocaleDateString("vi-VN")}
                  </p>
                  <div className="mt-2 flex gap-2">
                    <a
                      href={`/admin/analytics?job_id=${j.id}`}
                      className="text-xs text-[var(--color-brand-dark)] underline"
                    >
                      Xem phân tích →
                    </a>
                    <a
                      href={`/admin/leads?job_id=${j.id}`}
                      className="text-xs text-[var(--color-brand-dark)] underline"
                    >
                      Ứng viên →
                    </a>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <Stat value={j.total_clicks} label="lượt xem" color="text-slate-600" />
                  <Stat value={j.lead_count} label="đăng ký" color="text-blue-600" />
                  <Stat value={j.qualified_count} label="đạt YC" color="text-green-600" />
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function Stat({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2 min-w-[64px]">
      <div className={`text-lg font-bold ${color}`}>{value}</div>
      <div className="text-[10px] text-[var(--color-ink-muted)]">{label}</div>
    </div>
  );
}
