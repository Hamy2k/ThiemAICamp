import 'dart:math';
import '../models/board.dart';
import '../models/move.dart';
import '../models/piece.dart';
import '../models/position.dart';
import 'chess_rules.dart';

enum AiLevel { easy, medium, hard, master }

class AiEngine {
  final AiLevel level;
  final String? style;
  final Random _rng;

  AiEngine({this.level = AiLevel.medium, this.style, int? seed})
      : _rng = Random(seed);

  static const _pawnPst = [
    [0, 5, 5, 0, 5, 10, 50, 0],
    [0, 10, -5, 0, 5, 10, 50, 0],
    [0, 10, -10, 0, 10, 20, 50, 0],
    [0, -20, 0, 20, 25, 30, 50, 0],
    [0, -20, 0, 20, 25, 30, 50, 0],
    [0, 10, -10, 0, 10, 20, 50, 0],
    [0, 10, -5, 0, 5, 10, 50, 0],
    [0, 5, 5, 0, 5, 10, 50, 0],
  ];

  static const _knightPst = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  5,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
  ];

  Move? chooseMove(Board b) {
    final moves = ChessRules.legalMoves(b);
    if (moves.isEmpty) return null;

    if (level == AiLevel.easy) {
      moves.sort((a, z) => _moveOrder(z).compareTo(_moveOrder(a)));
      final top = moves.take(min(4, moves.length)).toList();
      return top[_rng.nextInt(top.length)];
    }

    final depth = switch (level) {
      AiLevel.easy => 1,
      AiLevel.medium => 2,
      AiLevel.hard => 3,
      AiLevel.master => 4,
    };

    moves.sort((a, z) => _moveOrder(z).compareTo(_moveOrder(a)));

    Move? best;
    int bestScore = -1 << 30;
    final maximizing = b.turn == PieceColor.white;
    for (final m in moves) {
      final next = ChessRules.applyMove(b, m);
      final score = -_negamax(next, depth - 1, -(1 << 30), 1 << 30, maximizing ? -1 : 1);
      if (score > bestScore) {
        bestScore = score;
        best = m;
      }
    }
    return best;
  }

  int _moveOrder(Move m) {
    int s = 0;
    if (m.captured != null) s += 10 * m.captured!.value - m.piece.value;
    if (m.promotion == PieceType.queen) s += 900;
    if (m.isCastle) s += 50;
    return s;
  }

  int _negamax(Board b, int depth, int alpha, int beta, int perspective) {
    final r = ChessRules.result(b);
    if (r == GameResult.checkmate) return -99999 - depth;
    if (r == GameResult.stalemate || r == GameResult.drawFiftyMove) return 0;
    if (depth == 0) return _evaluate(b) * perspective;

    final moves = ChessRules.legalMoves(b);
    moves.sort((a, z) => _moveOrder(z).compareTo(_moveOrder(a)));

    int best = -(1 << 30);
    for (final m in moves) {
      final next = ChessRules.applyMove(b, m);
      final score = -_negamax(next, depth - 1, -beta, -alpha, -perspective);
      if (score > best) best = score;
      if (best > alpha) alpha = best;
      if (alpha >= beta) break;
    }
    return best;
  }

  int _evaluate(Board b) {
    int whiteMat = 0, blackMat = 0;
    int whitePst = 0, blackPst = 0;
    int whiteMob = 0, blackMob = 0;
    int whiteKingSafety = 0, blackKingSafety = 0;

    for (int f = 0; f < 8; f++) {
      for (int r = 0; r < 8; r++) {
        final p = b.squares[f][r];
        if (p == null) continue;
        final val = p.value;
        final pstVal = _pst(p, f, r);
        if (p.color == PieceColor.white) {
          whiteMat += val;
          whitePst += pstVal;
        } else {
          blackMat += val;
          blackPst += pstVal;
        }
      }
    }

    whiteMob = ChessRules.legalMoves(b, forColor: PieceColor.white).length;
    blackMob = ChessRules.legalMoves(b, forColor: PieceColor.black).length;

    if (ChessRules.isInCheck(b, PieceColor.white)) whiteKingSafety -= 30;
    if (ChessRules.isInCheck(b, PieceColor.black)) blackKingSafety -= 30;

    int score = (whiteMat - blackMat) + (whitePst - blackPst) +
        (whiteMob - blackMob) * 2 + (whiteKingSafety - blackKingSafety);

    score = _applyStyle(score, b, whiteMat, blackMat, whiteMob, blackMob);

    return score;
  }

  int _applyStyle(int base, Board b, int wMat, int bMat, int wMob, int bMob) {
    switch (style) {
      case 'aggressive':
        final attackers = _countAttacks(b, PieceColor.black) -
            _countAttacks(b, PieceColor.white);
        return base + attackers * 6;
      case 'defensive':
        return base + (bMat - wMat) ~/ 2 - (wMob - bMob);
      case 'tactical':
        final tactics = _countPins(b);
        return base + tactics * 10;
      default:
        return base;
    }
  }

  int _countAttacks(Board b, PieceColor side) {
    int n = 0;
    final opp = side == PieceColor.white ? PieceColor.black : PieceColor.white;
    final oppKing = b.findKing(opp);
    if (oppKing == null) return 0;
    final moves = ChessRules.legalMoves(b, forColor: side);
    for (final m in moves) {
      final dx = (m.to.file - oppKing.file).abs();
      final dy = (m.to.rank - oppKing.rank).abs();
      if (dx <= 2 && dy <= 2) n++;
    }
    return n;
  }

  int _countPins(Board b) {
    int n = 0;
    for (int f = 0; f < 8; f++) {
      for (int r = 0; r < 8; r++) {
        final p = b.squares[f][r];
        if (p != null && (p.type == PieceType.bishop ||
            p.type == PieceType.rook || p.type == PieceType.queen)) n++;
      }
    }
    return n;
  }

  int _pst(Piece p, int f, int r) {
    final fr = p.color == PieceColor.white ? r : 7 - r;
    switch (p.type) {
      case PieceType.pawn: return _pawnPst[f][fr];
      case PieceType.knight: return _knightPst[f][fr];
      case PieceType.bishop: return (fr >= 2 && fr <= 5) ? 10 : 0;
      case PieceType.rook: return fr == 6 ? 20 : 0;
      case PieceType.queen: return 0;
      case PieceType.king:
        if (fr == 0) return 30;
        return -20;
    }
  }
}
