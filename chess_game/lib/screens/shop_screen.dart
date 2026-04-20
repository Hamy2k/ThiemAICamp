import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../services/ads_service.dart';
import '../services/storage_service.dart';
import '../theme/app_theme.dart';
import '../widgets/coin_badge.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  static const skins = [
    {'id': 'classic', 'name': 'Classic', 'price': 0, 'accent': AppColors.neonCyan, 'type': 'board'},
    {'id': 'midnight', 'name': 'Midnight Purple', 'price': 300, 'accent': AppColors.neonPurple, 'type': 'board'},
    {'id': 'neon', 'name': 'Neon Pink', 'price': 500, 'accent': AppColors.neonPink, 'type': 'board'},
    {'id': 'gold', 'name': 'Gold Royale', 'price': 1200, 'accent': AppColors.neonGold, 'type': 'board'},
    {'id': 'classic', 'name': 'Classic Pieces', 'price': 0, 'accent': AppColors.neonCyan, 'type': 'pieces'},
    {'id': 'knight', 'name': 'Cyber Knights', 'price': 600, 'accent': AppColors.neonGreen, 'type': 'pieces'},
    {'id': 'elite', 'name': 'Elite Set', 'price': 1500, 'accent': AppColors.neonGold, 'type': 'pieces'},
  ];

  Future<void> _buy(Map item) async {
    final player = context.read<PlayerProvider>();
    final isBoard = item['type'] == 'board';
    final owned = isBoard ? player.unlockedBoards.contains(item['id']) :
                            player.unlockedPieces.contains(item['id']);
    if (owned) {
      if (isBoard) { await player.selectBoard(item['id']); }
      else { await player.selectPieces(item['id']); }
      return;
    }
    if (!await player.spendCoins(item['price'])) {
      _snack('Không đủ coin');
      return;
    }
    if (isBoard) {
      await player.unlockBoard(item['id']);
      await player.selectBoard(item['id']);
    } else {
      await player.unlockPieces(item['id']);
      await player.selectPieces(item['id']);
    }
    _snack('Đã mở ${item['name']}!');
  }

  void _snack(String m) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));
  }

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerProvider>();
    final adsRemoved = StorageService.getBool(StorageKeys.removeAds);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Shop'),
        actions: const [Padding(
            padding: EdgeInsets.only(right: 8),
            child: Center(child: CoinBadge(compact: true)))],
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _coinPacks(),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.neonGreen.withValues(alpha: 0.5)),
            ),
            child: Row(
              children: [
                const Icon(Icons.block, color: AppColors.neonGreen),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text('Tắt quảng cáo vĩnh viễn',
                      style: TextStyle(fontWeight: FontWeight.w700)),
                ),
                ElevatedButton(
                  onPressed: adsRemoved ? null : () async {
                    await StorageService.setBool(StorageKeys.removeAds, true);
                    setState(() {});
                    _snack('Đã tắt quảng cáo (MVP — IAP sẽ được tích hợp)');
                  },
                  child: Text(adsRemoved ? 'ĐÃ MUA' : '\$2.99'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          const Text('BÀN CỜ', style: TextStyle(
              color: AppColors.neonCyan, fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 2)),
          const SizedBox(height: 8),
          ...skins.where((s) => s['type'] == 'board').map((s) => _skinTile(s, player)),
          const SizedBox(height: 16),
          const Text('QUÂN CỜ', style: TextStyle(
              color: AppColors.neonPink, fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 2)),
          const SizedBox(height: 8),
          ...skins.where((s) => s['type'] == 'pieces').map((s) => _skinTile(s, player)),
        ],
      ),
    );
  }

  Widget _coinPacks() {
    final packs = [
      {'coins': 100, 'bonus': 0, 'price': '\$0.99'},
      {'coins': 500, 'bonus': 50, 'price': '\$3.99'},
      {'coins': 1500, 'bonus': 300, 'price': '\$9.99'},
    ];
    return Row(
      children: packs.map((p) => Expanded(
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: GestureDetector(
            onTap: () async {
              await context.read<PlayerProvider>().addCoins(
                  (p['coins'] as int) + (p['bonus'] as int));
              _snack('+${(p['coins'] as int) + (p['bonus'] as int)} coin (MVP — IAP sau)');
            },
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.neonGold.withValues(alpha: 0.6)),
              ),
              child: Column(
                children: [
                  const Icon(Icons.monetization_on, color: AppColors.neonGold, size: 28),
                  const SizedBox(height: 4),
                  Text('${p['coins']}',
                      style: const TextStyle(color: AppColors.neonGold, fontWeight: FontWeight.w900)),
                  if ((p['bonus'] as int) > 0)
                    Text('+${p['bonus']} bonus',
                        style: const TextStyle(color: AppColors.neonGreen, fontSize: 10)),
                  const SizedBox(height: 2),
                  Text(p['price'] as String,
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 11)),
                ],
              ),
            ),
          ),
        ),
      )).toList(),
    );
  }

  Widget _skinTile(Map s, PlayerProvider player) {
    final isBoard = s['type'] == 'board';
    final owned = isBoard ? player.unlockedBoards.contains(s['id']) :
                            player.unlockedPieces.contains(s['id']);
    final selected = isBoard ? player.selectedBoard == s['id'] :
                               player.selectedPieces == s['id'];
    final accent = s['accent'] as Color;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: accent.withValues(alpha: selected ? 0.9 : 0.4), width: selected ? 2 : 1),
      ),
      child: Row(
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [accent.withValues(alpha: 0.5), AppColors.bg]),
              borderRadius: BorderRadius.circular(6),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(s['name'], style: TextStyle(
              color: accent, fontWeight: FontWeight.w800))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: owned && selected ? AppColors.neonGreen :
                               owned ? accent : AppColors.card,
              foregroundColor: owned && selected ? AppColors.bg : accent,
              side: BorderSide(color: accent),
            ),
            onPressed: () => _buy(s),
            child: Text(
              owned && selected ? 'DÙNG' : owned ? 'Chọn' : '${s['price']} 🪙',
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
