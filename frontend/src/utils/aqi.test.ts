import { describe, expect, it } from "vitest";
import { calculateAqi, getAqiCategory, getWhoCategory } from "./aqi";

describe("calculateAqi (US EPA 2024 PM2.5 Linear Interpolation)", () => {
  it("calculates AQI 0 for 0 µg/m³", () => {
    expect(calculateAqi(0)).toBe(0);
  });

  it("calculates AQI 50 for 9.0 µg/m³ (Good upper bound)", () => {
    expect(calculateAqi(9.0)).toBe(50);
  });

  it("calculates AQI 51 for 9.1 µg/m³ (Moderate lower bound)", () => {
    expect(calculateAqi(9.1)).toBe(51);
  });

  it("calculates AQI 90 for 30.0 µg/m³ (Moderate example)", () => {
    expect(calculateAqi(30.0)).toBe(90);
  });

  it("calculates AQI 100 for 35.4 µg/m³ (Moderate upper bound)", () => {
    expect(calculateAqi(35.4)).toBe(100);
  });

  it("calculates AQI 101 for 35.5 µg/m³ (Sensitive lower bound)", () => {
    expect(calculateAqi(35.5)).toBe(101);
  });

  it("calculates AQI 150 for 55.4 µg/m³ (Sensitive upper bound)", () => {
    expect(calculateAqi(55.4)).toBe(150);
  });

  it("calculates AQI 151 for 55.5 µg/m³ (Unhealthy lower bound)", () => {
    expect(calculateAqi(55.5)).toBe(151);
  });

  it("calculates AQI 200 for 125.4 µg/m³ (Unhealthy upper bound)", () => {
    expect(calculateAqi(125.4)).toBe(200);
  });

  it("calculates AQI 201 for 125.5 µg/m³ (Very Unhealthy lower bound)", () => {
    expect(calculateAqi(125.5)).toBe(201);
  });

  it("calculates AQI 300 for 225.4 µg/m³ (Very Unhealthy upper bound)", () => {
    expect(calculateAqi(225.4)).toBe(300);
  });

  it("calculates AQI 301 for 225.5 µg/m³ (Hazardous lower bound)", () => {
    expect(calculateAqi(225.5)).toBe(301);
  });

  it("calculates AQI 400 for 325.4 µg/m³ (Hazardous Tier 1 upper bound)", () => {
    expect(calculateAqi(325.4)).toBe(400);
  });

  it("calculates AQI 500 for 500.4 µg/m³", () => {
    expect(calculateAqi(500.4)).toBe(500);
  });

  it("caps at 500 for extreme values above 500.4 µg/m³", () => {
    expect(calculateAqi(600)).toBe(500);
    expect(calculateAqi(1000)).toBe(500);
  });

  it("handles negative values safely", () => {
    expect(calculateAqi(-5)).toBe(0);
  });
});

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
