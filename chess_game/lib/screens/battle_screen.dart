import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/boss.dart';
import '../providers/player_provider.dart';
import '../services/boss_repository.dart';
import '../services/storage_service.dart';
import '../theme/app_theme.dart';
import '../widgets/coin_badge.dart';
import 'game_screen.dart';

class BattleScreen extends StatefulWidget {
  const BattleScreen({super.key});

  @override
  State<BattleScreen> createState() => _BattleScreenState();
}

class _BattleScreenState extends State<BattleScreen> {
  Set<String> _unlocked = {};
  Set<String> _defeated = {};

  @override
  void initState() {
    super.initState();
    _unlocked = StorageService.getStrList('unlockedBosses').toSet();
    _defeated = StorageService.getStrList(StorageKeys.bossesDefeated).toSet();
    if (_unlocked.isEmpty) _unlocked = {'b01'};
  }

  Future<void> _unlockBoss(Boss boss) async {
    final player = context.read<PlayerProvider>();
    if (player.level < boss.requiredLevel) {
      _snack('Cần level ${boss.requiredLevel} để mở boss này');
      return;
    }
    if (!await player.spendCoins(boss.unlockCost)) {
      _snack('Không đủ coin');
      return;
    }
    setState(() => _unlocked.add(boss.id));
    await StorageService.setStrList('unlockedBosses', _unlocked.toList());
  }

  Future<void> _fight(Boss boss) async {
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => GameScreen(modeName: 'battle', boss: boss),
    ));
    if (!mounted) return;
    _defeated = StorageService.getStrList(StorageKeys.bossesDefeated).toSet();
    setState(() {});
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerProvider>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Boss Battle'),
        actions: const [Padding(
            padding: EdgeInsets.only(right: 8),
            child: Center(child: CoinBadge(compact: true)))],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: BossRepository.bosses.length,
        itemBuilder: (_, i) {
          final boss = BossRepository.bosses[i];
          final unlocked = _unlocked.contains(boss.id);
          final defeated = _defeated.contains(boss.id);
          final canUnlock = player.level >= boss.requiredLevel && player.coins >= boss.unlockCost;
          return _bossCard(boss, unlocked, defeated, canUnlock);
        },
      ),
    );
  }

  Widget _bossCard(Boss boss, bool unlocked, bool defeated, bool canUnlock) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: boss.accent.withValues(alpha: unlocked ? 0.75 : 0.3), width: 1.5),
        boxShadow: unlocked ? [
          BoxShadow(color: boss.accent.withValues(alpha: 0.25), blurRadius: 16),
        ] : null,
      ),
      child: Row(
        children: [
          Container(
            width: 58, height: 58,
            decoration: BoxDecoration(
              color: boss.accent.withValues(alpha: 0.15),
              shape: BoxShape.circle,
              border: Border.all(color: boss.accent, width: 1.5),
            ),
            child: Center(
              child: Text(
                unlocked ? boss.avatar : '🔒',
                style: TextStyle(fontSize: 30, color: boss.accent,
                  shadows: [Shadow(color: boss.accent.withValues(alpha: 0.7), blurRadius: 10)]),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(boss.name, style: TextStyle(
                        color: boss.accent, fontSize: 15, fontWeight: FontWeight.w900)),
                    const SizedBox(width: 6),
                    if (defeated)
                      const Icon(Icons.verified, color: AppColors.neonGreen, size: 16),
                  ],
                ),
                Text(boss.title, style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 11)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    _chip('LV ${boss.requiredLevel}+', AppColors.neonPurple),
                    const SizedBox(width: 4),
                    _chip(boss.style.name, boss.accent),
                    const SizedBox(width: 4),
                    _chip('⭐' * boss.difficulty, AppColors.neonGold),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),
          unlocked
              ? ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: boss.accent, foregroundColor: AppColors.bg,
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                  ),
                  onPressed: () => _fight(boss),
                  child: const Text('FIGHT', style: TextStyle(fontWeight: FontWeight.w900)),
                )
              : ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: canUnlock ? AppColors.neonGold : AppColors.textSecondary,
                    foregroundColor: AppColors.bg,
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                  ),
                  onPressed: canUnlock ? () => _unlockBoss(boss) : null,
                  child: Text('${boss.unlockCost} 🪙',
                      style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12)),
                ),
        ],
      ),
    );
  }

  Widget _chip(String text, Color c) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: c.withValues(alpha: 0.6)),
      ),
      child: Text(text, style: TextStyle(color: c, fontSize: 9, fontWeight: FontWeight.w700)),
    );
  }
}
