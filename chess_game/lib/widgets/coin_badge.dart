import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../theme/app_theme.dart';

class CoinBadge extends StatelessWidget {
  final bool compact;
  const CoinBadge({super.key, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final coins = context.watch<PlayerProvider>().coins;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 10 : 14, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.neonGold.withValues(alpha: 0.55), width: 1.2),
        boxShadow: [
          BoxShadow(color: AppColors.neonGold.withValues(alpha: 0.3), blurRadius: 12),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.monetization_on, color: AppColors.neonGold, size: 18),
          const SizedBox(width: 6),
          Text('$coins', style: const TextStyle(
            color: AppColors.neonGold, fontWeight: FontWeight.w800, fontSize: 15,
          )),
        ],
      ),
    );
  }
}
