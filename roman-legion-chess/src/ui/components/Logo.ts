/**
 * Roman Legion Chess logo — title + subtitle.
 * Reusable in MenuScene, splash, about dialog.
 */

export interface LogoOptions {
  title?: string;
  subtitle?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function createLogo(opts: LogoOptions = {}): HTMLElement {
  const wrap = document.createElement('div');
  wrap.className = 'flex flex-col items-center text-center select-none';

  const size = opts.size ?? 'lg';
  const titleClass =
    size === 'lg'
      ? 'text-4xl sm:text-5xl'
      : size === 'md'
        ? 'text-3xl'
        : 'text-2xl';

  const title = document.createElement('h1');
  title.className = `roman-title ${titleClass} leading-tight`;
  title.textContent = (opts.title ?? 'Roman Legion Chess').toUpperCase();
  wrap.appendChild(title);

  const subtitle = document.createElement('div');
  subtitle.className =
    'mt-2 font-numeric text-gold-dark tracking-[0.35em] text-xs sm:text-sm';
  subtitle.textContent = (opts.subtitle ?? 'Empire Arena').toUpperCase();
  wrap.appendChild(subtitle);

  return wrap;
}
