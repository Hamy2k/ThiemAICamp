interface FieldErrorProps {
  id?: string;
  message?: string;
}

/**
 * Inline field error — red, icon + text.
 * Uses aria-live so screen readers announce the message.
 */
export function FieldError({ id, message }: FieldErrorProps) {
  if (!message) return null;
  return (
    <p
      id={id}
      role="alert"
      aria-live="polite"
      className="mt-1.5 flex items-start gap-1.5 text-sm text-[var(--color-danger)]"
    >
      <span aria-hidden="true">⚠</span>
      <span>{message}</span>
    </p>
  );
}
