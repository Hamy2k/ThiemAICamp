import Phaser from 'phaser';
import type { Square } from 'chess.js';
import {
  ChessEngine,
  type BoardPiece,
  type Color,
  type LegalMove,
  type PieceType,
} from '@/core/ChessEngine';
import { AIEasy } from '@/ai/AIEasy';
import type { AIEngine } from '@/ai/AIEngine';
import { useGameStore } from '@/state/gameStore';
import { BOARD, COLORS, TIMINGS, GAME, FONTS } from '@/data/tuning';
import { PIECE_LETTERS, PIECE_TYPE_TO_KEY } from '@/data/assetConfig';
import { frToSquare, squareToFR } from '@/utils/squareCoords';
import { EndGameModal } from '@/ui/EndGameModal';
import { pieceTextureKey } from '@/scenes/BootScene';

interface PieceView {
  container: Phaser.GameObjects.Container;
  square: Square;
}

interface PulseMark {
  obj: Phaser.GameObjects.Arc | Phaser.GameObjects.Graphics;
  tween?: Phaser.Tweens.Tween;
}

const BACK_BTN_DOM_ID = 'game-back-btn';

export class GameScene extends Phaser.Scene {
  private engine!: ChessEngine;
  private ai!: AIEngine;

  private boardX = 0;
  private boardY = 0;
  private tileSize = 0;

  private pieces: Map<Square, PieceView> = new Map();
  private legalMarks: PulseMark[] = [];
  private selected: Square | null = null;
  private selectedHighlight: Phaser.GameObjects.Rectangle | null = null;
  private lastMoveMarks: Phaser.GameObjects.Rectangle[] = [];
  private hoverTints: Map<string, Phaser.GameObjects.Rectangle> = new Map();

  private aiThinking = false;
  private modal = new EndGameModal();

  constructor() {
    super({ key: 'GameScene' });
  }

  create(): void {
    this.engine = new ChessEngine();
    this.ai = new AIEasy();

    this.cameras.main.setBackgroundColor(COLORS.BG);
    this.computeLayout();
    this.drawBackdrop();
    this.drawBoardFrame();
    this.drawTiles();
    this.drawCoordinates();
    this.renderPieces();
    this.attachInput();
    this.mountBackButton();

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.unmountBackButton());
    this.scale.on('resize', this.handleResize, this);

    const { humanColor } = useGameStore.getState();
    if (humanColor !== this.engine.getTurn()) {
      this.queueAiMove();
    }
  }

  // ═══════════════════════════════ Layout ═══════════════════════════════

  private computeLayout(): void {
    const w = this.scale.width;
    const h = this.scale.height;
    const side = Math.min(w, h) * BOARD.VIEWPORT_PCT;
    this.tileSize = Math.floor(side / BOARD.FILES);
    const boardSide = this.tileSize * BOARD.FILES;
    this.boardX = Math.floor((w - boardSide) / 2);
    this.boardY = Math.floor((h - boardSide) / 2);
  }

  private tileTopLeft(file: number, rank: number): { x: number; y: number } {
    return {
      x: this.boardX + file * this.tileSize,
      y: this.boardY + (7 - rank) * this.tileSize,
    };
  }

  // ═══════════════════════════════ Draw ═══════════════════════════════

  private drawBackdrop(): void {
    const w = this.scale.width;
    const h = this.scale.height;
    this.add.rectangle(w / 2, h / 2, w, h, COLORS.BG);
    // Subtle crimson wash top, obsidian bottom
    this.add.rectangle(w / 2, h * 0.3, w, h * 0.6, COLORS.CRIMSON_DEEP, 0.05);
  }

  private drawBoardFrame(): void {
    const boardSide = this.tileSize * 8;
    const cx = this.boardX + boardSide / 2;
    const cy = this.boardY + boardSide / 2;

    // Outer glow rings (fake box-shadow)
    for (let i = BOARD.FRAME_GLOW_RINGS; i >= 1; i--) {
      const extra = BOARD.FRAME_THICKNESS + i * 5;
      this.add
        .rectangle(cx, cy, boardSide + extra * 2, boardSide + extra * 2)
        .setStrokeStyle(2, COLORS.GOLD, 0.08 * i);
    }

    // Main gold frame
    this.add
      .rectangle(
        cx,
        cy,
        boardSide + BOARD.FRAME_THICKNESS * 2,
        boardSide + BOARD.FRAME_THICKNESS * 2
      )
      .setStrokeStyle(BOARD.FRAME_THICKNESS, COLORS.GOLD);

    // Inner 1px dark line for "double border"
    this.add
      .rectangle(cx, cy, boardSide + 2, boardSide + 2)
      .setStrokeStyle(1, COLORS.OBSIDIAN_DEEP);
  }

  private drawTiles(): void {
    for (let rank = 0; rank < 8; rank++) {
      for (let file = 0; file < 8; file++) {
        const isLight = (file + rank) % 2 === 1;
        const { x, y } = this.tileTopLeft(file, rank);
        const cx = x + this.tileSize / 2;
        const cy = y + this.tileSize / 2;
        const baseColor = isLight ? COLORS.TILE_LIGHT : COLORS.TILE_DARK;

        const rect = this.add
          .rectangle(cx, cy, this.tileSize, this.tileSize, baseColor)
          .setInteractive({ useHandCursor: true });

        rect.on('pointerdown', () => this.onSquareClick(file, rank));
        rect.on('pointerover', () => this.onHoverEnter(file, rank, isLight));
        rect.on('pointerout', () => this.onHoverExit(file, rank));

        this.drawTileVein(x, y, isLight);
      }
    }
  }

  private drawTileVein(x: number, y: number, isLight: boolean): void {
    const g = this.add.graphics();
    if (isLight) {
      // Two subtle marble veins
      g.lineStyle(1, COLORS.TILE_LIGHT_VEIN, 0.4);
      g.beginPath();
      g.moveTo(x, y + this.tileSize * 0.32);
      g.lineTo(x + this.tileSize, y + this.tileSize * 0.48);
      g.strokePath();
      g.beginPath();
      g.moveTo(x + this.tileSize * 0.25, y);
      g.lineTo(x + this.tileSize * 0.78, y + this.tileSize);
      g.strokePath();
    } else {
      // Crimson energy wash (diagonal)
      g.lineStyle(2, COLORS.TILE_DARK_VEIN, 0.12);
      g.beginPath();
      g.moveTo(x + this.tileSize * 0.1, y);
      g.lineTo(x + this.tileSize * 0.95, y + this.tileSize);
      g.strokePath();
    }
    g.setDepth(0.1);
  }

  private drawCoordinates(): void {
    const fontSize = Math.max(11, Math.floor(this.tileSize * BOARD.COORDINATE_LABEL_PCT * 6));
    const style = {
      fontFamily: FONTS.NUMERIC,
      fontSize: `${fontSize}px`,
      color: this.rgbFromInt(COLORS.COORD_LABEL),
    };

    for (let i = 0; i < 8; i++) {
      const file = String.fromCharCode('a'.charCodeAt(0) + i);
      const { x, y } = this.tileTopLeft(i, 0);
      this.add
        .text(x + this.tileSize / 2, y + this.tileSize + 6, file, style)
        .setOrigin(0.5, 0);

      const rankLabel = `${i + 1}`;
      const { x: rx, y: ry } = this.tileTopLeft(0, i);
      this.add
        .text(rx - 6, ry + this.tileSize / 2, rankLabel, style)
        .setOrigin(1, 0.5);
    }
  }

  // ═══════════════════════════════ Pieces ═══════════════════════════════

  private renderPieces(): void {
    this.pieces.forEach((p) => p.container.destroy());
    this.pieces.clear();

    const board = this.engine.getBoard();
    for (let rank = 0; rank < 8; rank++) {
      for (let file = 0; file < 8; file++) {
        const cell = board[7 - rank]?.[file];
        if (!cell) continue;
        const sq = frToSquare(file, rank);
        this.addPieceView(sq, cell);
      }
    }
  }

  private addPieceView(square: Square, piece: BoardPiece): void {
    const { file, rank } = squareToFR(square);
    const { x, y } = this.tileTopLeft(file, rank);
    const cx = x + this.tileSize / 2;
    const cy = y + this.tileSize / 2;
    const size = this.tileSize * 0.86;

    const typeKey = PIECE_TYPE_TO_KEY[piece.type];
    const texKey = typeKey ? pieceTextureKey(piece.color, typeKey) : '';
    const hasTexture = texKey && this.textures.exists(texKey);

    const content: Phaser.GameObjects.GameObject[] = [];
    if (hasTexture) {
      const img = this.add.image(0, 0, texKey);
      img.setDisplaySize(size, size);
      content.push(img);
    } else {
      // Fallback: rounded rect + letter
      const isWhite = piece.color === 'w';
      const bgColor = isWhite ? COLORS.PIECE_WHITE_BG : COLORS.PIECE_BLACK_BG;
      const textColor = isWhite ? COLORS.PIECE_WHITE_TEXT : COLORS.PIECE_BLACK_TEXT;
      const borderColor = isWhite ? COLORS.PIECE_WHITE_BORDER : COLORS.PIECE_BLACK_BORDER;

      const bg = this.add.rectangle(0, 0, size, size, bgColor).setStrokeStyle(2, borderColor);
      const label = this.add
        .text(0, 0, PIECE_LETTERS[piece.type] ?? '?', {
          fontFamily: FONTS.DISPLAY,
          fontSize: `${Math.floor(size * 0.55)}px`,
          fontStyle: 'bold',
          color: this.rgbFromInt(textColor),
        })
        .setOrigin(0.5);
      content.push(bg, label);
    }

    const container = this.add.container(cx, cy, content).setSize(size, size).setDepth(2);
    this.pieces.set(square, { container, square });
  }

  // ═══════════════════════════════ Interaction ═══════════════════════════════

  private attachInput(): void {
    this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      const boardRight = this.boardX + this.tileSize * 8;
      const boardBottom = this.boardY + this.tileSize * 8;
      if (
        pointer.x < this.boardX ||
        pointer.x > boardRight ||
        pointer.y < this.boardY ||
        pointer.y > boardBottom
      ) {
        this.clearSelection();
      }
    });
  }

  private onHoverEnter(file: number, rank: number, isLight: boolean): void {
    if (this.aiThinking) return;
    const key = `${file}_${rank}`;
    if (this.hoverTints.has(key)) return;
    const { x, y } = this.tileTopLeft(file, rank);
    const tintColor = isLight ? COLORS.GOLD : COLORS.CRIMSON;
    const tint = this.add
      .rectangle(
        x + this.tileSize / 2,
        y + this.tileSize / 2,
        this.tileSize,
        this.tileSize,
        tintColor,
        0.2
      )
      .setDepth(0.4);
    this.hoverTints.set(key, tint);
  }

  private onHoverExit(file: number, rank: number): void {
    const key = `${file}_${rank}`;
    const tint = this.hoverTints.get(key);
    tint?.destroy();
    this.hoverTints.delete(key);
  }

  private onSquareClick(file: number, rank: number): void {
    if (this.aiThinking) return;
    const { humanColor } = useGameStore.getState();
    if (this.engine.getTurn() !== humanColor) return;

    const sq = frToSquare(file, rank);

    if (this.selected) {
      const legal = this.engine.getLegalMoves(this.selected);
      const target = legal.find((m) => m.to === sq);
      if (target) {
        this.executeHumanMove(this.selected, sq, target);
        return;
      }
      const board = this.engine.getBoard();
      const cell = board[7 - rank]?.[file];
      if (cell && cell.color === humanColor) {
        this.selectSquare(sq);
        return;
      }
      this.clearSelection();
      return;
    }

    const board = this.engine.getBoard();
    const cell = board[7 - rank]?.[file];
    if (cell && cell.color === humanColor) {
      this.selectSquare(sq);
    }
  }

  private selectSquare(sq: Square): void {
    this.clearSelection();
    this.selected = sq;
    const { file, rank } = squareToFR(sq);
    const { x, y } = this.tileTopLeft(file, rank);
    this.selectedHighlight = this.add
      .rectangle(
        x + this.tileSize / 2,
        y + this.tileSize / 2,
        this.tileSize,
        this.tileSize,
        COLORS.HIGHLIGHT_SELECTED,
        0.35
      )
      .setStrokeStyle(2, COLORS.GOLD_BRIGHT)
      .setDepth(0.5);

    const legal = this.engine.getLegalMoves(sq);
    for (const mv of legal) this.drawLegalMark(mv);

    this.pieces.get(sq)?.container.setDepth(10);
  }

  private drawLegalMark(mv: LegalMove): void {
    const { file, rank } = squareToFR(mv.to);
    const { x, y } = this.tileTopLeft(file, rank);
    const cx = x + this.tileSize / 2;
    const cy = y + this.tileSize / 2;
    const isCapture = mv.captured !== undefined;
    const color = isCapture ? COLORS.HIGHLIGHT_CAPTURE : COLORS.HIGHLIGHT_LEGAL;

    if (isCapture) {
      const ring = this.add.graphics().setDepth(5);
      ring.lineStyle(3, color, 0.9);
      ring.strokeCircle(cx, cy, this.tileSize * 0.44);
      const tween = this.tweens.add({
        targets: ring,
        alpha: { from: 0.55, to: 1 },
        duration: TIMINGS.LEGAL_PULSE_MS,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut',
      });
      this.legalMarks.push({ obj: ring, tween });
    } else {
      const dot = this.add.circle(cx, cy, this.tileSize * 0.17).setStrokeStyle(2.5, color).setDepth(5);
      const tween = this.tweens.add({
        targets: dot,
        alpha: { from: 0.5, to: 1 },
        duration: TIMINGS.LEGAL_PULSE_MS,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut',
      });
      this.legalMarks.push({ obj: dot, tween });
    }
  }

  private clearSelection(): void {
    this.selected = null;
    this.selectedHighlight?.destroy();
    this.selectedHighlight = null;
    this.legalMarks.forEach((m) => {
      m.tween?.stop();
      m.obj.destroy();
    });
    this.legalMarks = [];
    this.pieces.forEach((p) => p.container.setDepth(2));
  }

  // ═══════════════════════════════ Move execution ═══════════════════════════════

  private executeHumanMove(from: Square, to: Square, mv: LegalMove): void {
    this.clearSelection();
    const promo: PieceType = mv.promotion ?? GAME.AUTO_PROMOTION;
    this.applyMoveWithTween(from, to, promo, () => {
      if (this.checkEndAndMaybeShowModal()) return;
      this.queueAiMove();
    });
  }

  private queueAiMove(): void {
    this.aiThinking = true;
    this.time.delayedCall(TIMINGS.AI_RESPONSE_DELAY_MS, async () => {
      try {
        const decision = await this.ai.getMove(this.engine.getFen());
        const promo: PieceType =
          (decision.promotion as PieceType | undefined) ?? GAME.AUTO_PROMOTION;
        this.applyMoveWithTween(
          decision.from as Square,
          decision.to as Square,
          promo,
          () => {
            this.aiThinking = false;
            this.checkEndAndMaybeShowModal();
          }
        );
      } catch (err) {
        console.error('AI move failed', err);
        this.aiThinking = false;
      }
    });
  }

  private applyMoveWithTween(
    from: Square,
    to: Square,
    promotion: PieceType,
    onComplete: () => void
  ): void {
    const pieceView = this.pieces.get(from);
    if (!pieceView) {
      const result = this.engine.makeMove(from, to, promotion);
      if (!result) {
        onComplete();
        return;
      }
      this.renderPieces();
      this.drawLastMoveMarks(from, to);
      onComplete();
      return;
    }

    const victim = this.pieces.get(to);
    const { file: tf, rank: tr } = squareToFR(to);
    const { x, y } = this.tileTopLeft(tf, tr);
    const cx = x + this.tileSize / 2;
    const cy = y + this.tileSize / 2;

    this.tweens.add({
      targets: pieceView.container,
      x: cx,
      y: cy,
      duration: TIMINGS.MOVE_TWEEN_MS,
      ease: 'Linear',
      onComplete: () => {
        victim?.container.destroy();
        this.pieces.delete(to);

        const result = this.engine.makeMove(from, to, promotion);
        if (!result) {
          this.renderPieces();
          onComplete();
          return;
        }
        this.renderPieces();
        this.drawLastMoveMarks(from, to);
        onComplete();
      },
    });
  }

  private drawLastMoveMarks(from: Square, to: Square): void {
    this.lastMoveMarks.forEach((m) => m.destroy());
    this.lastMoveMarks = [];
    for (const sq of [from, to]) {
      const { file, rank } = squareToFR(sq);
      const { x, y } = this.tileTopLeft(file, rank);
      const mark = this.add
        .rectangle(
          x + this.tileSize / 2,
          y + this.tileSize / 2,
          this.tileSize,
          this.tileSize,
          COLORS.HIGHLIGHT_LAST_MOVE,
          0.2
        )
        .setDepth(0.5);
      this.lastMoveMarks.push(mark);
    }
  }

  // ═══════════════════════════════ End game ═══════════════════════════════

  private checkEndAndMaybeShowModal(): boolean {
    const status = this.engine.getStatus();
    if (status === 'ongoing') return false;
    const loserIsToMove = status === 'checkmate';
    const winner: Color | null = loserIsToMove
      ? this.engine.getTurn() === 'w'
        ? 'b'
        : 'w'
      : null;
    const { humanColor } = useGameStore.getState();
    this.time.delayedCall(TIMINGS.END_GAME_MODAL_DELAY_MS, () => {
      this.modal.show({
        status,
        humanColor,
        winner,
        onRestart: () => this.restartGame(),
        onMenu: () => this.returnToMenu(),
      });
    });
    return true;
  }

  private restartGame(): void {
    this.engine.newGame();
    this.clearSelection();
    this.lastMoveMarks.forEach((m) => m.destroy());
    this.lastMoveMarks = [];
    this.renderPieces();
    this.aiThinking = false;
    const { humanColor } = useGameStore.getState();
    if (humanColor !== this.engine.getTurn()) {
      this.queueAiMove();
    }
  }

  private returnToMenu(): void {
    this.unmountBackButton();
    this.scene.start('MenuScene');
  }

  // ═══════════════════════════════ Back button (DOM) ═══════════════════════════════

  private mountBackButton(): void {
    const overlay = document.getElementById('overlay');
    if (!overlay) return;
    const existing = document.getElementById(BACK_BTN_DOM_ID);
    if (existing) existing.remove();

    const btn = document.createElement('button');
    btn.id = BACK_BTN_DOM_ID;
    btn.type = 'button';
    btn.className =
      'pointer-events-auto absolute top-4 left-4 w-11 h-11 rounded-full ' +
      'border-2 border-gold bg-obsidian-deep/80 text-gold font-display text-xl ' +
      'flex items-center justify-center shadow-gold-soft ' +
      'hover:brightness-110 active:brightness-90';
    btn.textContent = '←';
    btn.addEventListener('click', () => this.returnToMenu());
    overlay.appendChild(btn);
  }

  private unmountBackButton(): void {
    document.getElementById(BACK_BTN_DOM_ID)?.remove();
  }

  // ═══════════════════════════════ Helpers ═══════════════════════════════

  private rgbFromInt(n: number): string {
    return `#${n.toString(16).padStart(6, '0')}`;
  }

  private handleResize(): void {
    this.computeLayout();
    this.scene.restart();
  }
}
