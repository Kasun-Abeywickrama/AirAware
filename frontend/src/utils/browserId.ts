export const BROWSER_ID_KEY = "airaware-browser-id";

/**
 * Returns a stable anonymous UUID stored in browser localStorage.
 * Generates a new random UUID if one does not exist yet.
 */
export function getBrowserId(): string {
  try {
    const savedId = window.localStorage.getItem(BROWSER_ID_KEY);
    if (savedId) return savedId;
    const id = crypto.randomUUID();
    window.localStorage.setItem(BROWSER_ID_KEY, id);
    return id;
  } catch {
    return "00000000-0000-0000-0000-000000000000";
  }
}

/** Backward-compatible alias */
export const anonymousBrowserId = getBrowserId;
