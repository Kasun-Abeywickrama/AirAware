import { getAqiCategory } from "../../utils/whoAqi";

/**
 * Displays the US EPA Air Quality Index (AQI) category badge for a given PM2.5 value.
 *
 * Two variants:
 *  - "card" : Light background badge for use on white/light surfaces.
 *  - "hero" : High-contrast elevated white pill badge for use inside the teal gradient hero card.
 */
export function WhoAqiBadge({
  pm25,
  variant = "card",
  showGuidance = false,
}: {
  pm25: number;
  variant?: "card" | "hero";
  showGuidance?: boolean;
}) {
  const info = getAqiCategory(pm25);
  const { colors, label, guidance, epaReference } = info;

  if (variant === "hero") {
    return (
      <div
        className="inline-flex flex-col gap-1 rounded-xl bg-white px-4 py-2.5 text-slate-900 shadow-md ring-1 ring-black/5"
        aria-label={`US EPA AQI classification: ${label}`}
      >
        <div className="flex items-center gap-2.5">
          <span className="relative flex size-2.5 shrink-0 items-center justify-center">
            <span
              className={`absolute -inset-0.5 rounded-full ${colors.dot} opacity-75 motion-safe:animate-ping`}
              aria-hidden="true"
            />
            <span className={`relative size-2.5 rounded-full ${colors.dot}`} aria-hidden="true" />
          </span>
          <span className={`text-sm font-bold ${colors.text}`}>{label}</span>
        </div>
        <span className="text-xs font-medium text-slate-500">{epaReference}</span>
      </div>
    );
  }

  return (
    <div aria-label={`US EPA AQI classification: ${label}`}>
      <span
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold ${colors.badge} ${colors.text}`}
      >
        <span className={`size-2 rounded-full ${colors.dot}`} aria-hidden="true" />
        {label}
      </span>
      <p className="mt-1 text-xs text-slate-500">{epaReference}</p>
      {showGuidance && (
        <p className="mt-2 text-sm leading-6 text-slate-600">{guidance}</p>
      )}
    </div>
  );
}

/** Preferred name alias */
export const AqiBadge = WhoAqiBadge;
