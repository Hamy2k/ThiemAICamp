import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../theme/app_theme.dart';

class XpBar extends StatelessWidget {
  const XpBar({super.key});

  @override
  Widget build(BuildContext context) {
    final p = context.watch<PlayerProvider>();
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.neonPurple.withValues(alpha: 0.5), width: 1.2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.neonPurple.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.neonPurple),
                ),
                child: Text('LV ${p.level}', style: const TextStyle(
                  color: AppColors.neonPurple, fontWeight: FontWeight.w900, fontSize: 13,
                )),
              ),
              const Spacer(),
              Text('${p.xp} / ${p.xpForNextLevel} XP',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: p.levelProgress.clamp(0, 1),
              minHeight: 8,
              backgroundColor: AppColors.bg,
              valueColor: const AlwaysStoppedAnimation(AppColors.neonPurple),
            ),
          ),
        ],
      ),
    );
  }
}
