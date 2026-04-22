export interface AIDecision {
  from: string;
  to: string;
  promotion?: string;
}

/**
 * All AI levels implement this interface.
 * FEN is the only input — AI engines are stateless w.r.t. game history.
 */
export interface AIEngine {
  readonly name: string;
  getMove(fen: string): Promise<AIDecision>;
}
