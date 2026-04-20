import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../engine/ai_engine.dart';
import '../engine/chess_rules.dart';
import '../models/board.dart';
import '../models/game_state.dart';
import '../models/move.dart';
import '../models/piece.dart';
import '../models/position.dart';
import '../models/boss.dart';
import '../providers/player_provider.dart';
import '../services/ads_service.dart';
import '../services/audio_service.dart';
import '../services/storage_service.dart';
import '../theme/app_theme.dart';
import '../widgets/chess_board_widget.dart';
import '../widgets/coin_badge.dart';

class GameScreen extends StatefulWidget {
  final String modeName;
  final Boss? boss;
  final AiLevel aiLevel;
  const GameScreen({
    super.key,
    required this.modeName,
    this.boss,
    this.aiLevel = AiLevel.medium,
  });

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late GameState state;
  Pos? selected;
  List<Move> legalForSelected = [];
  bool thinking = false;
  Pos? hintFrom, hintTo;
  int undosLeft = 1;
  AiEngine? _ai;
  AiLevel _level = AiLevel.medium;

  @override
  void initState() {
    super.initState();
    _level = widget.aiLevel;
    if (widget.boss != null) {
      _level = switch (widget.boss!.difficulty) {
        1 => AiLevel.easy,
        2 => AiLevel.medium,
        3 => AiLevel.medium,
        4 => AiLevel.hard,
        _ => AiLevel.master,
      };
      _ai = AiEngine(level: _level, style: widget.boss!.style.name);
    } else if (widget.modeName == 'ai') {
      _ai = AiEngine(level: _level);
    }

    state = GameState(
      board: Board.initial(),
      mode: widget.boss != null
          ? GameMode.battle
          : widget.modeName == 'local' ? GameMode.local2p : GameMode.quickAi,
      aiColor: (widget.modeName == 'local') ? null : PieceColor.black,
    );
  }

  Future<void> _onTap(Pos p) async {
    if (thinking || state.gameOver) return;
    if (state.aiColor != null && state.board.turn == state.aiColor) return;

    final piece = state.board.at(p);
    if (selected == null) {
      if (piece != null && piece.color == state.board.turn) {
        setState(() {
          selected = p;
          legalForSelected = ChessRules.legalMoves(state.board).where((m) => m.from == p).toList();
        });
      }
      return;
    }

    final target = legalForSelected.where((m) => m.to == p).toList();
    if (target.isEmpty) {
      if (piece != null && piece.color == state.board.turn) {
        setState(() {
          selected = p;
          legalForSelected = ChessRules.legalMoves(state.board).where((m) => m.from == p).toList();
        });
      } else {
        setState(() { selected = null; legalForSelected = []; });
      }
      return;
    }

    Move move = target.first;
    if (move.promotion != null) {
      final promo = await _showPromotionDialog(move.piece.color);
      if (promo == null) return;
      move = Move(
        from: move.from, to: move.to, piece: move.piece,
        captured: move.captured, promotion: promo,
      );
    }

    await _playMove(move);
    if (state.aiColor != null &&
        state.board.turn == state.aiColor &&
        !state.gameOver) {
      await _aiPlay();
    }
  }

  Future<PieceType?> _showPromotionDialog(PieceColor color) async {
    return showDialog<PieceType>(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Phong cấp'),
        content: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final pt in [PieceType.queen, PieceType.rook, PieceType.bishop, PieceType.knight])
              IconButton(
                iconSize: 40,
                onPressed: () => Navigator.pop(context, pt),
                icon: Text(
                  Piece(pt, color).symbol,
                  style: const TextStyle(fontSize: 36, color: AppColors.neonCyan),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _playMove(Move m) async {
    if (m.captured != null) {
      AudioService.playCapture();
    } else {
      AudioService.playMove();
    }
    setState(() {
      state = state.copyWith(board: ChessRules.applyMove(state.board, m));
      selected = null;
      legalForSelected = [];
      hintFrom = null; hintTo = null;
    });
    if (state.gameOver) {
      await _onGameEnd();
    }
  }

  Future<void> _aiPlay() async {
    setState(() => thinking = true);
    await Future.delayed(const Duration(milliseconds: 250));
    final chosen = _ai?.chooseMove(state.board);
    if (chosen == null) {
      setState(() => thinking = false);
      return;
    }
    setState(() => thinking = false);
    await _playMove(chosen);
  }

  Future<void> _onGameEnd() async {
    final r = state.result;
    final player = context.read<PlayerProvider>();
    int coins = 0;
    int xp = 0;
    String title = '';
    Color color = AppColors.neonCyan;

    final humanColor = state.aiColor == PieceColor.black ? PieceColor.white :
                       state.aiColor == PieceColor.white ? PieceColor.black : null;

    if (r == GameResult.checkmate) {
      if (humanColor == null) {
        title = 'Chiếu hết! ${state.board.turn == PieceColor.white ? "Đen" : "Trắng"} thắng';
      } else if (state.board.turn != humanColor) {
        title = 'BẠN THẮNG!';
        coins = widget.boss?.reward ?? 40;
        xp = 30 + (widget.boss?.difficulty ?? 0) * 15;
        color = AppColors.neonGreen;
        AudioService.playWin();
        if (widget.boss != null) {
          final defeated = StorageService.getStrList(StorageKeys.bossesDefeated).toSet();
          defeated.add(widget.boss!.id);
          await StorageService.setStrList(StorageKeys.bossesDefeated, defeated.toList());
        }
      } else {
        title = 'BẠN THUA';
        coins = 5;
        xp = 8;
        color = AppColors.neonPink;
        AudioService.playLose();
      }
    } else if (r == GameResult.stalemate) {
      title = 'Hòa (stalemate)';
      coins = 10; xp = 10;
    } else if (r == GameResult.drawFiftyMove) {
      title = 'Hòa (50 nước)';
      coins = 10; xp = 10;
    }

    await player.incMatch();
    if (coins > 0) await player.addCoins(coins);
    final leveledUp = await player.addXp(xp);

    await AdsService.maybeShowInterstitial();

    if (!mounted) return;
    await showDialog(
      context: context,
      builder: (_) => _GameEndDialog(
        title: title, coins: coins, xp: xp, leveledUp: leveledUp, color: color,
        onRematch: () {
          Navigator.pop(context);
          setState(() {
            state = GameState(
              board: Board.initial(),
              mode: state.mode,
              aiColor: state.aiColor,
            );
            selected = null; legalForSelected = []; undosLeft = 1;
          });
        },
        onExit: () {
          Navigator.pop(context);
          Navigator.pop(context);
        },
      ),
    );
  }

  Future<void> _requestHint() async {
    if (thinking || state.gameOver) return;
    final player = context.read<PlayerProvider>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Dùng gợi ý?'),
        content: const Text('Gợi ý tốn 10 coin — hoặc xem quảng cáo miễn phí.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Hủy')),
          TextButton(
            onPressed: () async {
              final earned = await AdsService.showRewarded(onReward: (_) {});
              if (context.mounted) Navigator.pop(context, earned);
            },
            child: const Text('Xem ads'),
          ),
          TextButton(
            onPressed: () async {
              if (await player.spendCoins(10)) {
                if (context.mounted) Navigator.pop(context, true);
              }
            },
            child: const Text('Dùng 10 coin'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final best = AiEngine(level: AiLevel.hard).chooseMove(state.board);
    if (best != null) {
      setState(() {
        hintFrom = best.from;
        hintTo = best.to;
      });
      Timer(const Duration(seconds: 3), () {
        if (mounted) setState(() { hintFrom = null; hintTo = null; });
      });
    }
  }

  Future<void> _undo() async {
    if (thinking || state.board.history.isEmpty || undosLeft <= 0) return;
    final h = state.board.history;
    final rewindBy = state.aiColor == null ? 1 : 2;
    if (h.length < rewindBy) return;
    Board b = Board.initial();
    for (final m in h.take(h.length - rewindBy)) {
      b = ChessRules.applyMove(b, m);
    }
    setState(() {
      state = state.copyWith(board: b);
      selected = null; legalForSelected = [];
      undosLeft--;
    });
  }

  @override
  Widget build(BuildContext context) {
    final check = state.isInCheck ? state.board.findKing(state.board.turn) : null;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.boss?.name ?? (widget.modeName == 'local' ? '2 người' : 'Quick Play')),
        actions: const [Padding(
          padding: EdgeInsets.only(right: 8),
          child: Center(child: CoinBadge(compact: true)),
        )],
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            if (widget.boss != null) _bossBanner(),
            _turnBanner(),
            const SizedBox(height: 12),
            AspectRatio(
              aspectRatio: 1,
              child: ChessBoardWidget(
                board: state.board,
                legalMoves: selected == null ? [] : legalForSelected,
                selected: selected,
                lastFrom: state.lastMoveFrom,
                lastTo: state.lastMoveTo,
                checkSquare: check,
                hintFrom: hintFrom, hintTo: hintTo,
                onTapSquare: _onTap,
              ),
            ),
            const SizedBox(height: 12),
            _controls(),
          ],
        ),
      ),
    );
  }

  Widget _bossBanner() {
    final boss = widget.boss!;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: boss.accent.withValues(alpha: 0.7)),
      ),
      child: Row(
        children: [
          Text(boss.avatar, style: TextStyle(fontSize: 34, color: boss.accent,
            shadows: [Shadow(color: boss.accent.withValues(alpha: 0.7), blurRadius: 14)])),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(boss.name, style: TextStyle(
                    color: boss.accent, fontWeight: FontWeight.w900, fontSize: 15)),
                Text('"${boss.quote}"', style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 11, fontStyle: FontStyle.italic)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: boss.accent.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text('+${boss.reward}',
                style: TextStyle(color: boss.accent, fontWeight: FontWeight.w900, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _turnBanner() {
    final turn = state.board.turn;
    final check = state.isInCheck;
    final text = thinking ? 'AI đang suy nghĩ...' :
        check ? '${turn == PieceColor.white ? "Trắng" : "Đen"} — CHIẾU!' :
        '${turn == PieceColor.white ? "Trắng" : "Đen"} đi';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: check ? AppColors.check : AppColors.neonCyan.withValues(alpha: 0.5)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (thinking) const SizedBox(width: 14, height: 14,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.neonCyan)),
          if (thinking) const SizedBox(width: 8),
          Text(text, style: TextStyle(
            color: check ? AppColors.check : AppColors.textPrimary,
            fontWeight: FontWeight.w700,
          )),
        ],
      ),
    );
  }

  Widget _controls() {
    return Row(
      children: [
        Expanded(child: _btn(Icons.lightbulb, 'Hint', AppColors.neonGold, _requestHint)),
        const SizedBox(width: 8),
        Expanded(child: _btn(Icons.undo, 'Undo ($undosLeft)',
            undosLeft > 0 ? AppColors.neonPurple : AppColors.textSecondary,
            undosLeft > 0 ? _undo : null)),
        const SizedBox(width: 8),
        Expanded(child: _btn(Icons.restart_alt, 'Mới', AppColors.neonPink, () {
          setState(() {
            state = GameState(board: Board.initial(), mode: state.mode, aiColor: state.aiColor);
            selected = null; legalForSelected = []; undosLeft = 1;
          });
        })),
      ],
    );
  }

  Widget _btn(IconData icon, String label, Color color, VoidCallback? onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withValues(alpha: 0.55)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}

class _GameEndDialog extends StatelessWidget {
  final String title;
  final int coins;
  final int xp;
  final int leveledUp;
  final Color color;
  final VoidCallback onRematch;
  final VoidCallback onExit;

  const _GameEndDialog({
    required this.title, required this.coins, required this.xp,
    required this.leveledUp, required this.color,
    required this.onRematch, required this.onExit,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: color, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(title, style: TextStyle(
                color: color, fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 1)),
            const SizedBox(height: 18),
            _rewardRow(Icons.monetization_on, '+$coins', AppColors.neonGold),
            const SizedBox(height: 8),
            _rewardRow(Icons.star, '+$xp XP', AppColors.neonPurple),
            if (leveledUp > 0) ...[
              const SizedBox(height: 8),
              _rewardRow(Icons.trending_up, 'LEVEL UP × $leveledUp', AppColors.neonGreen),
            ],
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onExit,
                    child: const Text('Thoát'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: color, foregroundColor: AppColors.bg,
                    ),
                    onPressed: onRematch,
                    child: const Text('Chơi lại', style: TextStyle(fontWeight: FontWeight.w900)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _rewardRow(IconData i, String text, Color c) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(i, color: c), const SizedBox(width: 8),
        Text(text, style: TextStyle(color: c, fontWeight: FontWeight.w800, fontSize: 16)),
      ],
    );
  }
}
