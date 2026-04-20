import '../models/board.dart';
import '../models/piece.dart';
import '../models/position.dart';

class FenService {
  static Board fromFen(String fen) {
    final parts = fen.split(' ');
    final squares = List<List<Piece?>>.generate(8, (_) => List<Piece?>.filled(8, null));
    final ranks = parts[0].split('/');
    for (int r = 0; r < 8; r++) {
      int f = 0;
      for (final ch in ranks[7 - r].split('')) {
        final n = int.tryParse(ch);
        if (n != null) { f += n; continue; }
        squares[f][r] = _parsePiece(ch);
        f++;
      }
    }
    final turn = (parts.length > 1 && parts[1] == 'b') ? PieceColor.black : PieceColor.white;
    final rights = <String>{};
    if (parts.length > 2 && parts[2] != '-') {
      for (final c in parts[2].split('')) rights.add(c);
    }
    return Board(squares: squares, turn: turn, castlingRights: rights);
  }

  static Piece _parsePiece(String ch) {
    final color = ch.toUpperCase() == ch ? PieceColor.white : PieceColor.black;
    final lc = ch.toLowerCase();
    final type = switch (lc) {
      'k' => PieceType.king, 'q' => PieceType.queen, 'r' => PieceType.rook,
      'b' => PieceType.bishop, 'n' => PieceType.knight, 'p' => PieceType.pawn,
      _ => PieceType.pawn,
    };
    return Piece(type, color, hasMoved: true);
  }

  static Pos parseSquare(String s) {
    final file = s.codeUnitAt(0) - 'a'.codeUnitAt(0);
    final rank = int.parse(s[1]) - 1;
    return Pos(file, rank);
  }

  static String uciOfMove(Pos from, Pos to, [String? promo]) {
    return '${from.toString()}${to.toString()}${promo ?? ''}';
  }
}
