import { describe, it, expect } from 'vitest';
import { Chess } from 'chess.js';
import { AIEasy } from '@/ai/AIEasy';

/**
 * Deterministic RNG helper for capture-bias verification.
 */
function seededRng(seed = 0.42): () => number {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

describe('AIEasy', () => {
  it('returns a legal move from the start position', async () => {
    const ai = new AIEasy(seededRng(0.5));
    const fen = new Chess().fen();
    const move = await ai.getMove(fen);
    const c = new Chess(fen);
    const legal = c.moves({ verbose: true });
    expect(legal.some((m) => m.from === move.from && m.to === move.to)).toBe(true);
  });

  it('prefers a capture when one is available (position 1: rook free-hanging)', async () => {
    // White rook on d4, black knight on d5 is capturable. White to move.
    const fen = '4k3/8/8/3n4/3R4/8/8/4K3 w - - 0 1';
    // Force a very particular index; regardless of RNG seed, pool is captures-only
    const ai = new AIEasy(seededRng(0.1));
    const move = await ai.getMove(fen);
    expect(move.from).toBe('d4');
    expect(move.to).toBe('d5');
  });

  it('prefers a capture when one is available (position 2: queen can capture pawn)', async () => {
    // Only legal capture: Qxh7 (white queen h1 captures black pawn h7)
    const fen = '4k3/7p/8/8/8/8/8/4K2Q w - - 0 1';
    const ai = new AIEasy(seededRng(0.9));
    const move = await ai.getMove(fen);
    const c = new Chess(fen);
    const played = c.move({ from: move.from, to: move.to, promotion: 'q' });
    expect(played).not.toBeNull();
    // If any capture existed in the original position, AIEasy must play a capture
    const captures = new Chess(fen).moves({ verbose: true }).filter((m) => m.captured);
    expect(captures.length).toBeGreaterThan(0);
    expect(played?.captured).toBeDefined();
  });

  it('prefers a capture when one is available (position 3: knight fork capture)', async () => {
    // White knight on e5 can capture: Nxf7 (pawn) — only capture
    const fen = 'r3kbnr/ppp2ppp/8/4N3/8/8/PPPP1PPP/RNBQKB1R w KQkq - 0 1';
    const ai = new AIEasy(seededRng(0.77));
    const move = await ai.getMove(fen);
    const c = new Chess(fen);
    const played = c.move({ from: move.from, to: move.to, promotion: 'q' });
    expect(played?.captured).toBeDefined();
  });

  it('prefers a capture when one is available (position 4: bishop capture)', async () => {
    // Bishop c4 can capture pawn on f7
    const fen = 'rnbqkbnr/pppppppp/8/8/2B5/8/PPPP1PPP/RNBQK1NR w KQkq - 0 1';
    const ai = new AIEasy(seededRng(0.33));
    const move = await ai.getMove(fen);
    const c = new Chess(fen);
    const played = c.move({ from: move.from, to: move.to, promotion: 'q' });
    expect(played?.captured).toBeDefined();
  });

  it('falls back to any legal move when no capture exists', async () => {
    // Clean opening position — no captures available
    const fen = new Chess().fen();
    const ai = new AIEasy(seededRng(0.25));
    const move = await ai.getMove(fen);
    const c = new Chess(fen);
    const played = c.move({ from: move.from, to: move.to, promotion: 'q' });
    expect(played).not.toBeNull();
    expect(played?.captured).toBeUndefined();
  });

  it('throws on terminal (no legal moves) position', async () => {
    // Stalemate: black king on a8, white king on a6, white queen on b6 — no, that's mate.
    // Use clean stalemate: black king h8, white king f7, white queen g6 → stalemate.
    const fen = '7k/8/5KQ1/8/8/8/8/8 b - - 0 1';
    const ai = new AIEasy();
    await expect(ai.getMove(fen)).rejects.toThrow();
  });
});
