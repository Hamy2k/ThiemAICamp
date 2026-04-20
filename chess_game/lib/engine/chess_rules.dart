import '../models/board.dart';
import '../models/move.dart';
import '../models/piece.dart';
import '../models/position.dart';

class ChessRules {
  static List<Move> legalMoves(Board b, {PieceColor? forColor}) {
    final color = forColor ?? b.turn;
    final pseudo = _pseudoMoves(b, color);
    final legal = <Move>[];
    for (final m in pseudo) {
      final next = applyMove(b, m);
      if (!isInCheck(next, color)) legal.add(m);
    }
    return legal;
  }

  static List<Move> _pseudoMoves(Board b, PieceColor color) {
    final moves = <Move>[];
    for (int f = 0; f < 8; f++) {
      for (int r = 0; r < 8; r++) {
        final p = b.squares[f][r];
        if (p == null || p.color != color) continue;
        final from = Pos(f, r);
        switch (p.type) {
          case PieceType.pawn: _pawnMoves(b, from, p, moves); break;
          case PieceType.knight: _knightMoves(b, from, p, moves); break;
          case PieceType.bishop: _slide(b, from, p, moves, const [[1,1],[-1,1],[1,-1],[-1,-1]]); break;
          case PieceType.rook: _slide(b, from, p, moves, const [[1,0],[-1,0],[0,1],[0,-1]]); break;
          case PieceType.queen: _slide(b, from, p, moves, const [[1,1],[-1,1],[1,-1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]]); break;
          case PieceType.king: _kingMoves(b, from, p, moves); break;
        }
      }
    }
    return moves;
  }

  static void _pawnMoves(Board b, Pos from, Piece p, List<Move> out) {
    final dir = p.color == PieceColor.white ? 1 : -1;
    final startRank = p.color == PieceColor.white ? 1 : 6;
    final promoteRank = p.color == PieceColor.white ? 7 : 0;

    final fwd = Pos(from.file, from.rank + dir);
    if (fwd.valid && b.at(fwd) == null) {
      if (fwd.rank == promoteRank) {
        for (final pt in [PieceType.queen, PieceType.rook, PieceType.bishop, PieceType.knight]) {
          out.add(Move(from: from, to: fwd, piece: p, promotion: pt));
        }
      } else {
        out.add(Move(from: from, to: fwd, piece: p));
        if (from.rank == startRank) {
          final dbl = Pos(from.file, from.rank + 2 * dir);
          if (b.at(dbl) == null) out.add(Move(from: from, to: dbl, piece: p));
        }
      }
    }
    for (final df in [-1, 1]) {
      final cap = Pos(from.file + df, from.rank + dir);
      if (!cap.valid) continue;
      final target = b.at(cap);
      if (target != null && target.color != p.color) {
        if (cap.rank == promoteRank) {
          for (final pt in [PieceType.queen, PieceType.rook, PieceType.bishop, PieceType.knight]) {
            out.add(Move(from: from, to: cap, piece: p, captured: target, promotion: pt));
          }
        } else {
          out.add(Move(from: from, to: cap, piece: p, captured: target));
        }
      } else if (cap == b.enPassantTarget) {
        final capturedPawnPos = Pos(cap.file, from.rank);
        final capturedPawn = b.at(capturedPawnPos);
        if (capturedPawn != null) {
          out.add(Move(from: from, to: cap, piece: p, captured: capturedPawn, isEnPassant: true));
        }
      }
    }
  }

  static void _knightMoves(Board b, Pos from, Piece p, List<Move> out) {
    const deltas = [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]];
    for (final d in deltas) {
      final to = Pos(from.file + d[0], from.rank + d[1]);
      if (!to.valid) continue;
      final t = b.at(to);
      if (t == null) out.add(Move(from: from, to: to, piece: p));
      else if (t.color != p.color) out.add(Move(from: from, to: to, piece: p, captured: t));
    }
  }

  static void _slide(Board b, Pos from, Piece p, List<Move> out, List<List<int>> dirs) {
    for (final d in dirs) {
      int f = from.file + d[0], r = from.rank + d[1];
      while (f >= 0 && f < 8 && r >= 0 && r < 8) {
        final to = Pos(f, r);
        final t = b.at(to);
        if (t == null) {
          out.add(Move(from: from, to: to, piece: p));
        } else {
          if (t.color != p.color) out.add(Move(from: from, to: to, piece: p, captured: t));
          break;
        }
        f += d[0]; r += d[1];
      }
    }
  }

  static void _kingMoves(Board b, Pos from, Piece p, List<Move> out) {
    for (int df = -1; df <= 1; df++) {
      for (int dr = -1; dr <= 1; dr++) {
        if (df == 0 && dr == 0) continue;
        final to = Pos(from.file + df, from.rank + dr);
        if (!to.valid) continue;
        final t = b.at(to);
        if (t == null) out.add(Move(from: from, to: to, piece: p));
        else if (t.color != p.color) out.add(Move(from: from, to: to, piece: p, captured: t));
      }
    }
    if (p.hasMoved) return;
    final rank = p.color == PieceColor.white ? 0 : 7;
    if (from != Pos(4, rank)) return;
    if (isInCheck(b, p.color)) return;
    final kKey = p.color == PieceColor.white ? 'K' : 'k';
    final qKey = p.color == PieceColor.white ? 'Q' : 'q';
    if (b.castlingRights.contains(kKey)) {
      final f5 = Pos(5, rank), f6 = Pos(6, rank);
      final rook = b.at(Pos(7, rank));
      if (b.at(f5) == null && b.at(f6) == null &&
          rook != null && rook.type == PieceType.rook && !rook.hasMoved &&
          !_squareAttacked(b, f5, p.color) && !_squareAttacked(b, f6, p.color)) {
        out.add(Move(from: from, to: f6, piece: p, isCastle: true));
      }
    }
    if (b.castlingRights.contains(qKey)) {
      final f3 = Pos(3, rank), f2 = Pos(2, rank), f1 = Pos(1, rank);
      final rook = b.at(Pos(0, rank));
      if (b.at(f3) == null && b.at(f2) == null && b.at(f1) == null &&
          rook != null && rook.type == PieceType.rook && !rook.hasMoved &&
          !_squareAttacked(b, f3, p.color) && !_squareAttacked(b, f2, p.color)) {
        out.add(Move(from: from, to: f2, piece: p, isCastle: true));
      }
    }
  }

  static bool isInCheck(Board b, PieceColor color) {
    final k = b.findKing(color);
    if (k == null) return false;
    return _squareAttacked(b, k, color);
  }

  static bool _squareAttacked(Board b, Pos sq, PieceColor defender) {
    final attacker = defender == PieceColor.white ? PieceColor.black : PieceColor.white;
    final dir = attacker == PieceColor.white ? 1 : -1;
    for (final df in [-1, 1]) {
      final p = b.at(Pos(sq.file + df, sq.rank - dir));
      if (p != null && p.type == PieceType.pawn && p.color == attacker) return true;
    }
    const nD = [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]];
    for (final d in nD) {
      final p = b.at(Pos(sq.file + d[0], sq.rank + d[1]));
      if (p != null && p.type == PieceType.knight && p.color == attacker) return true;
    }
    const diag = [[1,1],[-1,1],[1,-1],[-1,-1]];
    for (final d in diag) {
      int f = sq.file + d[0], r = sq.rank + d[1];
      while (f >= 0 && f < 8 && r >= 0 && r < 8) {
        final p = b.squares[f][r];
        if (p != null) {
          if (p.color == attacker && (p.type == PieceType.bishop || p.type == PieceType.queen)) return true;
          break;
        }
        f += d[0]; r += d[1];
      }
    }
    const ortho = [[1,0],[-1,0],[0,1],[0,-1]];
    for (final d in ortho) {
      int f = sq.file + d[0], r = sq.rank + d[1];
      while (f >= 0 && f < 8 && r >= 0 && r < 8) {
        final p = b.squares[f][r];
        if (p != null) {
          if (p.color == attacker && (p.type == PieceType.rook || p.type == PieceType.queen)) return true;
          break;
        }
        f += d[0]; r += d[1];
      }
    }
    for (int df = -1; df <= 1; df++) {
      for (int dr = -1; dr <= 1; dr++) {
        if (df == 0 && dr == 0) continue;
        final p = b.at(Pos(sq.file + df, sq.rank + dr));
        if (p != null && p.type == PieceType.king && p.color == attacker) return true;
      }
    }
    return false;
  }

  static Board applyMove(Board b, Move m) {
    final next = b.clone();
    final s = next.squares;
    s[m.from.file][m.from.rank] = null;

    Piece placed = m.piece.copyWith(hasMoved: true);
    if (m.promotion != null) {
      placed = Piece(m.promotion!, m.piece.color, hasMoved: true);
    }
    s[m.to.file][m.to.rank] = placed;

    if (m.isEnPassant) {
      s[m.to.file][m.from.rank] = null;
    }

    if (m.isCastle) {
      final rank = m.to.rank;
      if (m.to.file == 6) {
        final rook = s[7][rank]!;
        s[7][rank] = null;
        s[5][rank] = rook.copyWith(hasMoved: true);
      } else if (m.to.file == 2) {
        final rook = s[0][rank]!;
        s[0][rank] = null;
        s[3][rank] = rook.copyWith(hasMoved: true);
      }
    }

    final rights = Set<String>.from(next.castlingRights);
    if (m.piece.type == PieceType.king) {
      if (m.piece.color == PieceColor.white) { rights.remove('K'); rights.remove('Q'); }
      else { rights.remove('k'); rights.remove('q'); }
    }
    if (m.piece.type == PieceType.rook) {
      if (m.piece.color == PieceColor.white) {
        if (m.from == const Pos(0, 0)) rights.remove('Q');
        if (m.from == const Pos(7, 0)) rights.remove('K');
      } else {
        if (m.from == const Pos(0, 7)) rights.remove('q');
        if (m.from == const Pos(7, 7)) rights.remove('k');
      }
    }
    if (m.captured?.type == PieceType.rook) {
      if (m.to == const Pos(0, 0)) rights.remove('Q');
      if (m.to == const Pos(7, 0)) rights.remove('K');
      if (m.to == const Pos(0, 7)) rights.remove('q');
      if (m.to == const Pos(7, 7)) rights.remove('k');
    }

    Pos? ep;
    if (m.piece.type == PieceType.pawn && (m.to.rank - m.from.rank).abs() == 2) {
      ep = Pos(m.from.file, (m.from.rank + m.to.rank) ~/ 2);
    }

    final nextTurn = b.turn == PieceColor.white ? PieceColor.black : PieceColor.white;
    final nextHistory = List<Move>.from(next.history)..add(m);

    return Board(
      squares: s,
      turn: nextTurn,
      enPassantTarget: ep,
      castlingRights: rights,
      halfMoveClock: (m.captured != null || m.piece.type == PieceType.pawn)
          ? 0 : next.halfMoveClock + 1,
      fullMove: b.turn == PieceColor.black ? next.fullMove + 1 : next.fullMove,
      history: nextHistory,
    );
  }

  static GameResult result(Board b) {
    final legal = legalMoves(b);
    if (legal.isEmpty) {
      return isInCheck(b, b.turn) ? GameResult.checkmate : GameResult.stalemate;
    }
    if (b.halfMoveClock >= 100) return GameResult.drawFiftyMove;
    return GameResult.ongoing;
  }
}

enum GameResult { ongoing, checkmate, stalemate, drawFiftyMove }
