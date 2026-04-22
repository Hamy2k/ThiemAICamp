"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { LeadDetailResponse } from "@/types/api";

const TIER_STYLES: Record<"hot" | "warm" | "cold", string> = {
  hot: "bg-red-50 text-red-700 border-red-300",
  warm: "bg-amber-50 text-amber-700 border-amber-300",
  cold: "bg-slate-100 text-slate-600 border-slate-300",
};

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [token, setToken] = useState<string | null>(null);
  const [leadId, setLeadId] = useState<string | null>(null);
  const [lead, setLead] = useState<LeadDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      setToken(window.localStorage.getItem("rl.hr.token"));
    } catch {}
    params.then((p) => setLeadId(p.id));
  }, [params]);

  useEffect(() => {
    if (!token || !leadId) return;
    api
      .getLead(leadId, token)
      .then(setLead)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Không tải được chi tiết.");
      });
  }, [token, leadId]);

  if (!token || !leadId) {
    return (
      <main className="mx-auto max-w-md px-4 py-10">
        <p className="text-sm text-[var(--color-ink-muted)]">Đang tải…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-md px-4 py-10">
        <a href="/admin/leads" className="text-sm text-[var(--color-brand-dark)] underline">
          ← Về danh sách
        </a>
        <p className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      </main>
    );
  }

  if (!lead) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-8">
        <div className="space-y-3">
          <div className="h-8 w-1/3 animate-pulse rounded bg-slate-200" />
          <div className="h-24 animate-pulse rounded bg-slate-100" />
          <div className="h-40 animate-pulse rounded bg-slate-100" />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <a href="/admin/leads" className="mb-3 inline-block text-sm text-[var(--color-brand-dark)] underline">
        ← Về danh sách
      </a>

      <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-[var(--color-ink)]">{lead.full_name}</h1>
              {lead.tier && (
                <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${TIER_STYLES[lead.tier]}`}>
                  {lead.tier}
                </span>
              )}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
              <a href={`tel:${lead.phone_full}`} className="font-mono text-[var(--color-brand-dark)] underline">
                {lead.phone_full}
              </a>
              <button
                onClick={() => navigator.clipboard.writeText(lead.phone_full)}
                className="rounded-md border border-slate-300 bg-white px-2 py-0.5 text-xs hover:bg-slate-50"
              >
                Copy SĐT
              </button>
            </div>
            {lead.area_normalized && (
              <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
                📍 {lead.area_normalized}
                {lead.distance_km !== null && (
                  <span className="ml-2">· cách công ty {Number(lead.distance_km).toFixed(1)} km</span>
                )}
              </p>
            )}
            <p className="mt-1 text-xs text-[var(--color-ink-muted)]">
              Đăng ký: {new Date(lead.created_at).toLocaleString("vi-VN")}
            </p>
          </div>
          {lead.score_total !== null && (
            <div className="flex-shrink-0 rounded-xl bg-slate-50 px-5 py-3 text-center">
              <div className="text-4xl font-bold text-[var(--color-ink)]">
                {Math.round(Number(lead.score_total))}
              </div>
              <div className="text-[11px] uppercase tracking-wider text-[var(--color-ink-muted)]">/ 100</div>
            </div>
          )}
        </div>

        {lead.explanation_vi && (
          <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm italic text-[var(--color-ink)]">
            💭 {lead.explanation_vi}
          </p>
        )}
      </section>

      {lead.score_breakdown && (
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
            Chấm điểm
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <ScoreCell label="Địa điểm" value={Number(lead.score_breakdown.location)} weight="40%" />
            <ScoreCell label="Ca làm" value={Number(lead.score_breakdown.availability)} weight="30%" />
            <ScoreCell label="Kinh nghiệm" value={Number(lead.score_breakdown.experience)} weight="20%" />
            <ScoreCell label="Trả lời" value={Number(lead.score_breakdown.response_quality)} weight="10%" />
          </div>
        </section>
      )}

      {lead.attribution && (
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
            Nguồn đăng ký
          </h2>
          <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            <Row label="Kênh" value={lead.attribution.source_channel} />
            <Row label="Nhóm" value={lead.attribution.source_display_name ?? "—"} />
            <Row label="Style bài" value={lead.attribution.variant_hook_style ?? "—"} />
            <Row label="Tracking ID" value={lead.attribution.tracking_id ?? "—"} mono />
            <Row label="Việc làm" value={lead.job_title ?? "—"} />
          </dl>
        </section>
      )}

      {lead.transcript.length > 0 && (
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
            Hội thoại ({lead.turn_count ?? 0}/5 lượt · {lead.session_status})
          </h2>
          <div className="space-y-3">
            {lead.transcript.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={
                    m.role === "user"
                      ? "max-w-[85%] rounded-2xl rounded-br-sm bg-[var(--color-brand-dark)] px-4 py-2.5 text-white"
                      : "max-w-[85%] rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 text-[var(--color-ink)]"
                  }
                >
                  <p className="text-sm leading-relaxed whitespace-pre-line">{m.content}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {lead.extracted_data && Object.keys(lead.extracted_data).length > 0 && (
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
            Thông tin AI trích xuất
          </h2>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs font-mono text-[var(--color-ink)]">
            {JSON.stringify(lead.extracted_data, null, 2)}
          </pre>
        </section>
      )}

      {lead.consent_version && (
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-2 text-sm font-bold uppercase tracking-wider text-[var(--color-ink-muted)]">
            Đồng thuận PDPD
          </h2>
          <p className="text-sm text-[var(--color-ink-muted)]">
            Phiên bản: <span className="font-mono">{lead.consent_version}</span>
            {lead.consent_granted_at && (
              <> · Đồng ý lúc: {new Date(lead.consent_granted_at).toLocaleString("vi-VN")}</>
            )}
          </p>
        </section>
      )}
    </main>
  );
}

function ScoreCell({ label, value, weight }: { label: string; value: number; weight: string }) {
  const color = value >= 80 ? "text-green-700" : value >= 50 ? "text-amber-700" : "text-red-700";
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-center">
      <div className={`text-2xl font-bold ${color}`}>{Math.round(value)}</div>
      <div className="mt-0.5 text-xs font-medium text-[var(--color-ink)]">{label}</div>
      <div className="text-[10px] text-[var(--color-ink-muted)]">trọng số {weight}</div>
    </div>
  );
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline gap-2">
      <dt className="min-w-[90px] text-xs uppercase tracking-wider text-[var(--color-ink-muted)]">
        {label}
      </dt>
      <dd className={mono ? "font-mono text-sm" : "text-sm"}>{value}</dd>
    </div>
  );
}
