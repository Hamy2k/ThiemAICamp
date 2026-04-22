"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { api, ApiError } from "@/lib/api";
import {
  screeningMessageSchema,
  type ScreeningMessageFormValues,
} from "@/lib/validation";
import {
  clearScreening,
  loadScreening,
  saveScreening,
  type StoredMessage,
} from "@/lib/storage";
import { Button } from "@/components/ui/Button";
import { FieldError } from "@/components/ui/FieldError";
import { MessageBubble } from "./MessageBubble";
import { TurnProgress } from "./TurnProgress";

interface Props {
  leadId: string;
  sessionId: string;
  firstMessage: string;
}

const MAX_TURNS = 5;

export function ScreeningChat({ leadId, sessionId, firstMessage }: Props) {
  const router = useRouter();
  const [messages, setMessages] = useState<StoredMessage[]>([
    { role: "assistant", content: firstMessage },
  ]);
  const [turnCount, setTurnCount] = useState(0);
  const [done, setDone] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ScreeningMessageFormValues>({
    resolver: zodResolver(screeningMessageSchema),
    defaultValues: { message: "" },
  });

  // Save-and-resume: restore from localStorage (if matches this lead)
  useEffect(() => {
    const stored = loadScreening(leadId);
    if (stored && stored.session_id === sessionId && stored.messages.length > 1) {
      setMessages(stored.messages);
      setTurnCount(stored.turn_count);
      setDone(stored.done);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leadId]);

  // Persist on every change
  useEffect(() => {
    saveScreening({
      lead_id: leadId,
      session_id: sessionId,
      messages,
      turn_count: turnCount,
      done,
      updated_at: Date.now(),
    });
  }, [leadId, sessionId, messages, turnCount, done]);

  // Scroll to latest message
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function onSubmit(values: ScreeningMessageFormValues) {
    setServerError(null);
    const userMsg: StoredMessage = { role: "user", content: values.message.trim() };
    setMessages((prev) => [...prev, userMsg]);
    reset({ message: "" });

    try {
      const res = await api.sendScreeningTurn({
        session_id: sessionId,
        message: values.message.trim(),
      });
      const assistantMsg: StoredMessage = { role: "assistant", content: res.reply };
      setMessages((prev) => [...prev, assistantMsg]);
      setTurnCount(res.turn_index);
      if (res.done || res.turns_remaining === 0) setDone(true);
    } catch (err) {
      if (err instanceof ApiError && err.code === "SCREENING_EXHAUSTED") {
        setDone(true);
        return;
      }
      const msg =
        err instanceof ApiError
          ? err.message
          : "Mất mạng một chút, anh/chị thử lại giúp em nhé.";
      setServerError(msg);
      // Remove optimistic user msg on error to let them retry
      setMessages((prev) => prev.slice(0, -1));
    }
  }

  async function onFinish() {
    setCompleting(true);
    setServerError(null);
    try {
      await api.completeScreening({ session_id: sessionId });
      clearScreening(leadId);
      router.push(`/success/${encodeURIComponent(leadId)}`);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : "Không hoàn tất được, anh/chị thử lại sau ít phút nhé.";
      setServerError(msg);
      setCompleting(false);
    }
  }

  return (
    <div className="flex h-[100dvh] flex-col bg-[var(--color-surface-muted)]">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-md">
          <p className="mb-2 text-sm font-medium text-[var(--color-ink)]">
            Trợ lý tuyển dụng
          </p>
          <TurnProgress current={Math.min(turnCount, MAX_TURNS)} max={MAX_TURNS} />
        </div>
      </header>

      {/* Messages */}
      <div
        ref={scrollRef}
        role="list"
        aria-live="polite"
        aria-label="Lịch sử trò chuyện"
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {messages.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} />
          ))}
          {isSubmitting && (
            <div className="flex justify-start" role="status" aria-label="AI đang trả lời">
              <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200">
                <span className="inline-flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.3s]" />
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input / finish bar */}
      <footer className="flex-shrink-0 border-t border-slate-200 bg-white px-4 py-3 pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto max-w-md">
          {serverError && (
            <p className="mb-2 text-sm text-[var(--color-danger)]" role="alert">
              {serverError}
            </p>
          )}
          {done ? (
            <Button
              onClick={onFinish}
              fullWidth
              size="lg"
              disabled={completing}
              aria-busy={completing}
            >
              {completing ? "Đang gửi…" : "HOÀN TẤT — GỬI CHO NHÀ TUYỂN DỤNG"}
            </Button>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex gap-2">
              <label htmlFor="msg-input" className="sr-only">
                Tin nhắn của bạn
              </label>
              <input
                id="msg-input"
                type="text"
                inputMode="text"
                autoComplete="off"
                autoCapitalize="sentences"
                placeholder="Nhập câu trả lời…"
                aria-invalid={errors.message ? "true" : "false"}
                className="h-12 flex-1 rounded-full border border-slate-300 bg-white px-4 text-base placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
                {...register("message")}
              />
              <Button
                type="submit"
                size="md"
                className="!h-12 !rounded-full !px-5"
                disabled={isSubmitting}
                aria-busy={isSubmitting}
              >
                Gửi
              </Button>
            </form>
          )}
          <FieldError message={errors.message?.message} />
        </div>
      </footer>
    </div>
  );
}
