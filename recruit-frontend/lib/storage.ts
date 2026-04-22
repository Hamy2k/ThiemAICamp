/**
 * localStorage wrapper for save-and-resume on screening chat.
 *
 * Rationale: Phase 1 API has no GET /screening/:id to restore state.
 * We cache minimal conversation state locally. Backend is source of truth
 * for scoring; losing local cache only loses UI continuity.
 */

export interface StoredMessage {
  role: "assistant" | "user";
  content: string;
}

export interface StoredScreeningState {
  lead_id: string;
  session_id: string;
  messages: StoredMessage[];
  turn_count: number;
  done: boolean;
  updated_at: number;
}

const PREFIX = "rl.screening.";
const TTL_MS = 48 * 60 * 60 * 1000; // 48h

function safeWindow(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function saveScreening(state: StoredScreeningState): void {
  const ls = safeWindow();
  if (!ls) return;
  try {
    ls.setItem(PREFIX + state.lead_id, JSON.stringify(state));
  } catch {
    // quota exceeded — drop silently
  }
}

export function loadScreening(lead_id: string): StoredScreeningState | null {
  const ls = safeWindow();
  if (!ls) return null;
  try {
    const raw = ls.getItem(PREFIX + lead_id);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredScreeningState;
    if (Date.now() - parsed.updated_at > TTL_MS) {
      ls.removeItem(PREFIX + lead_id);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function clearScreening(lead_id: string): void {
  const ls = safeWindow();
  if (!ls) return;
  try {
    ls.removeItem(PREFIX + lead_id);
  } catch {
    // noop
  }
}
