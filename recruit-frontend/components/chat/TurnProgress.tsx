interface TurnProgressProps {
  current: number;
  max: number;
}

export function TurnProgress({ current, max }: TurnProgressProps) {
  const pct = Math.min(100, Math.round((current / max) * 100));
  return (
    <div className="flex items-center gap-3">
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={current}
        aria-label={`Câu ${current}/${max}`}
        className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200"
      >
        <div
          className="h-full bg-[var(--color-brand-dark)] transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-[var(--color-ink-muted)]">
        {current}/{max}
      </span>
    </div>
  );
}
