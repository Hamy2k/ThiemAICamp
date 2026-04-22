/**
 * Roman banner — pennant-shaped horizontal band.
 * Use for scene titles, achievement toasts, boss name displays.
 */

export interface BannerOptions {
  text: string;
  size?: 'sm' | 'md' | 'lg';
  extraClass?: string;
}

export function createBanner(opts: BannerOptions): HTMLElement {
  const el = document.createElement('div');
  const sizeClass =
    opts.size === 'lg'
      ? 'text-xl px-10 py-3'
      : opts.size === 'sm'
        ? 'text-xs px-5 py-1.5'
        : 'text-sm px-7 py-2';

  el.className = ['roman-banner', sizeClass, opts.extraClass ?? '']
    .filter(Boolean)
    .join(' ');
  el.textContent = opts.text.toUpperCase();
  return el;
}
