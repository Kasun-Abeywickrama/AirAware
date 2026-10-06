import { describe, expect, it } from "vitest";
import { formatDateTime, formatPm25, formatRelativeAge } from "./format";

describe("format helpers", () => {
  it("formats PM2.5 values with up to one decimal place", () => {
    expect(formatPm25(42)).toBe("42");
    expect(formatPm25(42.34)).toBe("42.3");
  });

  it("formats date and time in Asia/Kolkata timezone", () => {
    const formatted = formatDateTime("2026-09-30T10:00:00Z");
    expect(formatted).toContain("Sep");
    expect(formatted).toContain("30");
  });

  it("formats relative age accurately", () => {
    const now = Date.now();
    expect(formatRelativeAge(new Date(now - 30_000).toISOString())).toBe("Updated just now");
    expect(formatRelativeAge(new Date(now - 120_000).toISOString())).toBe("Updated 2 min ago");
    expect(formatRelativeAge(new Date(now - 3_600_000 * 3).toISOString())).toBe("Updated 3h ago");
  });
});
