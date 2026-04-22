"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { SourceItem } from "@/types/api";
import { AdminNav } from "@/components/admin/AdminNav";

const CHANNEL_LABEL: Record<string, string> = {
  facebook: "📘 Facebook",
  zalo: "💬 Zalo",
  direct: "🔗 Chia sẻ trực tiếp",
  other: "📍 Khác",
  unknown: "❓ Chưa rõ",
};

export default function SourcesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // Form fields
  const [channel, setChannel] = useState<string>("facebook");
  const [displayName, setDisplayName] = useState("");
  const [externalId, setExternalId] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    try {
      setToken(window.localStorage.getItem("rl.hr.token"));
    } catch {}
  }, []);

  useEffect(() => {
    if (!token) return;
    api
      .listSources(token)
      .then(setSources)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Không tải được danh sách."));
  }, [token]);

  async function onAddSource(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !displayName.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await api.createSource(
        {
          channel,
          display_name: displayName.trim(),
          external_id: externalId.trim() || undefined,
        },
        token
      );
      setSources((prev) => [created, ...(prev ?? [])]);
      setDisplayName("");
      setExternalId("");
      setShowAddForm(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thêm được nguồn.");
    } finally {
      setSaving(false);
    }
  }

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
    <main className="mx-auto max-w-3xl px-4 py-8">
      <AdminNav />

      <header className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Nguồn đăng bài</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Mỗi nguồn (Facebook group, Zalo channel…) → 1 link theo dõi riêng khi bạn tạo việc làm.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm((v) => !v)}
          className="flex-shrink-0 rounded-lg bg-[var(--color-brand-dark)] px-4 py-2 text-sm font-semibold text-white"
        >
          {showAddForm ? "Đóng" : "+ Thêm nguồn"}
        </button>
      </header>

      {showAddForm && (
        <form
          onSubmit={onAddSource}
          className="mb-5 space-y-3 rounded-2xl border border-slate-200 bg-white p-5"
        >
          <div>
            <label className="block text-sm font-medium mb-1.5" htmlFor="channel">
              Loại kênh
            </label>
            <select
              id="channel"
              className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
            >
              <option value="facebook">Facebook group / page</option>
              <option value="zalo">Zalo</option>
              <option value="direct">Chia sẻ trực tiếp (email/SMS)</option>
              <option value="other">Khác</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5" htmlFor="name">
              Tên hiển thị <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="VD: Việc làm TPHCM"
              className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5" htmlFor="extid">
              Mã ngoài (tùy chọn)
            </label>
            <input
              id="extid"
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              placeholder="VD: fb-vieclam-tphcm (để phân biệt)"
              className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
            />
          </div>

          <button
            type="submit"
            disabled={saving || !displayName.trim()}
            className="w-full rounded-lg bg-[var(--color-brand-dark)] px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {saving ? "Đang lưu…" : "Lưu nguồn"}
          </button>
        </form>
      )}

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {sources === null && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {sources && sources.length === 0 && (
        <div className="rounded-2xl bg-white p-8 text-center">
          <p className="text-sm text-[var(--color-ink-muted)]">Chưa có nguồn nào.</p>
          <p className="mt-2 text-xs text-[var(--color-ink-muted)]">
            Bấm "+ Thêm nguồn" để đăng ký FB group đầu tiên.
          </p>
        </div>
      )}

      {sources && sources.length > 0 && (
        <ul className="space-y-2">
          {sources.map((s) => (
            <li
              key={s.id}
              className="rounded-xl border border-slate-200 bg-white p-4 flex items-center justify-between"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-[var(--color-ink-muted)]">
                    {CHANNEL_LABEL[s.channel] ?? s.channel}
                  </span>
                </div>
                <p className="font-semibold text-[var(--color-ink)]">{s.display_name}</p>
                {s.external_id && (
                  <p className="mt-0.5 text-xs font-mono text-[var(--color-ink-muted)]">
                    {s.external_id}
                  </p>
                )}
              </div>
              <span className="flex-shrink-0 rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-700">
                đang dùng
              </span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
