import { getWhoCategory } from "../../utils/whoAqi";

/**
 * Displays the WHO 2021 Air Quality category badge for a given PM2.5 value.
 *
 * Two variants:
 *  - "card"  : Light background badge for use on white/light surfaces.
 *  - "hero"  : Semi-transparent badge for use inside the teal gradient hero card.
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
  const info = getWhoCategory(pm25);
  const { colors, label, guidance, whoReference } = info;

  if (variant === "hero") {
    return (
      <div
        className={`inline-flex flex-col gap-1 rounded-xl px-3 py-2 ring-1 ${colors.heroBadge}`}
        aria-label={`WHO air quality classification: ${label}`}
      >
        <span className="flex items-center gap-2">
          <span className={`size-2 rounded-full ${colors.dot}`} aria-hidden="true" />
          <span className={`text-sm font-semibold ${colors.heroText}`}>{label}</span>
        </span>
        <span className="text-xs text-white/70">{whoReference}</span>
      </div>
    );
  }

  return (
    <div aria-label={`WHO air quality classification: ${label}`}>
      <span
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold ${colors.badge} ${colors.text}`}
      >
        <span className={`size-2 rounded-full ${colors.dot}`} aria-hidden="true" />
        {label}
      </span>
      <p className="mt-1 text-xs text-slate-500">{whoReference}</p>
      {showGuidance && (
        <p className="mt-2 text-sm leading-6 text-slate-600">{guidance}</p>
      )}
    </div>
  );
}
