import { describe, expect, it } from "vitest";
import { getWhoCategory } from "./whoAqi";

describe("getWhoCategory (WHO 2021 PM2.5 Guidelines)", () => {
  it("classifies 0 µg/m³ as Good", () => {
    expect(getWhoCategory(0).category).toBe("good");
  });
  it("classifies 15 µg/m³ as Good (boundary)", () => {
    expect(getWhoCategory(15).category).toBe("good");
  });
  it("classifies 15.1 µg/m³ as Moderate", () => {
    expect(getWhoCategory(15.1).category).toBe("moderate");
  });
  it("classifies 35 µg/m³ as Moderate (boundary)", () => {
    expect(getWhoCategory(35).category).toBe("moderate");
  });
  it("classifies 35.1 µg/m³ as Unhealthy for Sensitive Groups", () => {
    expect(getWhoCategory(35.1).category).toBe("unhealthy_sensitive");
  });
  it("classifies 75 µg/m³ as Unhealthy for Sensitive Groups (boundary)", () => {
    expect(getWhoCategory(75).category).toBe("unhealthy_sensitive");
  });
  it("classifies 75.1 µg/m³ as Unhealthy", () => {
    expect(getWhoCategory(75.1).category).toBe("unhealthy");
  });
  it("classifies 150 µg/m³ as Unhealthy (boundary)", () => {
    expect(getWhoCategory(150).category).toBe("unhealthy");
  });
  it("classifies 150.1 µg/m³ as Hazardous", () => {
    expect(getWhoCategory(150.1).category).toBe("hazardous");
  });
  it("classifies 500 µg/m³ as Hazardous", () => {
    expect(getWhoCategory(500).category).toBe("hazardous");
  });
});
