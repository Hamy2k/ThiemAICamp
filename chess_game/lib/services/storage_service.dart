import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static late SharedPreferences _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static int getInt(String key, [int def = 0]) => _prefs.getInt(key) ?? def;
  static Future<void> setInt(String key, int v) => _prefs.setInt(key, v);

  static String getStr(String key, [String def = '']) => _prefs.getString(key) ?? def;
  static Future<void> setStr(String key, String v) => _prefs.setString(key, v);

  static bool getBool(String key, [bool def = false]) => _prefs.getBool(key) ?? def;
  static Future<void> setBool(String key, bool v) => _prefs.setBool(key, v);

  static List<String> getStrList(String key) => _prefs.getStringList(key) ?? const [];
  static Future<void> setStrList(String key, List<String> v) => _prefs.setStringList(key, v);
}

class StorageKeys {
  static const coins = 'coins';
  static const xp = 'xp';
  static const level = 'level';
  static const streak = 'streak';
  static const lastLogin = 'lastLogin';
  static const lastDailyChallenge = 'lastDailyChallenge';
  static const dailyChallengesDone = 'dailyChallengesDone';
  static const puzzlesSolved = 'puzzlesSolved';
  static const bossesDefeated = 'bossesDefeated';
  static const matchesPlayed = 'matchesPlayed';
  static const selectedBoard = 'selectedBoard';
  static const selectedPieces = 'selectedPieces';
  static const unlockedBoards = 'unlockedBoards';
  static const unlockedPieces = 'unlockedPieces';
  static const removeAds = 'removeAds';
  static const soundEnabled = 'soundEnabled';
  static const vibrationEnabled = 'vibrationEnabled';
}
