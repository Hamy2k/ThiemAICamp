interface MessageBubbleProps {
  role: "assistant" | "user";
  content: string;
}

/** Chat bubble — assistant left/gray, user right/brand. */
export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      role="listitem"
    >
      <div
        className={
          isUser
            ? "max-w-[85%] rounded-2xl rounded-br-sm bg-[var(--color-brand-dark)] px-4 py-2.5 text-white"
            : "max-w-[85%] rounded-2xl rounded-bl-sm bg-white px-4 py-2.5 text-[var(--color-ink)] shadow-sm ring-1 ring-slate-200"
        }
      >
        <p className="text-sm leading-relaxed whitespace-pre-line">{content}</p>
      </div>
    </div>
  );
}
