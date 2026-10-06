/**
 * US EPA Air Quality Index (AQI) Standard – PM2.5 Concentration Breakpoints (2024 Revision).
 *
 * Source: U.S. EPA Air Quality Index Fact Sheet & NAAQS Standards
 * Effective: May 6, 2024
 * Reference: https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf
 * Technical Assistance Document: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
 *
 * Breakpoints:
 *   Good                           : 0.0 – 9.0   µg/m³  (AQI   0 – 50)   [Green]
 *   Moderate                       : 9.1 – 35.4  µg/m³  (AQI  51 – 100)  [Yellow]
 *   Unhealthy for Sensitive Groups : 35.5 – 55.4 µg/m³  (AQI 101 – 150)  [Orange]
 *   Unhealthy                      : 55.5 – 125.4 µg/m³ (AQI 151 – 200)  [Red]
 *   Very Unhealthy                 : 125.5 – 225.4 µg/m³(AQI 201 – 300)  [Purple]
 *   Hazardous (Tier 1)             : 225.5 – 325.4 µg/m³(AQI 301 – 400)  [Maroon]
 *   Hazardous (Tier 2)             : 325.5 – 500.4 µg/m³(AQI 401 – 500)  [Maroon]
 */

export type AqiCategory =
  | "good"
  | "moderate"
  | "unhealthy_sensitive"
  | "unhealthy"
  | "very_unhealthy"
  | "hazardous";

/** Backward-compatible alias */
export type WhoCategory = AqiCategory;

export interface AqiCategoryInfo {
  category: AqiCategory;
  /** Category display name */
  label: string;
  /** Short label for compact displays */
  shortLabel: string;
  /** AQI number range */
  aqiRange: string;
  /** PM2.5 concentration range */
  concentrationRange: string;
  /** One-line health guidance */
  guidance: string;
  /** Official EPA reference string */
  epaReference: string;
  /** Backward-compatible reference field */
  whoReference: string;
  /** Tailwind colour tokens for the badge */
  colors: {
    badge: string;
    text: string;
    dot: string;
    heroBadge: string;
    heroText: string;
  };
}

/** Backward-compatible alias */
export type WhoCategoryInfo = AqiCategoryInfo;

interface BreakpointBand {
  category: AqiCategory;
  cLow: number;
  cHigh: number;
  iLow: number;
  iHigh: number;
}

const BREAKPOINT_BANDS: BreakpointBand[] = [
  { category: "good", cLow: 0.0, cHigh: 9.0, iLow: 0, iHigh: 50 },
  { category: "moderate", cLow: 9.1, cHigh: 35.4, iLow: 51, iHigh: 100 },
  { category: "unhealthy_sensitive", cLow: 35.5, cHigh: 55.4, iLow: 101, iHigh: 150 },
  { category: "unhealthy", cLow: 55.5, cHigh: 125.4, iLow: 151, iHigh: 200 },
  { category: "very_unhealthy", cLow: 125.5, cHigh: 225.4, iLow: 201, iHigh: 300 },
  { category: "hazardous", cLow: 225.5, cHigh: 325.4, iLow: 301, iHigh: 400 },
  { category: "hazardous", cLow: 325.5, cHigh: 500.4, iLow: 401, iHigh: 500 },
];

export const CATEGORIES: Record<AqiCategory, AqiCategoryInfo> = {
  good: {
    category: "good",
    label: "Good",
    shortLabel: "Good",
    aqiRange: "0–50",
    concentrationRange: "0.0–9.0 µg/m³",
    guidance: "Air quality is satisfactory and poses little or no risk.",
    epaReference: "EPA AQI 0–50 (0.0–9.0 µg/m³)",
    whoReference: "EPA AQI 0–50 (0.0–9.0 µg/m³)",
    colors: {
      badge: "bg-emerald-100",
      text: "text-emerald-800",
      dot: "bg-emerald-500",
      heroBadge: "bg-emerald-400/20 ring-emerald-300/40",
      heroText: "text-emerald-100",
    },
  },
  moderate: {
    category: "moderate",
    label: "Moderate",
    shortLabel: "Moderate",
    aqiRange: "51–100",
    concentrationRange: "9.1–35.4 µg/m³",
    guidance: "Acceptable air quality. Sensitive individuals should consider limiting prolonged outdoor exertion.",
    epaReference: "EPA AQI 51–100 (9.1–35.4 µg/m³)",
    whoReference: "EPA AQI 51–100 (9.1–35.4 µg/m³)",
    colors: {
      badge: "bg-yellow-100",
      text: "text-yellow-800",
      dot: "bg-yellow-500",
      heroBadge: "bg-yellow-400/20 ring-yellow-300/40",
      heroText: "text-yellow-100",
    },
  },
  unhealthy_sensitive: {
    category: "unhealthy_sensitive",
    label: "Unhealthy for Sensitive Groups",
    shortLabel: "Sensitive",
    aqiRange: "101–150",
    concentrationRange: "35.5–55.4 µg/m³",
    guidance: "Members of sensitive groups may experience health effects. General public is less likely to be affected.",
    epaReference: "EPA AQI 101–150 (35.5–55.4 µg/m³)",
    whoReference: "EPA AQI 101–150 (35.5–55.4 µg/m³)",
    colors: {
      badge: "bg-orange-100",
      text: "text-orange-800",
      dot: "bg-orange-500",
      heroBadge: "bg-orange-400/20 ring-orange-300/40",
      heroText: "text-orange-100",
    },
  },
  unhealthy: {
    category: "unhealthy",
    label: "Unhealthy",
    shortLabel: "Unhealthy",
    aqiRange: "151–200",
    concentrationRange: "55.5–125.4 µg/m³",
    guidance: "Everyone may begin to experience health effects. Sensitive groups may experience more serious effects.",
    epaReference: "EPA AQI 151–200 (55.5–125.4 µg/m³)",
    whoReference: "EPA AQI 151–200 (55.5–125.4 µg/m³)",
    colors: {
      badge: "bg-red-100",
      text: "text-red-800",
      dot: "bg-red-500",
      heroBadge: "bg-red-400/20 ring-red-300/40",
      heroText: "text-red-100",
    },
  },
  very_unhealthy: {
    category: "very_unhealthy",
    label: "Very Unhealthy",
    shortLabel: "Very Unhealthy",
    aqiRange: "201–300",
    concentrationRange: "125.5–225.4 µg/m³",
    guidance: "Health alert: The risk of health effects is increased for everyone.",
    epaReference: "EPA AQI 201–300 (125.5–225.4 µg/m³)",
    whoReference: "EPA AQI 201–300 (125.5–225.4 µg/m³)",
    colors: {
      badge: "bg-purple-100",
      text: "text-purple-900",
      dot: "bg-purple-600",
      heroBadge: "bg-purple-400/20 ring-purple-300/40",
      heroText: "text-purple-100",
    },
  },
  hazardous: {
    category: "hazardous",
    label: "Hazardous",
    shortLabel: "Hazardous",
    aqiRange: "301–500+",
    concentrationRange: "≥ 225.5 µg/m³",
    guidance: "Health warning of emergency conditions: Everyone is more likely to be affected.",
    epaReference: "EPA AQI 301–500+ (≥ 225.5 µg/m³)",
    whoReference: "EPA AQI 301–500+ (≥ 225.5 µg/m³)",
    colors: {
      badge: "bg-rose-950/15",
      text: "text-rose-950",
      dot: "bg-rose-950",
      heroBadge: "bg-rose-900/30 ring-rose-400/40",
      heroText: "text-rose-100",
    },
  },
};

/**
 * Standard EPA AQI scale ordered list for legends and scale displays.
 */
export const EPA_AQI_SCALE = [
  {
    category: "good" as const,
    label: CATEGORIES.good.label,
    shortLabel: CATEGORIES.good.shortLabel,
    range: "0–9.0",
    colors: CATEGORIES.good.colors,
  },
  {
    category: "moderate" as const,
    label: CATEGORIES.moderate.label,
    shortLabel: CATEGORIES.moderate.shortLabel,
    range: "9.1–35.4",
    colors: CATEGORIES.moderate.colors,
  },
  {
    category: "unhealthy_sensitive" as const,
    label: CATEGORIES.unhealthy_sensitive.label,
    shortLabel: CATEGORIES.unhealthy_sensitive.shortLabel,
    range: "35.5–55.4",
    colors: CATEGORIES.unhealthy_sensitive.colors,
  },
  {
    category: "unhealthy" as const,
    label: CATEGORIES.unhealthy.label,
    shortLabel: CATEGORIES.unhealthy.shortLabel,
    range: "55.5–125.4",
    colors: CATEGORIES.unhealthy_sensitive.colors,
  },
  {
    category: "very_unhealthy" as const,
    label: CATEGORIES.very_unhealthy.label,
    shortLabel: CATEGORIES.very_unhealthy.shortLabel,
    range: "125.5–225.4",
    colors: CATEGORIES.very_unhealthy.colors,
  },
  {
    category: "hazardous" as const,
    label: CATEGORIES.hazardous.label,
    shortLabel: CATEGORIES.hazardous.shortLabel,
    range: "≥ 225.5",
    colors: CATEGORIES.hazardous.colors,
  },
];

/**
 * Calculates the exact numerical US EPA Air Quality Index (AQI) value
 * using the official linear interpolation formula:
 *
 *   I = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low
 *
 * Rules:
 *  - PM2.5 concentration C is truncated to 1 decimal place before interpolation.
 *  - The resulting index I is rounded to the nearest integer.
 *  - Values above 500.4 µg/m³ are capped at 500 (Beyond the AQI scale).
 */
export function calculateAqi(pm25: number): number {
  if (pm25 <= 0) return 0;

  // EPA Rule: Truncate PM2.5 to 1 decimal place
  const c = Math.floor(pm25 * 10) / 10;

  // Beyond the AQI (values above 500.4 µg/m³)
  if (c >= 500.4) {
    return 500;
  }

  // Find the corresponding breakpoint band
  const band = BREAKPOINT_BANDS.find((b) => c <= b.cHigh) ?? BREAKPOINT_BANDS[BREAKPOINT_BANDS.length - 1];

  const slope = (band.iHigh - band.iLow) / (band.cHigh - band.cLow);
  const aqi = slope * (c - band.cLow) + band.iLow;

  return Math.min(500, Math.max(0, Math.round(aqi)));
}

/**
 * Returns the US EPA AQI category info for a given PM2.5 value in µg/m³.
 * Uses the updated 2024 EPA NAAQS standard breakpoints.
 */
export function getAqiCategory(pm25: number): AqiCategoryInfo {
  const value = Math.max(0, pm25);
  if (value <= 9.0) return CATEGORIES.good;
  if (value <= 35.4) return CATEGORIES.moderate;
  if (value <= 55.4) return CATEGORIES.unhealthy_sensitive;
  if (value <= 125.4) return CATEGORIES.unhealthy;
  if (value <= 225.4) return CATEGORIES.very_unhealthy;
  return CATEGORIES.hazardous;
}

/** Backward-compatible function alias */
export const getWhoCategory = getAqiCategory;
