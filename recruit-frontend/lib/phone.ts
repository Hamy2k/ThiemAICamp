/**
 * Client-side phone normalization — mirrors backend app/utils/phone.py behavior
 * closely enough for inline UX. Final source of truth remains the server.
 *
 * Accepts: 0909…, +8490…, 84 909…, (+84) 909.123.456
 */

const DIGITS_ONLY = /[^\d+]/g;

export function stripToRaw(input: string): string {
  return input.trim().replace(DIGITS_ONLY, "");
}

/**
 * Best-effort conversion to E.164 for Vietnam.
 * Returns null if it can't confidently normalize (caller shows inline hint).
 */
export function normalizeVNPhone(input: string): string | null {
  if (!input) return null;
  let s = stripToRaw(input);

  // Leading "+" forms
  if (s.startsWith("+84") && s.length === 12) return s;
  // "84..." without plus
  if (s.startsWith("84") && s.length === 11) return "+" + s;
  // "0..." local
  if (s.startsWith("0") && s.length === 10) return "+84" + s.slice(1);
  return null;
}

export function isLikelyValidVNPhone(input: string): boolean {
  return normalizeVNPhone(input) !== null;
}
