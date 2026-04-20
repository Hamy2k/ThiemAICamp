class Pos {
  final int file;
  final int rank;
  const Pos(this.file, this.rank);

  bool get valid => file >= 0 && file < 8 && rank >= 0 && rank < 8;

  @override
  bool operator ==(Object other) =>
      other is Pos && other.file == file && other.rank == rank;

  @override
  int get hashCode => file * 8 + rank;

  @override
  String toString() => '${String.fromCharCode(97 + file)}${rank + 1}';

  Pos operator +(Pos o) => Pos(file + o.file, rank + o.rank);
}
