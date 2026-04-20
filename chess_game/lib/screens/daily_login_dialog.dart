import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../services/daily_rewards_service.dart';
import '../services/audio_service.dart';
import '../theme/app_theme.dart';

class DailyLoginDialog extends StatelessWidget {
  const DailyLoginDialog({super.key});

  @override
  Widget build(BuildContext context) {
    final streak = DailyRewardsService.currentStreak;
    final todayIdx = streak % DailyRewardsService.rewardCycle.length;

    return Dialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: AppColors.neonGold.withValues(alpha: 0.7), width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.card_giftcard, size: 48, color: AppColors.neonGold),
            const SizedBox(height: 8),
            const Text('ĐĂNG NHẬP HÀNG NGÀY',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppColors.neonGold)),
            const SizedBox(height: 4),
            Text('Streak hiện tại: $streak ngày',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
            const SizedBox(height: 16),
            GridView.count(
              shrinkWrap: true,
              crossAxisCount: 7,
              mainAxisSpacing: 6, crossAxisSpacing: 6,
              children: List.generate(7, (i) {
                final claimed = i < todayIdx;
                final today = i == todayIdx;
                return Container(
                  decoration: BoxDecoration(
                    color: today ? AppColors.neonGold.withValues(alpha: 0.2) :
                           claimed ? AppColors.card : AppColors.bg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: today ? AppColors.neonGold :
                             claimed ? AppColors.neonGreen : AppColors.textSecondary.withValues(alpha: 0.3),
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('D${i + 1}', style: TextStyle(
                        fontSize: 10,
                        color: today ? AppColors.neonGold : AppColors.textSecondary,
                      )),
                      Text('${DailyRewardsService.rewardCycle[i]}',
                          style: TextStyle(
                            fontSize: 11, fontWeight: FontWeight.w900,
                            color: today ? AppColors.neonGold :
                                   claimed ? AppColors.neonGreen : AppColors.textPrimary,
                          )),
                      if (claimed) const Icon(Icons.check, size: 10, color: AppColors.neonGreen),
                    ],
                  ),
                );
              }),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.neonGold,
                  foregroundColor: AppColors.bg,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () async {
                  final reward = await DailyRewardsService.claim();
                  if (reward == null) return;
                  if (!context.mounted) return;
                  await context.read<PlayerProvider>().addCoins(reward);
                  final player = context.read<PlayerProvider>();
                  await player.setStreak(DailyRewardsService.currentStreak);
                  AudioService.playCoin();
                  if (context.mounted) Navigator.of(context).pop();
                },
                child: Text('NHẬN +${DailyRewardsService.todayRewardAmount} COIN',
                    style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
