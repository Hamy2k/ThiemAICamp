import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const bg = Color(0xFF0A0E1A);
  static const surface = Color(0xFF121829);
  static const card = Color(0xFF1A2138);
  static const neonCyan = Color(0xFF00E5FF);
  static const neonPink = Color(0xFFFF2D95);
  static const neonPurple = Color(0xFFB537F2);
  static const neonGold = Color(0xFFFFD54F);
  static const neonGreen = Color(0xFF00FF9D);
  static const lightSquare = Color(0xFF3A4A6B);
  static const darkSquare = Color(0xFF1E2740);
  static const highlight = Color(0x8000E5FF);
  static const lastMove = Color(0x80B537F2);
  static const check = Color(0xFFFF2D95);
  static const textPrimary = Color(0xFFF0F4FF);
  static const textSecondary = Color(0xFF8A95B8);
}

class AppTheme {
  static ThemeData dark() {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: AppColors.bg,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.neonCyan,
        secondary: AppColors.neonPink,
        surface: AppColors.surface,
        onPrimary: AppColors.bg,
        onSurface: AppColors.textPrimary,
      ),
      textTheme: GoogleFonts.orbitronTextTheme(base.textTheme).apply(
        bodyColor: AppColors.textPrimary,
        displayColor: AppColors.textPrimary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
    );
  }
}

BoxDecoration neonGlow({
  Color color = AppColors.neonCyan,
  double radius = 12,
  double blur = 18,
}) =>
    BoxDecoration(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(color: color.withValues(alpha: 0.6), width: 1.5),
      boxShadow: [
        BoxShadow(color: color.withValues(alpha: 0.35), blurRadius: blur, spreadRadius: 1),
      ],
    );
