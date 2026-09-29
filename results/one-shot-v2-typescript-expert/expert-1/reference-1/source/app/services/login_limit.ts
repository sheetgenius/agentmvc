export type FailureWindow = { count: number; until: number }

export function pruneExpiredFailures(entries: Map<string, FailureWindow>, now: number) {
  for (const [email, window] of entries) if (window.until <= now) entries.delete(email)
}
