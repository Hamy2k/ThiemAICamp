import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../services/daily_rewards_service.dart';
import '../services/ads_service.dart';
import '../theme/app_theme.dart';
import '../widgets/coin_badge.dart';
import '../widgets/neon_button.dart';
import '../widgets/xp_bar.dart';
import 'game_screen.dart';
import 'daily_challenge_screen.dart';
import 'puzzle_screen.dart';
import 'battle_screen.dart';
import 'shop_screen.dart';
import 'daily_login_dialog.dart';

class MainMenuScreen extends StatefulWidget {
  const MainMenuScreen({super.key});

  @override
  State<MainMenuScreen> createState() => _MainMenuScreenState();
}

class _MainMenuScreenState extends State<MainMenuScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkDailyLogin());
  }

  Future<void> _checkDailyLogin() async {
    if (!DailyRewardsService.canClaimToday) return;
    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const DailyLoginDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment.topCenter, radius: 1.2,
            colors: [Color(0xFF1A1F3D), AppColors.bg],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              children: [
                _topBar(),
                const SizedBox(height: 14),
                const XpBar(),
                const SizedBox(height: 20),
                _logo(),
                const SizedBox(height: 24),
                Expanded(child: _menuList()),
                _footer(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _topBar() {
    final streak = context.watch<PlayerProvider>().streak;
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.neonPink.withValues(alpha: 0.55)),
          ),
          child: Row(
            children: [
              const Icon(Icons.local_fire_department, color: AppColors.neonPink, size: 18),
              const SizedBox(width: 4),
              Text('$streak', style: const TextStyle(
                color: AppColors.neonPink, fontWeight: FontWeight.w800,
              )),
            ],
          ),
        ),
        const Spacer(),
        const CoinBadge(),
        const SizedBox(width: 8),
        IconButton(
          icon: const Icon(Icons.settings, color: AppColors.textSecondary),
          onPressed: () => _openShop(),
        ),
      ],
    );
  }

  Widget _logo() {
    return Column(
      children: [
        ShaderMask(
          shaderCallback: (r) => const LinearGradient(
            colors: [AppColors.neonCyan, AppColors.neonPink],
          ).createShader(r),
          child: const Text(
            'NEON CHESS',
            style: TextStyle(
              fontSize: 38, fontWeight: FontWeight.w900,
              color: Colors.white, letterSpacing: 4,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Cờ vua — Bật chế độ nghiện',
          style: TextStyle(
            color: AppColors.textSecondary.withValues(alpha: 0.8),
            fontSize: 12, letterSpacing: 2,
          ),
        ),
      ],
    );
  }

  Widget _menuList() {
    return ListView(
      children: [
        NeonButton(
          label: 'CHƠI NHANH', subtitle: 'Đấu AI — 3 cấp độ',
          icon: Icons.flash_on, color: AppColors.neonCyan,
          onTap: () => _go(const GameScreen(modeName: 'ai')),
        ),
        const SizedBox(height: 10),
        NeonButton(
          label: 'DAILY CHALLENGE',
          subtitle: DailyRewardsService.didDailyChallengeToday()
              ? '✓ Hoàn thành — quay lại mai' : '3 câu đố · streak ${context.watch<PlayerProvider>().streak}',
          icon: Icons.calendar_today, color: AppColors.neonGold,
          onTap: () => _go(const DailyChallengeScreen()),
        ),
        const SizedBox(height: 10),
        NeonButton(
          label: 'BOSS BATTLE',
          subtitle: '6 boss — phong cách AI độc đáo',
          icon: Icons.whatshot, color: AppColors.neonPink,
          onTap: () => _go(const BattleScreen()),
        ),
        const SizedBox(height: 10),
        NeonButton(
          label: 'PUZZLE',
          subtitle: 'Mate in 1/2 — ${context.watch<PlayerProvider>().puzzlesSolved} đã giải',
          icon: Icons.extension, color: AppColors.neonPurple,
          onTap: () => _go(const PuzzleScreen()),
        ),
        const SizedBox(height: 10),
        NeonButton(
          label: '2 NGƯỜI (OFFLINE)',
          subtitle: 'Chia màn hình cùng bạn',
          icon: Icons.people, color: AppColors.neonGreen,
          onTap: () => _go(const GameScreen(modeName: 'local')),
        ),
        const SizedBox(height: 10),
        NeonButton(
          label: 'SHOP / SKIN',
          subtitle: 'Mở skin bàn cờ + quân',
          icon: Icons.shopping_bag, color: AppColors.neonGold,
          onTap: _openShop,
        ),
      ],
    );
  }

  Widget _footer() {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: GestureDetector(
        onTap: _watchAdForCoins,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.neonGreen.withValues(alpha: 0.5)),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.play_circle_fill, color: AppColors.neonGreen),
              SizedBox(width: 8),
              Text('Xem quảng cáo → +25 coin',
                  style: TextStyle(color: AppColors.neonGreen, fontWeight: FontWeight.w700)),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _watchAdForCoins() async {
    final ok = await AdsService.showRewarded(onReward: (_) {
      context.read<PlayerProvider>().addCoins(25);
    });
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Ad chưa sẵn sàng. Thử lại sau.'),
      ));
    }
  }

  void _openShop() {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ShopScreen()));
  }

  void _go(Widget w) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => w));
  }
}
