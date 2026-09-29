import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, CalendarClock, Database, LineChart } from "lucide-react";
import { api } from "../api/client";
import { formatDateTime, formatPm25 } from "../lib/format";
import { AirQualityChart } from "./AirQualityChart";
import { LoadingBlock, UnavailablePanel } from "./DataState";

const RANGES = [24, 72, 168] as const;

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Forecast history is temporarily unavailable.";
}

export function ForecastHistoryPage() {
  const [hours, setHours] = useState<(typeof RANGES)[number]>(72);
  const history = useQuery({
    queryKey: ["history", hours],
    queryFn: () => api.forecastHistory(hours),
    refetchInterval: 5 * 60_000,
    staleTime: 5 * 60_000,
  });
  const latestObservation = history.data?.observations.at(-1);
  const forecastCount = history.data?.forecasts.length ?? 0;

  return <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
    <section className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Forecast history</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">See the PM2.5 trend clearly.</h1>
      <p className="mt-3 text-base leading-7 text-slate-600">Compare stored station readings with model forecasts. All timestamps are shown in New Delhi local time.</p>
    </section>

    <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="history-controls-heading">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><h2 id="history-controls-heading" className="font-semibold text-slate-950">Choose a time range</h2><p className="mt-1 text-sm text-slate-600">A longer range gives more context; a shorter range is easier to scan.</p></div>
        <div className="inline-flex w-fit rounded-lg bg-slate-100 p-1" role="group" aria-label="Forecast history time range">
          {RANGES.map((range) => <button key={range} type="button" className={`rounded-md px-3 py-2 text-sm font-semibold transition ${hours === range ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"}`} aria-pressed={hours === range} onClick={() => setHours(range)}>Last {range}h</button>)}
        </div>
      </div>

      {history.isLoading ? <div className="mt-6"><LoadingBlock label="Loading forecast history" /></div> : history.isError ? <div className="mt-6"><UnavailablePanel title="Forecast history is unavailable" message={errorMessage(history.error)} /></div> : history.data && <>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <article className="rounded-xl bg-slate-50 p-4"><div className="flex items-center gap-2 text-sm font-medium text-slate-600"><Database className="size-4 text-teal-700" aria-hidden="true" />Latest reading</div><p className="mt-3 text-2xl font-bold text-slate-950">{latestObservation ? `${formatPm25(latestObservation.value_ug_m3)} µg/m³` : "—"}</p><p className="mt-1 text-xs text-slate-500">{latestObservation ? formatDateTime(latestObservation.observed_at) : "No stored observation"}</p></article>
          <article className="rounded-xl bg-slate-50 p-4"><div className="flex items-center gap-2 text-sm font-medium text-slate-600"><LineChart className="size-4 text-teal-700" aria-hidden="true" />Forecast points</div><p className="mt-3 text-2xl font-bold text-slate-950">{forecastCount}</p><p className="mt-1 text-xs text-slate-500">Saved model estimates in this view</p></article>
          <article className="rounded-xl bg-slate-50 p-4"><div className="flex items-center gap-2 text-sm font-medium text-slate-600"><CalendarClock className="size-4 text-teal-700" aria-hidden="true" />Displayed period</div><p className="mt-3 text-2xl font-bold text-slate-950">{history.data.hours} hours</p><p className="mt-1 text-xs text-slate-500">Stored data available for this range</p></article>
        </div>
        <div className="mt-6"><AirQualityChart history={history.data} expanded /></div>
      </>}
    </section>

    <section className="mt-6 grid gap-4 md:grid-cols-2" aria-label="Chart guide">
      <article className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><span className="size-3 rounded-full bg-teal-700" aria-hidden="true" /><h2 className="font-semibold text-slate-950">Observed line</h2></div><p className="mt-2 text-sm leading-6 text-slate-600">Solid teal values are approved PM2.5 readings from the monitoring station.</p></article>
      <article className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><BarChart3 className="size-4 text-blue-600" aria-hidden="true" /><h2 className="font-semibold text-slate-950">Forecast and range</h2></div><p className="mt-2 text-sm leading-6 text-slate-600">The dashed blue line is the saved forecast. The shaded band shows its lower and upper range.</p></article>
    </section>

    <aside className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-600"><p className="font-semibold text-slate-800">Important</p><p className="mt-1">Comparative timing guidance only; this is not a safety guarantee or medical advice.</p></aside>
  </main>;
}
