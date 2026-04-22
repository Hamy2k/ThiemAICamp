import { create } from 'zustand';

export type PlayerColor = 'w' | 'b';
export type AILevel = 'easy' | 'medium' | 'hard';

interface GameStore {
  humanColor: PlayerColor;
  aiLevel: AILevel;
  setHumanColor: (c: PlayerColor) => void;
  setAILevel: (lvl: AILevel) => void;
}

/**
 * Phase 1: minimal state. No persistence yet.
 * Persistence via @capacitor/preferences will be wired in a later phase.
 */
export const useGameStore = create<GameStore>((set) => ({
  humanColor: 'w',
  aiLevel: 'easy',
  setHumanColor: (c) => set({ humanColor: c }),
  setAILevel: (lvl) => set({ aiLevel: lvl }),
}));
