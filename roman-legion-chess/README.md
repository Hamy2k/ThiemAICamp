# Roman Legion Chess

Ancient Rome × Futuristic Empire — a chess game with boss battles & rule-breaks.

**Phase 1 status:** Playable core — human vs Easy AI in browser, placeholder graphics.

## Setup

Requires Node ≥ 20, pnpm ≥ 10.

```bash
pnpm install
```

## Dev (browser)

```bash
pnpm dev
```

Opens Vite on `http://localhost:5173`.

## Test

```bash
pnpm test         # one-shot
pnpm test:watch   # watch mode
```

## Build

```bash
pnpm build        # typecheck + vite build → dist/
pnpm preview      # serve the production build
```

## Lint / format

```bash
pnpm lint
pnpm format
pnpm typecheck
```

## Folder structure

```
roman-legion-chess/
├── index.html
├── public/assets/         # drop external assets here (Phase 1 uses fallbacks)
│   ├── pieces/, boards/, bosses/, ui/
│   └── audio/{sfx,music}/
├── src/
│   ├── main.ts            # entry
│   ├── game.ts            # Phaser config + scene list
│   ├── scenes/
│   │   ├── BootScene.ts   # no-op loader (Phase 1)
│   │   └── GameScene.ts   # board + interaction + AI
│   ├── core/
│   │   └── ChessEngine.ts # chess.js wrapper (typed API)
│   ├── ai/
│   │   ├── AIEngine.ts    # interface
│   │   └── AIEasy.ts      # random with capture bias
│   ├── ui/
│   │   └── EndGameModal.ts # Tailwind DOM overlay
│   ├── state/
│   │   └── gameStore.ts   # Zustand (no persistence yet)
│   ├── data/
│   │   ├── tuning.ts      # SSOT for timings, colors, AI depth
│   │   └── assetConfig.ts # SSOT for asset paths + letter fallbacks
│   ├── utils/
│   │   └── squareCoords.ts
│   └── styles/main.css    # Tailwind entry
└── tests/
    ├── core/ChessEngine.test.ts
    └── ai/AIEasy.test.ts
```

## Phase 1 acceptance

1. `pnpm install && pnpm dev` → open `localhost:5173`
2. 8×8 board, 32 placeholder pieces (colored squares + letters)
3. Click your pawn e2 → green dots on e3, e4
4. Click e4 → pawn slides (200ms), AI responds after 500ms
5. Play to checkmate/stalemate/draw → modal appears → `New Game` resets
6. `pnpm test` → all green
7. `pnpm build` → dist/ generated, no warnings

## Not yet (Phase 2+)

Promotion choice UI · undo · settings · main menu · assets · sound · Medium/Hard AI · Capacitor APK · bosses · progression.
