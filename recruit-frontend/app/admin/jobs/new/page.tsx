"use client";

import { useEffect, useState } from "react";
import { JobCreateForm } from "@/components/forms/JobCreateForm";

/**
 * HR job create page. MVP auth: token entered once, cached in localStorage.
 * Phase 4 will swap for proper session cookie.
 */
export default function NewJobPage() {
  const [token, setToken] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    try {
      const cached = window.localStorage.getItem("rl.hr.token");
      if (cached) setToken(cached);
    } catch {
      // noop
    }
  }, []);

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-4 py-10">
        <h1 className="mb-3 text-xl font-bold">Đăng nhập HR</h1>
        <p className="mb-4 text-sm text-[var(--color-ink-muted)]">
          Nhập token API (MVP). Token sẽ lưu trong trình duyệt.
        </p>
        <input
          type="password"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Bearer token"
          className="mb-3 h-12 w-full rounded-lg border border-slate-300 px-4"
        />
        <button
          onClick={() => {
            if (input.trim()) {
              window.localStorage.setItem("rl.hr.token", input.trim());
              setToken(input.trim());
            }
          }}
          className="h-12 w-full rounded-lg bg-[var(--color-brand-dark)] font-semibold text-white"
        >
          Tiếp tục
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <header className="mb-6">
        <a
          href="/admin/jobs"
          className="mb-2 inline-block text-sm text-[var(--color-brand-dark)] underline"
        >
          ← Danh sách việc làm
        </a>
        <h1 className="text-2xl font-bold">Tạo việc làm mới</h1>
        <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
          4 trường — dưới 2 phút. AI sẽ tự sinh 5 bài đăng Facebook.
        </p>
      </header>
      <JobCreateForm token={token} />
    </main>
  );
}
