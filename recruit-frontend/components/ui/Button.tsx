import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "md" | "lg";
  fullWidth?: boolean;
  children: ReactNode;
}

const VARIANT: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-[var(--color-brand-dark)] text-white hover:brightness-110 active:brightness-95 disabled:bg-slate-400",
  secondary:
    "bg-white border border-slate-300 text-[var(--color-ink)] hover:bg-slate-50 active:bg-slate-100",
  ghost: "bg-transparent text-[var(--color-ink-muted)] hover:bg-slate-100",
};

const SIZE: Record<NonNullable<ButtonProps["size"]>, string> = {
  md: "h-11 px-4 text-sm",
  lg: "h-14 px-6 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const width = fullWidth ? "w-full" : "";
  const base =
    "inline-flex items-center justify-center rounded-lg font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand)] focus-visible:ring-offset-2 disabled:cursor-not-allowed";
  return (
    <button
      {...rest}
      className={`${base} ${VARIANT[variant]} ${SIZE[size]} ${width} ${className}`}
    >
      {children}
    </button>
  );
}
