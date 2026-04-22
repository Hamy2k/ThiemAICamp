import Phaser from 'phaser';
import { COLORS } from '@/data/tuning';
import { createLogo } from '@/ui/components/Logo';
import { createButton } from '@/ui/components/Button';
import { createCurrencyBar } from '@/ui/components/CurrencyBar';
import { ComingSoonModal } from '@/ui/ComingSoonModal';
import { CURRENCY } from '@/data/tuning';

const MENU_DOM_ID = 'menu-overlay';

export class MenuScene extends Phaser.Scene {
  private domRoot: HTMLElement | null = null;
  private comingSoon = new ComingSoonModal();

  constructor() {
    super({ key: 'MenuScene' });
  }

  create(): void {
    this.cameras.main.setBackgroundColor(COLORS.BG);
    this.drawBackdrop();
    this.mountDom();

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.teardownDom());
    this.events.once(Phaser.Scenes.Events.DESTROY, () => this.teardownDom());
  }

  private drawBackdrop(): void {
    const w = this.scale.width;
    const h = this.scale.height;
    // If a menu_bg texture loaded, render it stretched; else gradient via two rects.
    if (this.textures.exists('menu_bg')) {
      const img = this.add.image(w / 2, h / 2, 'menu_bg');
      const scale = Math.max(w / img.width, h / img.height);
      img.setScale(scale).setAlpha(0.55);
      this.add
        .rectangle(w / 2, h / 2, w, h, COLORS.BG, 0.55)
        .setDepth(1);
      return;
    }

    // Fallback: radial-ish gradient simulated with two alpha rects
    this.add.rectangle(w / 2, h / 2, w, h, COLORS.OBSIDIAN_DEEP);
    this.add
      .rectangle(w / 2, h * 0.35, w, h * 0.8, COLORS.OBSIDIAN, 0.8)
      .setStrokeStyle(0);
    // Gold underline accent near title
    const lineY = h * 0.22;
    this.add.rectangle(w / 2, lineY + 34, Math.min(w * 0.55, 320), 1, COLORS.GOLD, 0.55);
    // Subtle crimson wash at bottom
    this.add.rectangle(w / 2, h, w, h * 0.3, COLORS.CRIMSON_DEEP, 0.15);
  }

  private mountDom(): void {
    const overlay = document.getElementById('overlay');
    if (!overlay) return;

    const existing = document.getElementById(MENU_DOM_ID);
    if (existing) existing.remove();

    const root = document.createElement('div');
    root.id = MENU_DOM_ID;
    root.className =
      'pointer-events-auto absolute inset-0 flex flex-col items-center ' +
      'justify-between px-5 py-8 animate-fade-in';

    // ─── Header (logo) ───
    const header = document.createElement('div');
    header.className = 'w-full flex justify-center pt-2 sm:pt-4';
    header.appendChild(createLogo({ size: 'lg' }));
    root.appendChild(header);

    // ─── Main menu ───
    const main = document.createElement('div');
    main.className =
      'flex-1 flex items-center justify-center w-full max-w-sm mx-auto';

    const stack = document.createElement('div');
    stack.className = 'w-full flex flex-col gap-3';

    stack.appendChild(
      createButton({
        label: 'Campaign',
        icon: '⚔',
        fullWidth: true,
        size: 'lg',
        onClick: () =>
          this.comingSoon.show({
            title: 'Campaign',
            body: 'The Legion arena opens soon. Conquer the Emperor’s trials in a future update.',
          }),
      })
    );

    stack.appendChild(
      createButton({
        label: 'Arena',
        icon: '♞',
        fullWidth: true,
        size: 'lg',
        onClick: () => this.enterArena(),
      })
    );

    stack.appendChild(
      createButton({
        label: 'Daily',
        icon: '☀',
        fullWidth: true,
        size: 'lg',
        onClick: () =>
          this.comingSoon.show({
            title: 'Daily',
            body: 'Daily challenges return each sunrise. Coming soon.',
          }),
      })
    );

    stack.appendChild(
      createButton({
        label: 'Inventory',
        icon: '🛡',
        fullWidth: true,
        size: 'lg',
        locked: true,
      })
    );

    main.appendChild(stack);
    root.appendChild(main);

    // ─── Footer (currency) ───
    const footer = document.createElement('div');
    footer.className = 'w-full flex justify-center pb-2';
    footer.appendChild(
      createCurrencyBar({ gold: CURRENCY.STARTING_GOLD, gems: CURRENCY.STARTING_GEMS })
    );
    root.appendChild(footer);

    overlay.appendChild(root);
    this.domRoot = root;
  }

  private enterArena(): void {
    this.teardownDom();
    this.scene.start('GameScene');
  }

  private teardownDom(): void {
    this.domRoot?.remove();
    this.domRoot = null;
    this.comingSoon.hide();
  }
}
