import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { hasError = false, className = "", ...rest },
  ref
) {
  const base =
    "w-full h-12 rounded-lg border px-4 text-base bg-white placeholder:text-slate-400 " +
    "focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] focus:border-transparent";
  const border = hasError
    ? "border-[var(--color-danger)]"
    : "border-slate-300";
  return <input ref={ref} className={`${base} ${border} ${className}`} {...rest} />;
});
