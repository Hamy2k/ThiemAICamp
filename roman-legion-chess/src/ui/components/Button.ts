/**
 * Roman Legion button — Tailwind DOM element.
 * Reuse across menu, settings, modals.
 *
 * Style: 2px gold border, obsidian-gradient interior, Cinzel uppercase text.
 * Hover: gold glow + brightness +10%.
 * Active: brightness -10% + inset shadow.
 * Disabled: opacity 0.4, no hover effect, lock icon if `locked`.
 */

export interface ButtonOptions {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  locked?: boolean;
  fullWidth?: boolean;
  variant?: 'primary' | 'ghost';
  icon?: string;
  size?: 'md' | 'lg';
  extraClass?: string;
}

export function createButton(opts: ButtonOptions): HTMLButtonElement {
  const btn = document.createElement('button');
  btn.type = 'button';
  const sizeClasses =
    opts.size === 'lg' ? 'py-4 text-lg' : 'py-3 text-base';
  const widthClass = opts.fullWidth ? 'w-full' : '';
  const variantClass =
    opts.variant === 'ghost'
      ? 'border-gold/60 bg-transparent hover:bg-gold/10'
      : '';

  btn.className = [
    'roman-btn',
    sizeClasses,
    widthClass,
    variantClass,
    opts.extraClass ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  btn.disabled = !!opts.disabled || !!opts.locked;

  const content = document.createElement('span');
  content.className = 'flex items-center justify-center gap-2';

  if (opts.icon) {
    const ic = document.createElement('span');
    ic.textContent = opts.icon;
    ic.className = 'text-xl leading-none';
    content.appendChild(ic);
  }

  const text = document.createElement('span');
  text.textContent = opts.label.toUpperCase();
  content.appendChild(text);

  if (opts.locked) {
    const lock = document.createElement('span');
    lock.textContent = '🔒';
    lock.className = 'ml-1 opacity-70';
    content.appendChild(lock);
  }

  btn.appendChild(content);

  if (opts.onClick && !opts.disabled && !opts.locked) {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      opts.onClick?.();
    });
  }

  return btn;
}
