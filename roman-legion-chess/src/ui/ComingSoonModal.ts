import { createButton } from '@/ui/components/Button';
import { createBanner } from '@/ui/components/Banner';

/**
 * Generic "coming soon" modal for not-yet-implemented menu items.
 * DOM overlay (Tailwind styled).
 */

export interface ComingSoonOptions {
  title: string;
  body?: string;
  onClose?: () => void;
}

export class ComingSoonModal {
  private root: HTMLElement;

  constructor() {
    const existing = document.getElementById('coming-soon-modal');
    if (existing) existing.remove();
    this.root = document.createElement('div');
    this.root.id = 'coming-soon-modal';
  }

  show(opts: ComingSoonOptions): void {
    const overlay = document.getElementById('overlay');
    if (!overlay) return;

    this.root.className =
      'pointer-events-auto absolute inset-0 flex items-center justify-center ' +
      'bg-black/80 backdrop-blur-sm animate-fade-in';

    const panel = document.createElement('div');
    panel.className =
      'roman-panel mx-6 max-w-sm w-full p-6 text-center shadow-gold-soft';

    const banner = createBanner({ text: opts.title, size: 'sm' });
    banner.classList.add('mx-auto', '-mt-9', 'mb-4');

    const body = document.createElement('p');
    body.className = 'mt-3 text-marble/80 text-sm leading-relaxed';
    body.textContent = opts.body ?? 'This feature is coming in a future update.';

    const close = createButton({
      label: 'Close',
      fullWidth: true,
      onClick: () => {
        this.hide();
        opts.onClose?.();
      },
      extraClass: 'mt-6',
    });

    panel.appendChild(banner);
    panel.appendChild(body);
    panel.appendChild(close);
    this.root.appendChild(panel);
    overlay.appendChild(this.root);
  }

  hide(): void {
    this.root.remove();
  }
}
