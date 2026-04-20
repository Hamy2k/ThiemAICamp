import 'package:flutter/material.dart';
import '../models/boss.dart';
import '../theme/app_theme.dart';

class BossRepository {
  static const bosses = <Boss>[
    Boss(
      id: 'b01', name: 'Rook Rookie', title: 'Tân binh xe pháo',
      difficulty: 1, style: BossStyle.balanced,
      reward: 80, unlockCost: 0, requiredLevel: 1,
      avatar: '♜', accent: AppColors.neonCyan,
      quote: 'Lên bàn đi nhóc. Đừng để tao phải hối.',
    ),
    Boss(
      id: 'b02', name: 'Knight Nyx', title: 'Bóng đêm kỵ sĩ',
      difficulty: 2, style: BossStyle.aggressive,
      reward: 150, unlockCost: 200, requiredLevel: 3,
      avatar: '♞', accent: AppColors.neonPink,
      quote: 'Tao sẽ nuốt vua ngươi bằng hai nước ngựa.',
    ),
    Boss(
      id: 'b03', name: 'Bishop Bask', title: 'Giáo chủ chéo',
      difficulty: 2, style: BossStyle.tactical,
      reward: 200, unlockCost: 400, requiredLevel: 5,
      avatar: '♝', accent: AppColors.neonPurple,
      quote: 'Đường chéo là chân lý. Ngươi sẽ hiểu.',
    ),
    Boss(
      id: 'b04', name: 'Wall Warden', title: 'Bức tường thép',
      difficulty: 3, style: BossStyle.defensive,
      reward: 320, unlockCost: 700, requiredLevel: 8,
      avatar: '♛', accent: AppColors.neonGreen,
      quote: 'Không ai phá được phòng tuyến của ta.',
    ),
    Boss(
      id: 'b05', name: 'Queen Vex', title: 'Nữ hoàng sấm sét',
      difficulty: 4, style: BossStyle.aggressive,
      reward: 500, unlockCost: 1200, requiredLevel: 12,
      avatar: '♕', accent: AppColors.neonGold,
      quote: 'Ngôi vua của ngươi sẽ thành tro.',
    ),
    Boss(
      id: 'b06', name: 'Grand Zero', title: 'Đại Sư Hư Không',
      difficulty: 5, style: BossStyle.tactical,
      reward: 1000, unlockCost: 2500, requiredLevel: 18,
      avatar: '♚', accent: AppColors.neonPink,
      quote: 'Hãy thử đi. Ta đã thấy trước 20 nước của ngươi.',
    ),
  ];
}
