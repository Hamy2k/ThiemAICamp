import '../models/puzzle.dart';

class PuzzleRepository {
  static final List<Puzzle> puzzles = [
    const Puzzle(
      id: 'm1-001', title: 'Chiếu hết 1 nước #1',
      fen: '6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1',
      solutionUci: ['a1a8'], rating: 800, reward: 20,
    ),
    const Puzzle(
      id: 'm1-002', title: 'Chiếu hết 1 nước #2',
      fen: 'r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1',
      solutionUci: ['a8a1'], rating: 800, reward: 20,
    ),
    const Puzzle(
      id: 'm1-003', title: 'Smothered mate',
      fen: '6rk/6pp/8/6N1/8/8/8/6K1 w - - 0 1',
      solutionUci: ['g5f7'], rating: 1100, reward: 30,
    ),
    const Puzzle(
      id: 'm1-004', title: 'Back rank mate',
      fen: '3r2k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1',
      solutionUci: ['d1d8'], rating: 900, reward: 25,
    ),
    const Puzzle(
      id: 'm1-005', title: 'Queen sac mate',
      fen: '6k1/5ppp/8/8/8/8/4QPPP/6K1 w - - 0 1',
      solutionUci: ['e2e8'], rating: 1000, reward: 28,
    ),
    const Puzzle(
      id: 'm2-001', title: 'Chiếu hết 2 nước #1',
      fen: '6k1/5ppp/8/8/8/8/Q4PPP/6K1 w - - 0 1',
      solutionUci: ['a2a8', 'g8a8'], rating: 1300, reward: 50,
    ),
    const Puzzle(
      id: 'm2-002', title: 'Knight fork mate',
      fen: '4k3/8/3N4/8/8/8/8/4K2R w K - 0 1',
      solutionUci: ['d6f7', 'e8e7'], rating: 1400, reward: 55,
    ),
    const Puzzle(
      id: 'm1-006', title: 'Rook lift mate',
      fen: '7k/6pp/8/8/8/8/R6P/6K1 w - - 0 1',
      solutionUci: ['a2a8'], rating: 850, reward: 22,
    ),
  ];

  static Puzzle dailyPuzzle(DateTime date) {
    final idx = (date.year * 366 + date.month * 31 + date.day) % puzzles.length;
    return puzzles[idx];
  }

  static List<Puzzle> todaysThree() {
    final n = DateTime.now();
    final seed = n.year * 366 + n.month * 31 + n.day;
    return [
      puzzles[seed % puzzles.length],
      puzzles[(seed + 3) % puzzles.length],
      puzzles[(seed + 7) % puzzles.length],
    ];
  }

  static List<Puzzle> unlocked(int playerLevel) {
    final count = (playerLevel * 3).clamp(3, puzzles.length);
    return puzzles.take(count).toList();
  }
}
