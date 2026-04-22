import '@/styles/main.css';
import { createGame } from '@/game';

const GAME_MOUNT_ID = 'game';

async function boot(): Promise<void> {
  // Wait for display + numeric fonts so Phaser text renders them on first frame.
  // If loading fails or times out, we still boot — Phaser will fallback.
  try {
    await Promise.race([
      Promise.all([
        document.fonts.load('700 16px "Cinzel"'),
        document.fonts.load('700 16px "Orbitron"'),
      ]),
      new Promise((resolve) => setTimeout(resolve, 1500)),
    ]);
  } catch (err) {
    console.warn('[fonts] preload failed, continuing anyway', err);
  }
  createGame(GAME_MOUNT_ID);
}

window.addEventListener('load', () => {
  void boot();
});
