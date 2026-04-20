import 'storage_service.dart';

class DailyRewardsService {
  static const rewardCycle = [50, 80, 120, 180, 250, 400, 700];

  static DateTime _today() {
    final n = DateTime.now();
    return DateTime(n.year, n.month, n.day);
  }

  static DateTime? _lastLogin() {
    final s = StorageService.getStr(StorageKeys.lastLogin);
    if (s.isEmpty) return null;
    return DateTime.tryParse(s);
  }

  static bool get canClaimToday {
    final last = _lastLogin();
    if (last == null) return true;
    return _today().isAfter(last);
  }

  static int get currentStreak => StorageService.getInt(StorageKeys.streak);

  static int get todayRewardAmount {
    final streak = currentStreak;
    final idx = streak % rewardCycle.length;
    return rewardCycle[idx];
  }

  static Future<int?> claim() async {
    if (!canClaimToday) return null;
    final last = _lastLogin();
    final today = _today();
    int newStreak;
    if (last == null) {
      newStreak = 1;
    } else {
      final diff = today.difference(last).inDays;
      newStreak = diff == 1 ? currentStreak + 1 : 1;
    }
    final idx = (newStreak - 1) % rewardCycle.length;
    final reward = rewardCycle[idx];
    await StorageService.setInt(StorageKeys.streak, newStreak);
    await StorageService.setStr(StorageKeys.lastLogin, today.toIso8601String());
    return reward;
  }

  static bool didDailyChallengeToday() {
    final s = StorageService.getStr(StorageKeys.lastDailyChallenge);
    if (s.isEmpty) return false;
    final last = DateTime.tryParse(s);
    if (last == null) return false;
    return last.isAtSameMomentAs(_today()) ||
        (last.year == _today().year && last.month == _today().month && last.day == _today().day);
  }

  static Future<void> markDailyChallengeDone() async {
    await StorageService.setStr(StorageKeys.lastDailyChallenge, _today().toIso8601String());
    final done = StorageService.getInt(StorageKeys.dailyChallengesDone);
    await StorageService.setInt(StorageKeys.dailyChallengesDone, done + 1);
  }
}
