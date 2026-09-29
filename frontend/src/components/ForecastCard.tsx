import { ChevronDown, ChevronUp, Clock3 } from "lucide-react";
import { useState } from "react";
import type { ForecastExplanationFactor, ForecastItem } from "../api/types";
import { formatDateTime, formatPm25 } from "../lib/format";

export function ForecastCard({ forecast }: { forecast: ForecastItem }) {
  const [showAllFactors, setShowAllFactors] = useState(false);
  const factors = forecast.explanation?.factors ?? [];
  const topFactors = factors.filter((factor) => factor.is_top_3);
  const remainingFactors = factors.filter((factor) => !factor.is_top_3);
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-900">In {forecast.horizon_hours} {forecast.horizon_hours === 1 ? "hour" : "hours"}</h3>
        <Clock3 className="size-4 text-teal-700" aria-hidden="true" />
      </div>
      <p className="mt-5 text-3xl font-bold tracking-tight text-slate-950">{formatPm25(forecast.predicted_value_ug_m3)} <span className="text-base font-medium text-slate-500">µg/m³</span></p>
      <p className="mt-2 text-sm text-slate-600">Target: {formatDateTime(forecast.target_at)}</p>
      <p className="mt-4 border-t border-slate-100 pt-3 text-xs font-medium text-slate-600">Forecast range: {formatPm25(forecast.lower_bound_ug_m3)}–{formatPm25(forecast.upper_bound_ug_m3)} µg/m³</p>
      {forecast.explanation && topFactors.length > 0 && <section className="mt-5 border-t border-slate-100 pt-4" aria-label={`Why the ${forecast.horizon_hours}-hour forecast looks this way`}>
        <h4 className="text-sm font-semibold text-slate-900">What influenced this forecast</h4>
        <p className="mt-1 text-xs leading-5 text-slate-600">The three strongest patterns in this forecast.</p>
        <ul className="mt-3 space-y-2">
          {topFactors.map((factor) => <FactorRow key={factor.key} factor={factor} />)}
        </ul>
        <button
          type="button"
          className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-teal-700 hover:text-teal-900 focus:outline-none focus:ring-2 focus:ring-teal-700 focus:ring-offset-2"
          aria-expanded={showAllFactors}
          onClick={() => setShowAllFactors((visible) => !visible)}
        >
          {showAllFactors ? "Show less" : "See all factors"}
          {showAllFactors ? <ChevronUp className="size-4" aria-hidden="true" /> : <ChevronDown className="size-4" aria-hidden="true" />}
        </button>
        {showAllFactors && <div className="mt-3 border-t border-slate-100 pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Other factors</p>
          <ul className="mt-2 space-y-2">{remainingFactors.map((factor) => <FactorRow key={factor.key} factor={factor} />)}</ul>
          <p className="mt-4 text-xs leading-5 text-slate-500">{forecast.explanation.notice}</p>
        </div>}
      </section>}
    </article>
  );
}

function FactorRow({ factor }: { factor: ForecastExplanationFactor }) {
  if (!factor.used_by_model) {
    return <li className="flex items-center justify-between gap-3 text-xs text-slate-500"><span>{factor.label}</span><span className="shrink-0">Not used by this model</span></li>;
  }
  const amount = formatPm25(Math.abs(factor.contribution_ug_m3));
  const description = factor.direction === "increased"
    ? `Raised forecast by ${amount} µg/m³`
    : factor.direction === "decreased"
      ? `Lowered forecast by ${amount} µg/m³`
      : "No meaningful change";
  return <li className="flex items-start justify-between gap-3 text-xs leading-5"><span className="font-medium text-slate-700">{factor.label}</span><span className={factor.direction === "increased" ? "shrink-0 text-right font-medium text-amber-700" : factor.direction === "decreased" ? "shrink-0 text-right font-medium text-teal-700" : "shrink-0 text-right text-slate-500"}>{description}</span></li>;
}
