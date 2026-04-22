import Phaser from 'phaser';
import { PIECE_ASSETS, PIECE_TYPE_TO_KEY, UI_ASSETS } from '@/data/assetConfig';
import { PIECE_BLACK_FILTER } from '@/data/tuning';

/**
 * BootScene — attempts to load optional external assets.
 * Missing files emit a warn and are handled by fallback rendering.
 * After load, synthesises black-piece variants via canvas filter.
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
    // Pieces (optional — fallback to letters)
    for (const [typeKey, path] of Object.entries(PIECE_ASSETS)) {
      this.load.image(pieceTextureKey('w', typeKey), path);
    }
    // Menu background (optional)
    this.load.image('menu_bg', UI_ASSETS.menu_bg);

    this.load.on('loaderror', (file: Phaser.Loader.File) => {
      console.warn(`[assets] missing: ${file.src}`);
    });
  }

  create(): void {
    this.generateBlackVariants();
    this.scene.start('MenuScene');
  }

  private generateBlackVariants(): void {
    for (const typeKey of Object.values(PIECE_TYPE_TO_KEY)) {
      const whiteKey = pieceTextureKey('w', typeKey);
      const blackKey = pieceTextureKey('b', typeKey);
      if (!this.textures.exists(whiteKey)) continue;
      if (this.textures.exists(blackKey)) continue;
      try {
        const src = this.textures.get(whiteKey).getSourceImage() as
          | HTMLImageElement
          | HTMLCanvasElement;
        const w = 'width' in src ? src.width : 128;
        const h = 'height' in src ? src.height : 128;
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) continue;
        ctx.filter = PIECE_BLACK_FILTER;
        ctx.drawImage(src as CanvasImageSource, 0, 0);
        this.textures.addCanvas(blackKey, canvas);
      } catch (err) {
        console.warn(`[assets] failed to create black variant for ${typeKey}`, err);
      }
    }
  }
}

export function pieceTextureKey(color: 'w' | 'b', typeKey: string): string {
  return `piece_${color}_${typeKey}`;
}
