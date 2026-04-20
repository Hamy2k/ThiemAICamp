import 'package:flutter/material.dart';

enum BossStyle { aggressive, defensive, balanced, tactical }

class Boss {
  final String id;
  final String name;
  final String title;
  final int difficulty;
  final BossStyle style;
  final int reward;
  final int unlockCost;
  final int requiredLevel;
  final String avatar;
  final Color accent;
  final String quote;

  const Boss({
    required this.id,
    required this.name,
    required this.title,
    required this.difficulty,
    required this.style,
    required this.reward,
    required this.unlockCost,
    required this.requiredLevel,
    required this.avatar,
    required this.accent,
    required this.quote,
  });
}
