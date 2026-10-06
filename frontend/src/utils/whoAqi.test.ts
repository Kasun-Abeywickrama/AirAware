import { describe, expect, it } from "vitest";
import { getAqiCategory, getWhoCategory } from "./whoAqi";

describe("getAqiCategory (US EPA AQI 2024 PM2.5 Standards)", () => {
  it("classifies 0 µg/m³ as Good", () => {
    expect(getAqiCategory(0).category).toBe("good");
  });
  it("classifies 9.0 µg/m³ as Good (boundary)", () => {
    expect(getAqiCategory(9.0).category).toBe("good");
  });
  it("classifies 9.1 µg/m³ as Moderate", () => {
    expect(getAqiCategory(9.1).category).toBe("moderate");
  });
  it("classifies 35.4 µg/m³ as Moderate (boundary)", () => {
    expect(getAqiCategory(35.4).category).toBe("moderate");
  });
  it("classifies 35.5 µg/m³ as Unhealthy for Sensitive Groups", () => {
    expect(getAqiCategory(35.5).category).toBe("unhealthy_sensitive");
  });
  it("classifies 55.4 µg/m³ as Unhealthy for Sensitive Groups (boundary)", () => {
    expect(getAqiCategory(55.4).category).toBe("unhealthy_sensitive");
  });
  it("classifies 55.5 µg/m³ as Unhealthy", () => {
    expect(getAqiCategory(55.5).category).toBe("unhealthy");
  });
  it("classifies 125.4 µg/m³ as Unhealthy (boundary)", () => {
    expect(getAqiCategory(125.4).category).toBe("unhealthy");
  });
  it("classifies 125.5 µg/m³ as Very Unhealthy", () => {
    expect(getAqiCategory(125.5).category).toBe("very_unhealthy");
  });
  it("classifies 225.4 µg/m³ as Very Unhealthy (boundary)", () => {
    expect(getAqiCategory(225.4).category).toBe("very_unhealthy");
  });
  it("classifies 225.5 µg/m³ as Hazardous", () => {
    expect(getAqiCategory(225.5).category).toBe("hazardous");
  });
  it("classifies 500 µg/m³ as Hazardous", () => {
    expect(getAqiCategory(500).category).toBe("hazardous");
  });
  it("supports getWhoCategory alias identically", () => {
    expect(getWhoCategory(48.4).category).toBe("unhealthy_sensitive");
  });
});
