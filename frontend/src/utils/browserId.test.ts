import { beforeEach, describe, expect, it } from "vitest";
import { BROWSER_ID_KEY, getBrowserId } from "./browserId";

describe("browserId utility", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("generates and persists a new UUID if none exists in localStorage", () => {
    const id = getBrowserId();
    expect(id).toMatch(/^[0-9a-f-]{36}$/i);
    expect(window.localStorage.getItem(BROWSER_ID_KEY)).toBe(id);
  });

  it("reuses existing browser ID from localStorage", () => {
    window.localStorage.setItem(BROWSER_ID_KEY, "existing-uuid-1234");
    const id = getBrowserId();
    expect(id).toBe("existing-uuid-1234");
  });
});
