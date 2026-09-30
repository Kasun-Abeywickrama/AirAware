/**
 * WHO Air Quality Guidelines (2021) – PM2.5 24-hour mean breakpoints.
 *
 * Source: WHO Global Air Quality Guidelines, 2021
 * https://www.who.int/publications/i/item/9789240034228
 *
 * Breakpoints:
 *   AQG Level    : ≤ 15  µg/m³  (WHO 24-h guideline)
 *   Interim T-1  : 15–35  µg/m³
 *   Interim T-2  : 35–75  µg/m³
 *   Interim T-3  : 75–150 µg/m³
 *   Hazardous    : > 150  µg/m³
 */
export type WhoCategory =
  | "good"
  | "moderate"
  | "unhealthy_sensitive"
  | "unhealthy"
  | "hazardous";

export interface WhoCategoryInfo {
  category: WhoCategory;
  /** Short label suitable for a badge */
  label: string;
  /** One-line health guidance */
  guidance: string;
  /** WHO Interim Target or AQG reference label */
  whoReference: string;
  /** Tailwind colour tokens for the badge */
  colors: {
    badge: string;
    text: string;
    dot: string;
    /** For use inside the teal hero card (white-tinted palette) */
    heroBadge: string;
    heroText: string;
  };
}

const CATEGORIES: Record<WhoCategory, WhoCategoryInfo> = {
  good: {
    category: "good",
    label: "Good",
    guidance: "Air quality meets WHO guidelines. Ideal for outdoor activities.",
    whoReference: "WHO AQG (≤ 15 µg/m³)",
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
    guidance: "Acceptable air quality. Sensitive individuals should limit prolonged exertion.",
    whoReference: "WHO Interim T-1 (15–35 µg/m³)",
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
    guidance: "People with respiratory or heart conditions, children, and older adults should reduce prolonged outdoor exertion.",
    whoReference: "WHO Interim T-2 (35–75 µg/m³)",
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
    guidance: "Everyone may begin to experience health effects. Limit outdoor activity and wear protection if necessary.",
    whoReference: "WHO Interim T-3 (75–150 µg/m³)",
    colors: {
      badge: "bg-red-100",
      text: "text-red-800",
      dot: "bg-red-500",
      heroBadge: "bg-red-400/20 ring-red-300/40",
      heroText: "text-red-100",
    },
  },
  hazardous: {
    category: "hazardous",
    label: "Hazardous",
    guidance: "Serious health effects for everyone. Avoid all outdoor activity where possible.",
    whoReference: "Exceeds all WHO interim targets (> 150 µg/m³)",
    colors: {
      badge: "bg-purple-100",
      text: "text-purple-900",
      dot: "bg-purple-700",
      heroBadge: "bg-purple-400/20 ring-purple-300/40",
      heroText: "text-purple-100",
    },
  },
};

/** Returns the WHO category for a given PM2.5 value in µg/m³. */
export function getWhoCategory(pm25: number): WhoCategoryInfo {
  if (pm25 <= 15) return CATEGORIES.good;
  if (pm25 <= 35) return CATEGORIES.moderate;
  if (pm25 <= 75) return CATEGORIES.unhealthy_sensitive;
  if (pm25 <= 150) return CATEGORIES.unhealthy;
  return CATEGORIES.hazardous;
}
