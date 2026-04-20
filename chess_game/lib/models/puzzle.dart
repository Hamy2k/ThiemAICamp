class Puzzle {
  final String id;
  final String fen;
  final List<String> solutionUci;
  final String title;
  final int rating;
  final int reward;

  const Puzzle({
    required this.id,
    required this.fen,
    required this.solutionUci,
    required this.title,
    this.rating = 1000,
    this.reward = 20,
  });
}
