import type { LabelHTMLAttributes, ReactNode } from "react";

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  children: ReactNode;
  required?: boolean;
}

export function Label({ children, required, className = "", ...rest }: LabelProps) {
  return (
    <label
      {...rest}
      className={`block text-sm font-medium text-[var(--color-ink)] mb-1.5 ${className}`}
    >
      {children}
      {required && <span className="ml-0.5 text-[var(--color-danger)]">*</span>}
    </label>
  );
}
