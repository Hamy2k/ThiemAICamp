import 'package:flutter/material.dart';
import '../models/board.dart';
import '../models/move.dart';
import '../models/piece.dart';
import '../models/position.dart';
import '../theme/app_theme.dart';

class ChessBoardWidget extends StatelessWidget {
  final Board board;
  final Pos? selected;
  final List<Move> legalMoves;
  final Pos? lastFrom;
  final Pos? lastTo;
  final Pos? checkSquare;
  final Pos? hintFrom;
  final Pos? hintTo;
  final bool flipped;
  final void Function(Pos) onTapSquare;

  const ChessBoardWidget({
    super.key,
    required this.board,
    required this.legalMoves,
    required this.onTapSquare,
    this.selected,
    this.lastFrom,
    this.lastTo,
    this.checkSquare,
    this.hintFrom,
    this.hintTo,
    this.flipped = false,
  });

  @override
  Widget build(BuildContext context) {
    final legalTargets = legalMoves.map((m) => m.to).toSet();
    return LayoutBuilder(
      builder: (context, c) {
        final side = c.maxWidth;
        final sq = side / 8;
        return Container(
          width: side, height: side,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.neonCyan.withValues(alpha: 0.6), width: 2),
            boxShadow: [
              BoxShadow(color: AppColors.neonCyan.withValues(alpha: 0.35), blurRadius: 24, spreadRadius: 1),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: Stack(
              children: [
                for (int rank = 0; rank < 8; rank++)
                  for (int file = 0; file < 8; file++)
                    _buildSquare(file, rank, sq, legalTargets),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSquare(int file, int rank, double sq, Set<Pos> targets) {
    final displayFile = flipped ? 7 - file : file;
    final displayRank = flipped ? rank : 7 - rank;
    final pos = Pos(displayFile, displayRank);
    final piece = board.at(pos);
    final isDark = (displayFile + displayRank) % 2 == 0;
    final isSelected = selected == pos;
    final isLegalTarget = targets.contains(pos);
    final isLastMove = pos == lastFrom || pos == lastTo;
    final isCheck = pos == checkSquare;
    final isHint = pos == hintFrom || pos == hintTo;

    Color bg = isDark ? AppColors.darkSquare : AppColors.lightSquare;
    if (isLastMove) bg = Color.alphaBlend(AppColors.lastMove, bg);
    if (isSelected) bg = Color.alphaBlend(AppColors.highlight, bg);
    if (isCheck) bg = Color.alphaBlend(AppColors.check.withValues(alpha: 0.5), bg);
    if (isHint) bg = Color.alphaBlend(AppColors.neonGreen.withValues(alpha: 0.45), bg);

    return Positioned(
      left: file * sq,
      top: rank * sq,
      width: sq,
      height: sq,
      child: GestureDetector(
        onTap: () => onTapSquare(pos),
        child: Container(
          color: bg,
          child: Stack(
            alignment: Alignment.center,
            children: [
              if (file == 0)
                Positioned(
                  left: 3, top: 2,
                  child: Text('${displayRank + 1}',
                      style: TextStyle(color: AppColors.textSecondary.withValues(alpha: 0.6), fontSize: 9)),
                ),
              if (rank == 7)
                Positioned(
                  right: 3, bottom: 2,
                  child: Text(String.fromCharCode(97 + displayFile),
                      style: TextStyle(color: AppColors.textSecondary.withValues(alpha: 0.6), fontSize: 9)),
                ),
              if (isLegalTarget && piece == null)
                Container(
                  width: sq * 0.28, height: sq * 0.28,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.neonCyan.withValues(alpha: 0.55),
                  ),
                ),
              if (isLegalTarget && piece != null)
                Container(
                  width: sq * 0.92, height: sq * 0.92,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.neonPink, width: 3),
                  ),
                ),
              if (piece != null) _buildPiece(piece, sq),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPiece(Piece p, double sq) {
    final isWhite = p.color == PieceColor.white;
    return Center(
      child: Text(
        p.symbol,
        style: TextStyle(
          fontSize: sq * 0.78,
          color: isWhite ? Colors.white : const Color(0xFF0C1224),
          fontWeight: FontWeight.w900,
          shadows: [
            Shadow(
              color: isWhite ? AppColors.neonCyan : AppColors.neonPink,
              blurRadius: 12,
            ),
            Shadow(
              color: Colors.black.withValues(alpha: 0.55),
              blurRadius: 2, offset: const Offset(1, 1),
            ),
          ],
        ),
      ),
    );
  }
}
