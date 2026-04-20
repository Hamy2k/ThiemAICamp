import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../models/puzzle.dart';
import '../services/daily_rewards_service.dart';
import '../services/puzzle_repository.dart';
import '../theme/app_theme.dart';
import '../widgets/coin_badge.dart';
import '../widgets/neon_button.dart';
import 'puzzle_screen.dart';

class DailyChallengeScreen extends StatefulWidget {
  const DailyChallengeScreen({super.key});

  @override
  State<DailyChallengeScreen> createState() => _DailyChallengeScreenState();
}

class _DailyChallengeScreenState extends State<DailyChallengeScreen> {
  late final List<Puzzle> puzzles;
  List<bool> solved = [false, false, false];

  @override
  void initState() {
    super.initState();
    puzzles = PuzzleRepository.todaysThree();
  }

  Future<void> _open(int i) async {
    if (solved[i]) return;
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PuzzleScreen(
        directPuzzle: puzzles[i],
        onSolved: () => solved[i] = true,
      ),
    ));
    if (!mounted) return;
    setState(() {});
    if (solved.every((s) => s)) await _completeDay();
  }

  Future<void> _completeDay() async {
    if (DailyRewardsService.didDailyChallengeToday()) return;
    await DailyRewardsService.markDailyChallengeDone();
    final player = context.read<PlayerProvider>();
    await player.addCoins(100);
    await player.addXp(50);
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('CHALLENGE HOÀN THÀNH!',
            style: TextStyle(color: AppColors.neonGold)),
        content: const Text('Bonus: +100 coin · +50 XP\nStreak vẫn sống — gặp lại mai!'),
        actions: [
          TextButton(
            onPressed: () { Navigator.pop(context); Navigator.pop(context); },
            child: const Text('Tuyệt'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final streak = context.watch<PlayerProvider>().streak;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Challenge'),
        actions: const [Padding(
            padding: EdgeInsets.only(right: 8),
            child: Center(child: CoinBadge(compact: true)))],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [
                  AppColors.neonGold.withValues(alpha: 0.15),
                  AppColors.neonPink.withValues(alpha: 0.15),
                ]),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.neonGold.withValues(alpha: 0.55)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.local_fire_department, color: AppColors.neonPink, size: 36),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Streak: $streak ngày',
                            style: const TextStyle(
                                color: AppColors.neonPink,
                                fontSize: 18, fontWeight: FontWeight.w900)),
                        const Text('Giải 3 puzzle/ngày để giữ streak',
                            style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            for (int i = 0; i < 3; i++) ...[
              NeonButton(
                label: 'Puzzle ${i + 1}  ${solved[i] ? "✓" : ""}',
                subtitle: puzzles[i].title,
                icon: solved[i] ? Icons.check_circle : Icons.bolt,
                color: solved[i] ? AppColors.neonGreen : AppColors.neonPurple,
                onTap: solved[i] ? null : () => _open(i),
              ),
              const SizedBox(height: 10),
            ],
            const Spacer(),
            if (DailyRewardsService.didDailyChallengeToday())
              const Text('Hôm nay bạn đã hoàn thành — Quay lại mai.',
                  style: TextStyle(color: AppColors.neonGreen)),
          ],
        ),
      ),
    );
  }
}
