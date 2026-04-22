"use client";

import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/admin/jobs", label: "Việc làm" },
  { href: "/admin/jobs/new", label: "+ Tạo việc" },
  { href: "/admin/leads", label: "Ứng viên" },
  { href: "/admin/sources", label: "Nguồn" },
  { href: "/admin/analytics", label: "Phân tích" },
];

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav className="mb-5 flex flex-wrap gap-3 border-b border-slate-200 pb-3 text-sm">
      {LINKS.map((l) => {
        const active = pathname === l.href || (l.href !== "/admin/jobs" && pathname.startsWith(l.href));
        return (
          <a
            key={l.href}
            href={l.href}
            className={
              active
                ? "font-bold text-[var(--color-ink)] border-b-2 border-[var(--color-brand-dark)] pb-2"
                : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] pb-2"
            }
          >
            {l.label}
          </a>
        );
      })}
    </nav>
  );
}
