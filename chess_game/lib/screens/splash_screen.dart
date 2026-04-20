import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'main_menu_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 1200), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(MaterialPageRoute(
        builder: (_) => const MainMenuScreen(),
      ));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(colors: [Color(0xFF1A1F3D), AppColors.bg]),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 120, height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: [AppColors.neonCyan, AppColors.neonPink],
                  ),
                  boxShadow: [
                    BoxShadow(color: AppColors.neonCyan.withValues(alpha: 0.6), blurRadius: 40, spreadRadius: 4),
                  ],
                ),
                child: const Center(
                  child: Text('♚', style: TextStyle(fontSize: 70, color: Colors.white)),
                ),
              ),
              const SizedBox(height: 24),
              ShaderMask(
                shaderCallback: (r) => const LinearGradient(
                  colors: [AppColors.neonCyan, AppColors.neonPink],
                ).createShader(r),
                child: const Text('NEON CHESS',
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 4)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
