import { ScreeningChat } from "@/components/chat/ScreeningChat";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ lead_id: string }>;
  searchParams: Promise<{ session_id?: string; first_msg?: string }>;
}

/**
 * Screening chat route.
 * Expects session_id + first_msg in query (set by LandingForm redirect).
 * If missing, renders an error card with CTA back to /apply.
 */
export default async function ScreeningPage({ params, searchParams }: Props) {
  const { lead_id } = await params;
  const qs = await searchParams;
  const sessionId = qs.session_id;
  const firstMessage = qs.first_msg;

  if (!sessionId || !firstMessage) {
    return (
      <main className="mx-auto max-w-md px-4 py-10 text-center">
        <h1 className="mb-3 text-lg font-bold">Không mở được trò chuyện</h1>
        <p className="mb-6 text-sm text-[var(--color-ink-muted)]">
          Link này thiếu thông tin phiên. Vui lòng quay lại và đăng ký lại giúp em nhé.
        </p>
        <a
          href="/apply"
          className="inline-block rounded-lg bg-[var(--color-brand-dark)] px-6 py-3 font-semibold text-white"
        >
          Về trang đăng ký
        </a>
      </main>
    );
  }

  return (
    <ScreeningChat
      leadId={lead_id}
      sessionId={sessionId}
      firstMessage={firstMessage}
    />
  );
}
