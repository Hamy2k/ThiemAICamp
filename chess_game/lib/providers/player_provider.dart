import 'package:flutter/foundation.dart';
import '../services/storage_service.dart';

class PlayerProvider extends ChangeNotifier {
  int _coins = 0;
  int _xp = 0;
  int _level = 1;
  int _streak = 0;
  int _matchesPlayed = 0;
  int _puzzlesSolved = 0;
  Set<String> _unlockedBoards = {'classic'};
  Set<String> _unlockedPieces = {'classic'};
  String _selectedBoard = 'classic';
  String _selectedPieces = 'classic';

  int get coins => _coins;
  int get xp => _xp;
  int get level => _level;
  int get streak => _streak;
  int get matchesPlayed => _matchesPlayed;
  int get puzzlesSolved => _puzzlesSolved;
  Set<String> get unlockedBoards => _unlockedBoards;
  Set<String> get unlockedPieces => _unlockedPieces;
  String get selectedBoard => _selectedBoard;
  String get selectedPieces => _selectedPieces;

  int get xpForNextLevel => 100 + (_level - 1) * 75;
  double get levelProgress => _xp / xpForNextLevel;

  PlayerProvider() {
    _load();
  }

  void _load() {
    _coins = StorageService.getInt(StorageKeys.coins, 100);
    _xp = StorageService.getInt(StorageKeys.xp);
    _level = StorageService.getInt(StorageKeys.level, 1);
    _streak = StorageService.getInt(StorageKeys.streak);
    _matchesPlayed = StorageService.getInt(StorageKeys.matchesPlayed);
    _puzzlesSolved = StorageService.getInt(StorageKeys.puzzlesSolved);
    _unlockedBoards = StorageService.getStrList(StorageKeys.unlockedBoards).toSet();
    if (_unlockedBoards.isEmpty) _unlockedBoards = {'classic'};
    _unlockedPieces = StorageService.getStrList(StorageKeys.unlockedPieces).toSet();
    if (_unlockedPieces.isEmpty) _unlockedPieces = {'classic'};
    _selectedBoard = StorageService.getStr(StorageKeys.selectedBoard, 'classic');
    _selectedPieces = StorageService.getStr(StorageKeys.selectedPieces, 'classic');
  }

  Future<void> addCoins(int amount) async {
    _coins += amount;
    await StorageService.setInt(StorageKeys.coins, _coins);
    notifyListeners();
  }

  Future<bool> spendCoins(int amount) async {
    if (_coins < amount) return false;
    _coins -= amount;
    await StorageService.setInt(StorageKeys.coins, _coins);
    notifyListeners();
    return true;
  }

  Future<int> addXp(int amount) async {
    _xp += amount;
    int leveledUp = 0;
    while (_xp >= xpForNextLevel) {
      _xp -= xpForNextLevel;
      _level++;
      leveledUp++;
    }
    await StorageService.setInt(StorageKeys.xp, _xp);
    await StorageService.setInt(StorageKeys.level, _level);
    notifyListeners();
    return leveledUp;
  }

  Future<void> setStreak(int v) async {
    _streak = v;
    await StorageService.setInt(StorageKeys.streak, _streak);
    notifyListeners();
  }

  Future<void> incMatch() async {
    _matchesPlayed++;
    await StorageService.setInt(StorageKeys.matchesPlayed, _matchesPlayed);
    notifyListeners();
  }

  Future<void> incPuzzle() async {
    _puzzlesSolved++;
    await StorageService.setInt(StorageKeys.puzzlesSolved, _puzzlesSolved);
    notifyListeners();
  }

  Future<void> unlockBoard(String id) async {
    _unlockedBoards.add(id);
    await StorageService.setStrList(StorageKeys.unlockedBoards, _unlockedBoards.toList());
    notifyListeners();
  }

  Future<void> unlockPieces(String id) async {
    _unlockedPieces.add(id);
    await StorageService.setStrList(StorageKeys.unlockedPieces, _unlockedPieces.toList());
    notifyListeners();
  }

  Future<void> selectBoard(String id) async {
    _selectedBoard = id;
    await StorageService.setStr(StorageKeys.selectedBoard, id);
    notifyListeners();
  }

  Future<void> selectPieces(String id) async {
    _selectedPieces = id;
    await StorageService.setStr(StorageKeys.selectedPieces, id);
    notifyListeners();
  }
}
