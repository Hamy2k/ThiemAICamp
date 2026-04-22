import { Chess, type Move } from 'chess.js';
import type { AIDecision, AIEngine } from './AIEngine';

/**
 * Easy AI — random move with capture bias.
 * If any capture is legal, picks a random capture.
 * Otherwise picks a random legal move.
 */
export class AIEasy implements AIEngine {
  readonly name = 'Easy';

  private readonly rng: () => number;

  constructor(rng: () => number = Math.random) {
    this.rng = rng;
  }

  async getMove(fen: string): Promise<AIDecision> {
    const chess = new Chess(fen);
    const all = chess.moves({ verbose: true }) as Move[];
    if (all.length === 0) {
      throw new Error('AIEasy.getMove called on terminal position');
    }

    const captures = all.filter((m) => m.captured !== undefined);
    const pool = captures.length > 0 ? captures : all;
    const picked = pool[Math.floor(this.rng() * pool.length)]!;

    return {
      from: picked.from,
      to: picked.to,
      promotion: picked.promotion,
    };
  }
}
