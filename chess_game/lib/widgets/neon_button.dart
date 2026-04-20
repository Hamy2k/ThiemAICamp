import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class NeonButton extends StatefulWidget {
  final String label;
  final IconData? icon;
  final Color color;
  final VoidCallback? onTap;
  final double height;
  final String? subtitle;

  const NeonButton({
    super.key,
    required this.label,
    this.icon,
    this.color = AppColors.neonCyan,
    this.onTap,
    this.height = 64,
    this.subtitle,
  });

  @override
  State<NeonButton> createState() => _NeonButtonState();
}

class _NeonButtonState extends State<NeonButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final disabled = widget.onTap == null;
    return GestureDetector(
      onTapDown: disabled ? null : (_) => setState(() => _pressed = true),
      onTapUp: disabled ? null : (_) => setState(() => _pressed = false),
      onTapCancel: () => setState(() => _pressed = false),
      onTap: widget.onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 120),
        height: widget.height,
        transform: Matrix4.identity()..scale(_pressed ? 0.97 : 1.0),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: widget.color.withValues(alpha: disabled ? 0.25 : 0.7), width: 1.6),
          boxShadow: disabled ? [] : [
            BoxShadow(
              color: widget.color.withValues(alpha: _pressed ? 0.2 : 0.45),
              blurRadius: _pressed ? 6 : 16,
              spreadRadius: _pressed ? 0 : 1,
            ),
          ],
          gradient: LinearGradient(
            begin: Alignment.topLeft, end: Alignment.bottomRight,
            colors: [
              AppColors.card,
              widget.color.withValues(alpha: 0.12),
            ],
          ),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 18),
        child: Row(
          children: [
            if (widget.icon != null) ...[
              Icon(widget.icon, color: widget.color, size: 26),
              const SizedBox(width: 14),
            ],
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.label,
                    style: TextStyle(
                      color: disabled ? AppColors.textSecondary : AppColors.textPrimary,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                  if (widget.subtitle != null)
                    Text(
                      widget.subtitle!,
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                    ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: widget.color.withValues(alpha: 0.8)),
          ],
        ),
      ),
    );
  }
}
