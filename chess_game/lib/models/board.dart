import 'piece.dart';
import 'position.dart';
import 'move.dart';

class Board {
  final List<List<Piece?>> squares;
  final PieceColor turn;
  final Pos? enPassantTarget;
  final Set<String> castlingRights;
  final int halfMoveClock;
  final int fullMove;
  final List<Move> history;

  Board({
    required this.squares,
    this.turn = PieceColor.white,
    this.enPassantTarget,
    Set<String>? castlingRights,
    this.halfMoveClock = 0,
    this.fullMove = 1,
    List<Move>? history,
  })  : castlingRights = castlingRights ?? {'K', 'Q', 'k', 'q'},
        history = history ?? [];

  factory Board.initial() {
    final b = List<List<Piece?>>.generate(8, (_) => List<Piece?>.filled(8, null));
    const order = [
      PieceType.rook, PieceType.knight, PieceType.bishop, PieceType.queen,
      PieceType.king, PieceType.bishop, PieceType.knight, PieceType.rook,
    ];
    for (int f = 0; f < 8; f++) {
      b[f][0] = Piece(order[f], PieceColor.white);
      b[f][1] = const Piece(PieceType.pawn, PieceColor.white);
      b[f][6] = const Piece(PieceType.pawn, PieceColor.black);
      b[f][7] = Piece(order[f], PieceColor.black);
    }
    return Board(squares: b);
  }

  factory Board.empty() {
    final b = List<List<Piece?>>.generate(8, (_) => List<Piece?>.filled(8, null));
    return Board(squares: b, castlingRights: {});
  }

  Piece? at(Pos p) => p.valid ? squares[p.file][p.rank] : null;

  Board clone() {
    final s = List<List<Piece?>>.generate(
        8, (f) => List<Piece?>.generate(8, (r) => squares[f][r]));
    return Board(
      squares: s,
      turn: turn,
      enPassantTarget: enPassantTarget,
      castlingRights: Set.from(castlingRights),
      halfMoveClock: halfMoveClock,
      fullMove: fullMove,
      history: List.from(history),
    );
  }

  Pos? findKing(PieceColor color) {
    for (int f = 0; f < 8; f++) {
      for (int r = 0; r < 8; r++) {
        final p = squares[f][r];
        if (p != null && p.type == PieceType.king && p.color == color) {
          return Pos(f, r);
        }
      }
    }
    return null;
  }
}
