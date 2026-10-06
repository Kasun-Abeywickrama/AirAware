import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, X } from "lucide-react";
import type { AlertPreference } from "../../api/types";
import { formatPm25 } from "../../utils/format";
import { calculateAqi, getAqiCategory } from "../../utils/aqi";

export interface ThresholdAlertBannerProps {
  currentPm25: number;
  preference?: AlertPreference | null;
  className?: string;
}

export function ThresholdAlertBanner({
  currentPm25,
  preference,
  className = "",
}: ThresholdAlertBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  // If dismissed, disabled, or not exceeded, do not render
  if (
    dismissed ||
    !preference ||
    !preference.enabled ||
    preference.threshold_ug_m3 === null ||
    currentPm25 <= preference.threshold_ug_m3
  ) {
    return null;
  }

  const threshold = preference.threshold_ug_m3;
  const excess = Math.max(0, Math.round((currentPm25 - threshold) * 10) / 10);
  const aqiCategory = getAqiCategory(currentPm25);
  const aqiScore = calculateAqi(currentPm25);

  const isSevere = currentPm25 >= 125.5; // Unhealthy or worse

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`relative rounded-xl border p-4 shadow-2xs transition-all ${
        isSevere
          ? "border-rose-200/90 bg-rose-50/60 text-slate-900"
          : "border-amber-200/90 bg-amber-50/60 text-slate-900"
      } ${className}`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        {/* Main info block */}
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div
            className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg ${
              isSevere ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"
            }`}
          >
            <AlertTriangle className="size-4" aria-hidden="true" />
          </div>

          <div className="space-y-2">
            {/* 1. Header with Badge & Title */}
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                  isSevere ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                }`}
              >
                Air Quality Alert
              </span>
              <h3 className="text-sm font-semibold text-slate-900">
                Current PM2.5 exceeds your personal alert limit
              </h3>
            </div>

            {/* 2. Structured Metric Chips */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center rounded-md bg-white/90 px-2.5 py-1 font-medium text-slate-700 ring-1 ring-slate-200/80 shadow-2xs">
                Live PM2.5: <strong className="ml-1 font-bold text-slate-950">{formatPm25(currentPm25)} µg/m³</strong>
              </span>

              <span className="inline-flex items-center rounded-md bg-rose-100/70 px-2.5 py-1 font-medium text-rose-900 ring-1 ring-rose-200/80 shadow-2xs">
                <span className="font-bold text-rose-700">+{excess} µg/m³ higher</span>
                <span className="ml-1 text-rose-800">than your {threshold} µg/m³ limit</span>
              </span>

              <span
                className={`inline-flex items-center rounded-md px-2.5 py-1 font-semibold ring-1 shadow-2xs ${aqiCategory.colors.badge} ${aqiCategory.colors.text} ring-black/5`}
              >
                {aqiCategory.label} (AQI {aqiScore})
              </span>
            </div>

            {/* 3. Distinct Health Guidance line */}
            <p className="text-xs text-slate-600 sm:text-[13px]">
              <span className="font-semibold text-slate-700">Health note:</span> {aqiCategory.guidance}
            </p>
          </div>
        </div>

        {/* Actions on the right */}
        <div className="flex shrink-0 items-center gap-3 self-end lg:self-center">
          <Link
            to="/alerts"
            className="inline-flex items-center gap-1 text-xs font-semibold text-teal-800 transition hover:text-teal-950 hover:underline underline-offset-2"
          >
            <span>Adjust Alert Threshold</span>
            <ArrowRight className="size-3" aria-hidden="true" />
          </Link>

          <button
            type="button"
            onClick={() => setDismissed(true)}
            className="rounded-md p-1.5 text-slate-400 transition hover:bg-black/5 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            aria-label="Dismiss alert for now"
            title="Dismiss alert"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
