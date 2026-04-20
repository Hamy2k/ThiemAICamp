import 'board.dart';
import 'move.dart';
import 'piece.dart';
import 'position.dart';
import '../engine/chess_rules.dart';

enum GameMode { quickAi, local2p, puzzle, battle, daily }

class GameState {
  final Board board;
  final GameMode mode;
  final PieceColor? aiColor;
  final int aiDepth;
  final String? aiStyle;
  final List<Move> undoneMoves;

  const GameState({
    required this.board,
    required this.mode,
    this.aiColor,
    this.aiDepth = 3,
    this.aiStyle,
    this.undoneMoves = const [],
  });

  GameState copyWith({Board? board, List<Move>? undoneMoves}) =>
      GameState(
        board: board ?? this.board,
        mode: mode,
        aiColor: aiColor,
        aiDepth: aiDepth,
        aiStyle: aiStyle,
        undoneMoves: undoneMoves ?? this.undoneMoves,
      );

  GameResult get result => ChessRules.result(board);
  bool get gameOver => result != GameResult.ongoing;
  bool get isInCheck => ChessRules.isInCheck(board, board.turn);

  Pos? get lastMoveFrom => board.history.isEmpty ? null : board.history.last.from;
  Pos? get lastMoveTo => board.history.isEmpty ? null : board.history.last.to;
}
