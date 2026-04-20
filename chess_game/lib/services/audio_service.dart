import 'package:audioplayers/audioplayers.dart';
import 'package:vibration/vibration.dart';
import 'storage_service.dart';

class AudioService {
  static final _move = AudioPlayer();
  static final _capture = AudioPlayer();
  static final _win = AudioPlayer();
  static final _lose = AudioPlayer();
  static final _coin = AudioPlayer();

  static Future<void> init() async {
    for (final p in [_move, _capture, _win, _lose, _coin]) {
      await p.setReleaseMode(ReleaseMode.stop);
    }
  }

  static bool get _on => StorageService.getBool(StorageKeys.soundEnabled, true);
  static bool get _vib => StorageService.getBool(StorageKeys.vibrationEnabled, true);

  static Future<void> _play(AudioPlayer p, String asset) async {
    if (!_on) return;
    try {
      await p.stop();
      await p.play(AssetSource(asset));
    } catch (_) {}
  }

  static Future<void> playMove() async {
    await _play(_move, 'sounds/move.mp3');
    if (_vib) Vibration.vibrate(duration: 15);
  }

  static Future<void> playCapture() async {
    await _play(_capture, 'sounds/capture.mp3');
    if (_vib) Vibration.vibrate(duration: 30);
  }

  static Future<void> playWin() => _play(_win, 'sounds/win.mp3');
  static Future<void> playLose() => _play(_lose, 'sounds/lose.mp3');
  static Future<void> playCoin() => _play(_coin, 'sounds/coin.mp3');
}
