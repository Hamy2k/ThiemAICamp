import { describe, it, expect, beforeEach } from 'vitest';
import { ChessEngine } from '@/core/ChessEngine';

describe('ChessEngine', () => {
  let engine: ChessEngine;

  beforeEach(() => {
    engine = new ChessEngine();
  });

  describe('new game state', () => {
    it('starts with white to move', () => {
      expect(engine.getTurn()).toBe('w');
    });

    it('status is ongoing', () => {
      expect(engine.getStatus()).toBe('ongoing');
    });

    it('has 32 pieces on starting board', () => {
      const board = engine.getBoard();
      const count = board.flat().filter((c) => c !== null).length;
      expect(count).toBe(32);
    });

    it('returns standard starting FEN', () => {
      expect(engine.getFen()).toBe(
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
      );
    });
  });

  describe('legal moves', () => {
    it('knight b1 has 2 legal moves at start (a3, c3)', () => {
      const moves = engine.getLegalMoves('b1');
      expect(moves).toHaveLength(2);
      const targets = moves.map((m) => m.to).sort();
      expect(targets).toEqual(['a3', 'c3']);
    });

    it('pawn e2 has 2 legal moves at start (e3, e4)', () => {
      const moves = engine.getLegalMoves('e2');
      expect(moves).toHaveLength(2);
      expect(moves.map((m) => m.to).sort()).toEqual(['e3', 'e4']);
    });

    it('rook a1 is trapped at start (0 legal moves)', () => {
      const moves = engine.getLegalMoves('a1');
      expect(moves).toHaveLength(0);
    });
  });

  describe('castling', () => {
    it('allows kingside castling when path is clear', () => {
      // Set up a position where white can castle kingside
      const fen = 'r3k2r/pppqpppp/2n1bn2/3p4/3P4/2N1BN2/PPPQPPPP/R3K2R w KQkq - 0 1';
      expect(engine.loadFen(fen)).toBe(true);
      const kingMoves = engine.getLegalMoves('e1');
      const castleMove = kingMoves.find((m) => m.to === 'g1');
      expect(castleMove).toBeDefined();
      expect(castleMove?.flags).toContain('k');
    });

    it('executes kingside castling move', () => {
      const fen = 'r3k2r/pppqpppp/2n1bn2/3p4/3P4/2N1BN2/PPPQPPPP/R3K2R w KQkq - 0 1';
      engine.loadFen(fen);
      const result = engine.makeMove('e1', 'g1');
      expect(result).not.toBeNull();
      expect(result?.flags).toContain('k');

      const board = engine.getBoard();
      // King on g1 (row 7 in chess.js board indexing; g-file = col 6)
      const g1 = board[7]?.[6];
      const f1 = board[7]?.[5];
      expect(g1?.type).toBe('k');
      expect(f1?.type).toBe('r');
    });
  });

  describe('en passant', () => {
    it('allows en passant capture immediately after double pawn push', () => {
      // Position: white pawn e5, black just played d7-d5
      const fen = 'rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3';
      engine.loadFen(fen);
      const pawnMoves = engine.getLegalMoves('e5');
      const ep = pawnMoves.find((m) => m.to === 'd6');
      expect(ep).toBeDefined();
      expect(ep?.flags).toContain('e');
    });

    it('executes en passant and removes captured pawn', () => {
      const fen = 'rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3';
      engine.loadFen(fen);
      const result = engine.makeMove('e5', 'd6');
      expect(result).not.toBeNull();
      expect(result?.flags).toContain('e');
      expect(result?.captured).toBe('p');
      // d5 pawn should be gone, d6 should now hold a white pawn
      const board = engine.getBoard();
      // chess.js: d6 = row 2, col 3; d5 = row 3, col 3
      expect(board[2]?.[3]?.type).toBe('p');
      expect(board[2]?.[3]?.color).toBe('w');
      expect(board[3]?.[3]).toBeNull();
    });
  });

  describe('checkmate detection', () => {
    it('detects fool\'s mate', () => {
      // 1.f3 e5 2.g4 Qh4#
      engine.makeMove('f2', 'f3');
      engine.makeMove('e7', 'e5');
      engine.makeMove('g2', 'g4');
      engine.makeMove('d8', 'h4');
      expect(engine.getStatus()).toBe('checkmate');
      expect(engine.getTurn()).toBe('w');
    });

    it('detects scholar\'s mate', () => {
      // 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
      engine.makeMove('e2', 'e4');
      engine.makeMove('e7', 'e5');
      engine.makeMove('f1', 'c4');
      engine.makeMove('b8', 'c6');
      engine.makeMove('d1', 'h5');
      engine.makeMove('g8', 'f6');
      engine.makeMove('h5', 'f7');
      expect(engine.getStatus()).toBe('checkmate');
    });
  });

  describe('makeMove + loadFen', () => {
    it('rejects illegal move', () => {
      const result = engine.makeMove('e2', 'e5'); // pawn can't jump 3
      expect(result).toBeNull();
    });

    it('newGame resets to start position', () => {
      engine.makeMove('e2', 'e4');
      engine.newGame();
      expect(engine.getFen()).toBe(
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
      );
    });

    it('loadFen accepts valid FEN', () => {
      const fen = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1';
      expect(engine.loadFen(fen)).toBe(true);
      expect(engine.getTurn()).toBe('b');
    });

    it('loadFen rejects invalid FEN', () => {
      expect(engine.loadFen('not-a-fen')).toBe(false);
    });
  });
});
