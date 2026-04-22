"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { JobListItem } from "@/types/api";
import { AdminNav } from "@/components/admin/AdminNav";

interface SourceRow {
  source_channel: string;
  source_id: string | null;
  display_name: string;
  clicks: number;
  leads: number;
  qualified: number;
  ctr_pct: number | null;
  conversion_pct: number | null;
}
interface VariantRow {
  variant_id: string;
  variant_index: number;
  hook_style: string;
  clicks: number;
  leads: number;
  qualified: number;
  conversion_pct: number | null;
}

export default function AnalyticsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [jobId, setJobId] = useState<string>("");
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [variants, setVariants] = useState<VariantRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      setToken(window.localStorage.getItem("rl.hr.token"));
    } catch {}
    // Read initial job_id from URL
    const params = new URLSearchParams(window.location.search);
    const j = params.get("job_id");
    if (j) setJobId(j);
  }, []);

  useEffect(() => {
    if (!token) return;
    api.listJobs(token).then((r) => {
      setJobs(r.items);
      if (!jobId && r.items.length) setJobId(r.items[0]!.id);
    }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (!token || !jobId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      api.listSourceAnalytics(jobId, token),
      api.listVariantAnalytics(jobId, token),
    ])
      .then(([s, v]) => {
        setSources(s.rows);
        setVariants(v.rows);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Không tải được phân tích."))
      .finally(() => setLoading(false));
  }, [token, jobId]);

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-4 py-10">
        <p className="text-sm text-[var(--color-ink-muted)]">
          Cần đăng nhập HR.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <AdminNav />

      <header className="mb-5">
        <h1 className="text-2xl font-bold">Phân tích</h1>
        <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
          Nguồn nào hiệu quả? Bài viết nào convert cao?
        </p>
      </header>

      {/* Job selector */}
      <div className="mb-5">
        <label className="mb-1.5 block text-sm font-medium">Chọn việc làm</label>
        <select
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
        >
          {jobs.length === 0 && <option value="">(chưa có việc làm)</option>}
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title} ({j.status})
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="h-40 animate-pulse rounded-lg bg-slate-100" />
      )}

      {!loading && jobId && (
        <div className="space-y-6">
          <BarChartSection
            title="Nguồn đăng bài — click / đăng ký / đạt YC"
            rows={sources.map((s) => ({
              label: s.display_name,
              clicks: s.clicks,
              leads: s.leads,
              qualified: s.qualified,
              conv: s.conversion_pct,
            }))}
          />
          <BarChartSection
            title="Bài đăng (variant) — click / đăng ký / đạt YC"
            rows={variants.map((v) => ({
              label: `#${v.variant_index} ${v.hook_style}`,
              clicks: v.clicks,
              leads: v.leads,
              qualified: v.qualified,
              conv: v.conversion_pct,
            }))}
          />

          {/* Conversion funnel */}
          <FunnelSection sources={sources} />
        </div>
      )}
    </main>
  );
}

interface BarRow {
  label: string;
  clicks: number;
  leads: number;
  qualified: number;
  conv: number | null;
}

function BarChartSection({ title, rows }: { title: string; rows: BarRow[] }) {
  const max = Math.max(1, ...rows.flatMap((r) => [r.clicks, r.leads, r.qualified]));
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
        {title}
      </h2>
      {rows.length === 0 && (
        <p className="text-sm text-[var(--color-ink-muted)]">Chưa có dữ liệu cho việc làm này.</p>
      )}
      <ul className="space-y-3">
        {rows.map((r, i) => (
          <li key={i} className="space-y-1.5">
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="truncate font-medium">{r.label}</span>
              <span className="flex-shrink-0 text-xs text-[var(--color-ink-muted)]">
                {r.conv !== null ? `CR: ${r.conv.toFixed(1)}%` : "—"}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Bar value={r.clicks} max={max} color="bg-slate-300" />
              <Bar value={r.leads} max={max} color="bg-blue-500" />
              <Bar value={r.qualified} max={max} color="bg-green-600" />
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex gap-4 text-xs text-[var(--color-ink-muted)]">
        <Legend color="bg-slate-300" label="Clicks" />
        <Legend color="bg-blue-500" label="Leads" />
        <Legend color="bg-green-600" label="Đạt YC" />
      </div>
    </section>
  );
}

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = (value / max) * 100;
  return (
    <div className="flex-1 min-w-0">
      <div className="h-5 rounded bg-slate-100 overflow-hidden relative">
        <div
          className={`h-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
        {value > 0 && (
          <span className="absolute inset-0 flex items-center px-1.5 text-[10px] font-bold text-white mix-blend-difference">
            {value}
          </span>
        )}
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-block h-2.5 w-2.5 rounded ${color}`} />
      <span>{label}</span>
    </div>
  );
}

function FunnelSection({ sources }: { sources: SourceRow[] }) {
  const totalClicks = sources.reduce((s, r) => s + r.clicks, 0);
  const totalLeads = sources.reduce((s, r) => s + r.leads, 0);
  const totalQual = sources.reduce((s, r) => s + r.qualified, 0);

  const leadsPct = totalClicks ? (totalLeads / totalClicks) * 100 : 0;
  const qualPct = totalLeads ? (totalQual / totalLeads) * 100 : 0;
  const overallPct = totalClicks ? (totalQual / totalClicks) * 100 : 0;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
        Phễu chuyển đổi
      </h2>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="rounded-lg bg-slate-50 p-4">
          <div className="text-2xl font-bold text-slate-600">{totalClicks}</div>
          <div className="text-xs text-[var(--color-ink-muted)]">lượt xem</div>
        </div>
        <div className="rounded-lg bg-blue-50 p-4">
          <div className="text-2xl font-bold text-blue-700">{totalLeads}</div>
          <div className="text-xs text-blue-700/70">
            đăng ký
            <br />
            ({leadsPct.toFixed(1)}% click)
          </div>
        </div>
        <div className="rounded-lg bg-green-50 p-4">
          <div className="text-2xl font-bold text-green-700">{totalQual}</div>
          <div className="text-xs text-green-700/70">
            đạt YC
            <br />
            ({qualPct.toFixed(1)}% lead)
          </div>
        </div>
      </div>
      <p className="mt-4 text-center text-sm text-[var(--color-ink-muted)]">
        Click → Đạt YC:{" "}
        <strong className="text-[var(--color-ink)]">{overallPct.toFixed(2)}%</strong>
      </p>
    </section>
  );
}
