import type { Square } from 'chess.js';

/**
 * Convert between chess.js `Square` notation (e.g. "e4") and
 * file/rank indices (0..7 each).
 *
 * Board coordinate system used in rendering:
 *   file 0 = a-file, rank 0 = rank 1.
 * Visual rendering may flip rank if board is displayed from black's side.
 */

export function squareToFR(sq: Square): { file: number; rank: number } {
  const file = sq.charCodeAt(0) - 'a'.charCodeAt(0);
  const rank = parseInt(sq[1]!, 10) - 1;
  return { file, rank };
}

export function frToSquare(file: number, rank: number): Square {
  const fileCh = String.fromCharCode('a'.charCodeAt(0) + file);
  return `${fileCh}${rank + 1}` as Square;
}
