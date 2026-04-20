enum PieceType { pawn, knight, bishop, rook, queen, king }
enum PieceColor { white, black }

class Piece {
  final PieceType type;
  final PieceColor color;
  final bool hasMoved;

  const Piece(this.type, this.color, {this.hasMoved = false});

  Piece copyWith({bool? hasMoved}) =>
      Piece(type, color, hasMoved: hasMoved ?? this.hasMoved);

  String get symbol {
    const map = {
      PieceType.king: ['♔', '♚'],
      PieceType.queen: ['♕', '♛'],
      PieceType.rook: ['♖', '♜'],
      PieceType.bishop: ['♗', '♝'],
      PieceType.knight: ['♘', '♞'],
      PieceType.pawn: ['♙', '♟'],
    };
    return map[type]![color == PieceColor.white ? 0 : 1];
  }

  int get value {
    switch (type) {
      case PieceType.pawn: return 100;
      case PieceType.knight: return 320;
      case PieceType.bishop: return 330;
      case PieceType.rook: return 500;
      case PieceType.queen: return 900;
      case PieceType.king: return 20000;
    }
  }

  String get char {
    const m = {
      PieceType.king: 'k', PieceType.queen: 'q', PieceType.rook: 'r',
      PieceType.bishop: 'b', PieceType.knight: 'n', PieceType.pawn: 'p',
    };
    final c = m[type]!;
    return color == PieceColor.white ? c.toUpperCase() : c;
  }
}
