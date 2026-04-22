"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { LeadListItem } from "@/types/api";
import { AdminNav } from "@/components/admin/AdminNav";

type TierFilter = "all" | "hot" | "warm" | "cold";

const TIER_STYLES: Record<"hot" | "warm" | "cold", string> = {
  hot: "bg-red-50 text-red-700 border-red-300",
  warm: "bg-amber-50 text-amber-700 border-amber-300",
  cold: "bg-slate-100 text-slate-600 border-slate-300",
};

export default function LeadsListPage() {
  const [token, setToken] = useState<string | null>(null);
  const [items, setItems] = useState<LeadListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<TierFilter>("all");
  const [jobFilter, setJobFilter] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      setToken(window.localStorage.getItem("rl.hr.token"));
    } catch {}
    const params = new URLSearchParams(window.location.search);
    const jid = params.get("job_id");
    if (jid) setJobFilter(jid);
  }, []);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    api
      .listLeads(token, {
        tier: filter === "all" ? undefined : filter,
        job_id: jobFilter || undefined,
      })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Không tải được danh sách.");
      })
      .finally(() => setLoading(false));
  }, [token, filter, jobFilter]);

  function downloadCsv() {
    if (!items || items.length === 0) return;
    const header = [
      "full_name",
      "phone_masked",
      "tier",
      "score_total",
      "area",
      "distance_km",
      "source",
      "job_title",
      "created_at",
    ];
    const rows = items.map((it) => [
      escapeCsv(it.full_name),
      escapeCsv(it.phone_masked),
      it.tier ?? "",
      it.score_total?.toString() ?? "",
      escapeCsv(it.area ?? ""),
      it.distance_km?.toString() ?? "",
      escapeCsv(it.source_display_name ?? ""),
      escapeCsv(it.job_title ?? ""),
      it.created_at,
    ]);
    // BOM + CRLF for Excel VN compatibility
    const csv = "\uFEFF" + [header, ...rows].map((r) => r.join(",")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ung-vien-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

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

      <header className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Danh sách ứng viên</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Tổng: {total} ứng viên
            {jobFilter && (
              <span>
                {" "}· lọc theo 1 việc{" "}
                <button
                  onClick={() => setJobFilter("")}
                  className="underline text-[var(--color-brand-dark)]"
                >
                  (bỏ lọc)
                </button>
              </span>
            )}
          </p>
        </div>
        <button
          onClick={downloadCsv}
          disabled={!items || items.length === 0}
          className="flex-shrink-0 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
        >
          📥 Xuất CSV
        </button>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {(["all", "hot", "warm", "cold"] as TierFilter[]).map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={
              filter === t
                ? "rounded-lg bg-[var(--color-brand-dark)] px-4 py-2 text-sm font-semibold text-white"
                : "rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm"
            }
          >
            {t === "all" ? "Tất cả" : t.toUpperCase()}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {!loading && items && items.length === 0 && (
        <div className="rounded-2xl bg-white p-8 text-center">
          <p className="text-sm text-[var(--color-ink-muted)]">
            Chưa có ứng viên nào {filter !== "all" ? `ở tier ${filter.toUpperCase()}` : ""}.
          </p>
        </div>
      )}

      {!loading && items && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.lead_id}>
              <a
                href={`/admin/leads/${item.lead_id}`}
                className="block rounded-xl border border-slate-200 bg-white p-4 hover:border-[var(--color-brand-dark)] hover:shadow-sm transition"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="truncate font-semibold text-[var(--color-ink)]">
                        {item.full_name}
                      </h3>
                      {item.tier && (
                        <span
                          className={`inline-block rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${TIER_STYLES[item.tier]}`}
                        >
                          {item.tier}
                        </span>
                      )}
                      {item.session_status === "in_progress" && (
                        <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-0.5 text-[10px] text-blue-700">
                          Đang chat
                        </span>
                      )}
                    </div>
                    <p className="mt-1 font-mono text-xs text-[var(--color-ink-muted)]">
                      {item.phone_masked}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-[var(--color-ink-muted)]">
                      {item.area && <span>📍 {item.area}</span>}
                      {item.source_display_name && <span>🔗 {item.source_display_name}</span>}
                      {item.distance_km !== null && (
                        <span>📏 {Number(item.distance_km).toFixed(1)} km</span>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    {item.score_total !== null ? (
                      <>
                        <div className="text-2xl font-bold text-[var(--color-ink)]">
                          {Math.round(Number(item.score_total))}
                        </div>
                        <div className="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)]">
                          /100
                        </div>
                      </>
                    ) : (
                      <div className="text-xs text-[var(--color-ink-muted)]">
                        chưa có điểm
                      </div>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-xs text-[var(--color-ink-muted)]">
                  {new Date(item.created_at).toLocaleString("vi-VN")}
                </p>
              </a>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function escapeCsv(s: string): string {
  if (s.includes(",") || s.includes("\"") || s.includes("\n")) {
    return `"${s.replaceAll("\"", "\"\"")}"`;
  }
  return s;
}
