Place these sound files here (use any royalty-free source like freesound.org):

- move.mp3       (quick click, ~100ms)
- capture.mp3    (sharp thud, ~200ms)
- win.mp3        (short fanfare, ~1s)
- lose.mp3       (descending note, ~1s)
- coin.mp3       (coin jingle, ~400ms)

AudioService handles missing files gracefully (play calls are try/catch'd),
so the app will still run without them — just silent.
