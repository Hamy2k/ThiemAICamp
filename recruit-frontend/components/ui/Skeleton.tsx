interface SkeletonProps {
  className?: string;
}

/** Gray skeleton bar — use instead of spinner on slow 3G. */
export function Skeleton({ className = "h-4 w-full" }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded bg-slate-200 ${className}`}
    />
  );
}
