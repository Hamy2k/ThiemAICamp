import 'piece.dart';
import 'position.dart';

class Move {
  final Pos from;
  final Pos to;
  final Piece piece;
  final Piece? captured;
  final PieceType? promotion;
  final bool isCastle;
  final bool isEnPassant;

  const Move({
    required this.from,
    required this.to,
    required this.piece,
    this.captured,
    this.promotion,
    this.isCastle = false,
    this.isEnPassant = false,
  });

  @override
  String toString() => '$from→$to';
}
