import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tìm việc nhanh — Roman Recruit",
  description: "Đăng ký việc làm blue-collar trong 30 giây.",
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0369a1",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-[var(--color-surface-muted)] text-[var(--color-ink)] antialiased">
        {children}
      </body>
    </html>
  );
}
