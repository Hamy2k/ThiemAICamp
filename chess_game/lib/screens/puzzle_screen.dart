import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../engine/chess_rules.dart';
import '../models/board.dart';
import '../models/move.dart';
import '../models/piece.dart';
import '../models/position.dart';
import '../models/puzzle.dart';
import '../providers/player_provider.dart';
import '../services/audio_service.dart';
import '../services/fen_service.dart';
import '../services/puzzle_repository.dart';
import '../theme/app_theme.dart';
import '../widgets/chess_board_widget.dart';
import '../widgets/coin_badge.dart';

class PuzzleScreen extends StatefulWidget {
  final Puzzle? directPuzzle;
  final VoidCallback? onSolved;
  const PuzzleScreen({super.key, this.directPuzzle, this.onSolved});

  @override
  State<PuzzleScreen> createState() => _PuzzleScreenState();
}

class _PuzzleScreenState extends State<PuzzleScreen> {
  late List<Puzzle> available;
  int idx = 0;
  late Board board;
  late Puzzle current;
  int stepIdx = 0;
  Pos? selected;
  List<Move> legal = [];
  String status = 'Tìm nước hay nhất...';

  @override
  void initState() {
    super.initState();
    if (widget.directPuzzle != null) {
      available = [widget.directPuzzle!];
    } else {
      final lvl = context.read<PlayerProvider>().level;
      available = PuzzleRepository.unlocked(lvl);
    }
    _load(0);
  }

  void _load(int i) {
    idx = i;
    current = available[i];
    board = FenService.fromFen(current.fen);
    stepIdx = 0;
    selected = null; legal = [];
    status = 'Tìm nước hay nhất cho ${board.turn == PieceColor.white ? "Trắng" : "Đen"}';
  }

  Future<void> _onTap(Pos p) async {
    final piece = board.at(p);
    if (selected == null) {
      if (piece != null && piece.color == board.turn) {
        setState(() {
          selected = p;
          legal = ChessRules.legalMoves(board).where((m) => m.from == p).toList();
        });
      }
      return;
    }

    final target = legal.where((m) => m.to == p).toList();
    if (target.isEmpty) {
      setState(() { selected = null; legal = []; });
      return;
    }
    final m = target.first;
    final uci = FenService.uciOfMove(m.from, m.to,
        m.promotion != null ? _promoChar(m.promotion!) : null);

    final expected = current.solutionUci[stepIdx];
    if (uci == expected || uci.substring(0, 4) == expected.substring(0, 4)) {
      AudioService.playMove();
      setState(() {
        board = ChessRules.applyMove(board, m);
        selected = null; legal = [];
        stepIdx++;
      });
      if (stepIdx >= current.solutionUci.length) {
        await _solved();
        return;
      }
      final next = current.solutionUci[stepIdx];
      final replyFrom = FenService.parseSquare(next.substring(0, 2));
      final replyTo = FenService.parseSquare(next.substring(2, 4));
      final replies = ChessRules.legalMoves(board).where((m) =>
          m.from == replyFrom && m.to == replyTo).toList();
      if (replies.isNotEmpty) {
        await Future.delayed(const Duration(milliseconds: 500));
        if (!mounted) return;
        setState(() {
          board = ChessRules.applyMove(board, replies.first);
          stepIdx++;
          status = 'Tiếp tục...';
        });
      }
    } else {
      AudioService.playLose();
      setState(() {
        status = 'Sai rồi. Thử lại.';
        selected = null; legal = [];
      });
    }
  }

  String _promoChar(PieceType t) => switch (t) {
    PieceType.queen => 'q', PieceType.rook => 'r',
    PieceType.bishop => 'b', PieceType.knight => 'n', _ => 'q',
  };

  Future<void> _solved() async {
    setState(() => status = '✓ Xuất sắc!');
    final player = context.read<PlayerProvider>();
    await player.addCoins(current.reward);
    await player.addXp(25);
    await player.incPuzzle();
    AudioService.playWin();
    widget.onSolved?.call();
    if (!mounted) return;
    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Giải xong!', style: TextStyle(color: AppColors.neonGreen)),
        content: Text('+${current.reward} coin\n+25 XP'),
        actions: [
          if (idx < available.length - 1)
            TextButton(
              onPressed: () { Navigator.pop(context); setState(() => _load(idx + 1)); },
              child: const Text('Puzzle tiếp'),
            ),
          TextButton(
            onPressed: () { Navigator.pop(context); Navigator.pop(context); },
            child: const Text('Thoát'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${current.title} · ${idx + 1}/${available.length}'),
        actions: const [Padding(
            padding: EdgeInsets.only(right: 8),
            child: Center(child: CoinBadge(compact: true)))],
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.neonPurple.withValues(alpha: 0.5)),
              ),
              child: Text(status,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.neonPurple, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: 12),
            AspectRatio(
              aspectRatio: 1,
              child: ChessBoardWidget(
                board: board, legalMoves: selected == null ? [] : legal,
                selected: selected,
                flipped: board.turn == PieceColor.black,
                onTapSquare: _onTap,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => setState(() => _load(idx)),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Thử lại'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: idx < available.length - 1
                        ? () => setState(() => _load(idx + 1)) : null,
                    icon: const Icon(Icons.skip_next),
                    label: const Text('Bỏ qua'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
