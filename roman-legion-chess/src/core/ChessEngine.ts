import { Chess, type Square, type Move } from 'chess.js';

export type GameStatus = 'ongoing' | 'checkmate' | 'stalemate' | 'draw';
export type Color = 'w' | 'b';
export type PieceType = 'p' | 'n' | 'b' | 'r' | 'q' | 'k';

export interface BoardPiece {
  type: PieceType;
  color: Color;
  square: Square;
}

export interface LegalMove {
  from: Square;
  to: Square;
  promotion?: PieceType;
  captured?: PieceType;
  flags: string;
}

/**
 * Thin wrapper around chess.js providing a typed, stable API for our game.
 * chess.js is the source of truth for rule validation.
 */
export class ChessEngine {
  private chess: Chess;

  constructor(fen?: string) {
    this.chess = new Chess(fen);
  }

  newGame(): void {
    this.chess.reset();
  }

  getBoard(): (BoardPiece | null)[][] {
    const raw = this.chess.board();
    return raw.map((row) =>
      row.map((cell) =>
        cell === null
          ? null
          : { type: cell.type as PieceType, color: cell.color as Color, square: cell.square as Square }
      )
    );
  }

  getLegalMoves(square: Square): LegalMove[] {
    const moves = this.chess.moves({ square, verbose: true }) as Move[];
    return moves.map((m) => ({
      from: m.from as Square,
      to: m.to as Square,
      promotion: m.promotion as PieceType | undefined,
      captured: m.captured as PieceType | undefined,
      flags: m.flags,
    }));
  }

  getAllLegalMoves(): LegalMove[] {
    const moves = this.chess.moves({ verbose: true }) as Move[];
    return moves.map((m) => ({
      from: m.from as Square,
      to: m.to as Square,
      promotion: m.promotion as PieceType | undefined,
      captured: m.captured as PieceType | undefined,
      flags: m.flags,
    }));
  }

  makeMove(from: Square, to: Square, promotion: PieceType = 'q'): LegalMove | null {
    try {
      const result = this.chess.move({ from, to, promotion });
      if (!result) return null;
      return {
        from: result.from as Square,
        to: result.to as Square,
        promotion: result.promotion as PieceType | undefined,
        captured: result.captured as PieceType | undefined,
        flags: result.flags,
      };
    } catch {
      return null;
    }
  }

  getTurn(): Color {
    return this.chess.turn() as Color;
  }

  getStatus(): GameStatus {
    if (this.chess.isCheckmate()) return 'checkmate';
    if (this.chess.isStalemate()) return 'stalemate';
    if (this.chess.isDraw()) return 'draw';
    return 'ongoing';
  }

  isInCheck(): boolean {
    return this.chess.inCheck();
  }

  getFen(): string {
    return this.chess.fen();
  }

  loadFen(fen: string): boolean {
    try {
      this.chess.load(fen);
      return true;
    } catch {
      return false;
    }
  }

  history(): Move[] {
    return this.chess.history({ verbose: true }) as Move[];
  }
}
