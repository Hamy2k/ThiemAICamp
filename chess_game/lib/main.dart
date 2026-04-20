import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'providers/player_provider.dart';
import 'screens/splash_screen.dart';
import 'services/ads_service.dart';
import 'services/audio_service.dart';
import 'services/storage_service.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  await StorageService.init();
  await AudioService.init();
  AdsService.init();

  runApp(
    ChangeNotifierProvider(
      create: (_) => PlayerProvider(),
      child: const NeonChessApp(),
    ),
  );
}

class NeonChessApp extends StatelessWidget {
  const NeonChessApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Neon Chess',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      home: const SplashScreen(),
    );
  }
}
