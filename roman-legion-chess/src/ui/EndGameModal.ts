import type { GameStatus, Color } from '@/core/ChessEngine';
import { createButton } from '@/ui/components/Button';
import { createBanner } from '@/ui/components/Banner';

export interface EndGameModalOptions {
  status: GameStatus;
  humanColor: Color;
  winner: Color | null;
  onRestart: () => void;
  onMenu?: () => void;
}

/**
 * End-of-game DOM modal. Rebuilt each show() call.
 */
export class EndGameModal {
  private root: HTMLElement;

  constructor() {
    const existing = document.getElementById('endgame-modal');
    if (existing) existing.remove();
    this.root = document.createElement('div');
    this.root.id = 'endgame-modal';
  }

  show(opts: EndGameModalOptions): void {
    const overlay = document.getElementById('overlay');
    if (!overlay) return;

    const { status, humanColor, winner } = opts;

    let bannerText = 'Draw';
    let titleAccent = 'text-gold';
    if (status === 'checkmate') {
      if (winner === humanColor) {
        bannerText = 'Victory';
        titleAccent = 'text-emerald-400';
      } else {
        bannerText = 'Defeat';
        titleAccent = 'text-crimson';
      }
    } else if (status === 'stalemate') {
      bannerText = 'Stalemate';
    }

    const subtitle =
      status === 'checkmate'
        ? 'The arena falls silent. Checkmate.'
        : status === 'stalemate'
          ? 'No legal moves remain.'
          : 'The battle ends in balance.';

    this.root.className =
      'pointer-events-auto absolute inset-0 flex items-center justify-center ' +
      'bg-black/80 backdrop-blur-sm animate-fade-in';
    this.root.innerHTML = '';

    const panel = document.createElement('div');
    panel.className =
      'roman-panel mx-6 max-w-sm w-full p-8 text-center shadow-gold-strong';

    const banner = createBanner({ text: bannerText, size: 'lg' });
    banner.classList.add('mx-auto', '-mt-12', 'mb-5');
    panel.appendChild(banner);

    const resultTitle = document.createElement('h2');
    resultTitle.className = `font-display font-bold uppercase tracking-banner text-2xl ${titleAccent}`;
    resultTitle.textContent =
      bannerText === 'Victory' ? 'Ave Imperator' : bannerText === 'Defeat' ? 'Vae Victis' : bannerText;
    panel.appendChild(resultTitle);

    const sub = document.createElement('p');
    sub.className = 'mt-2 text-marble/70 text-sm';
    sub.textContent = subtitle;
    panel.appendChild(sub);

    const btnRow = document.createElement('div');
    btnRow.className = 'mt-8 flex flex-col gap-2';

    btnRow.appendChild(
      createButton({
        label: 'New Game',
        fullWidth: true,
        onClick: () => {
          this.hide();
          opts.onRestart();
        },
      })
    );

    if (opts.onMenu) {
      btnRow.appendChild(
        createButton({
          label: 'Menu',
          variant: 'ghost',
          fullWidth: true,
          onClick: () => {
            this.hide();
            opts.onMenu?.();
          },
        })
      );
    }

    panel.appendChild(btnRow);
    this.root.appendChild(panel);
    overlay.appendChild(this.root);
  }

  hide(): void {
    this.root.remove();
  }
}
