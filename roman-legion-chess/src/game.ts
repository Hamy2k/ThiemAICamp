import Phaser from 'phaser';
import { BootScene } from '@/scenes/BootScene';
import { MenuScene } from '@/scenes/MenuScene';
import { GameScene } from '@/scenes/GameScene';
import { COLORS } from '@/data/tuning';

export function createGame(parent: string): Phaser.Game {
  return new Phaser.Game({
    type: Phaser.AUTO,
    parent,
    backgroundColor: COLORS.BG,
    scale: {
      mode: Phaser.Scale.RESIZE,
      autoCenter: Phaser.Scale.CENTER_BOTH,
      width: window.innerWidth,
      height: window.innerHeight,
    },
    scene: [BootScene, MenuScene, GameScene],
    render: {
      antialias: true,
      pixelArt: false,
    },
  });
}
