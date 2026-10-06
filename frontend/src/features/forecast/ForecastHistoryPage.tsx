import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, CalendarClock, Database, LineChart } from "lucide-react";
import { api } from "../../api/client";
import { formatDateTime, formatPm25 } from "../../utils/format";
import { AirQualityChart } from "../dashboard/AirQualityChart";
import { LoadingBlock, UnavailablePanel } from "../../components/common/DataState";

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

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <section className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700 sm:text-sm">Forecast history</p>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl lg:text-4xl">See the PM2.5 trend clearly.</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:mt-3 sm:text-base sm:leading-7">
          Compare stored station readings with model forecasts. All timestamps are shown in New Delhi local time.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mt-8 sm:p-6" aria-labelledby="history-controls-heading">
        <div className="flex flex-col gap-3.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <div>
            <h2 id="history-controls-heading" className="text-base font-semibold text-slate-950 sm:text-lg">
              Choose a time range
            </h2>
            <p className="mt-0.5 text-xs text-slate-600 sm:mt-1 sm:text-sm">A longer range gives more context; a shorter range is easier to scan.</p>
          </div>
          <div className="grid grid-cols-3 w-full sm:w-fit sm:flex rounded-lg bg-slate-100 p-1" role="group" aria-label="Forecast history time range">
            {RANGES.map((range) => (
              <button
                key={range}
                type="button"
                className={`rounded-md px-2.5 py-1.5 text-xs font-semibold transition sm:px-3 sm:py-2 sm:text-sm ${
                  hours === range ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
                aria-pressed={hours === range}
                onClick={() => setHours(range)}
              >
                Last {range}h
              </button>
            ))}
          </div>
        </div>

        {history.isLoading ? (
          <div className="mt-6">
            <LoadingBlock label="Loading forecast history" />
          </div>
        ) : history.isError ? (
          <div className="mt-6">
            <UnavailablePanel title="Forecast history is unavailable" message={errorMessage(history.error)} />
          </div>
        ) : (
          history.data && (
            <>
              <div className="mt-5 sm:mt-6 grid gap-2.5 sm:gap-3 sm:grid-cols-3">
                <article className="rounded-xl bg-slate-50 p-3 sm:p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 sm:text-sm">
                    <Database className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                    Latest reading
                  </div>
                  <p className="mt-2 text-xl font-bold text-slate-950 sm:mt-3 sm:text-2xl">
                    {latestObservation ? `${formatPm25(latestObservation.value_ug_m3)} µg/m³` : "—"}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-500 sm:text-xs">
                    {latestObservation ? formatDateTime(latestObservation.observed_at) : "No stored observation"}
                  </p>
                </article>
                <article className="rounded-xl bg-slate-50 p-3 sm:p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 sm:text-sm">
                    <LineChart className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                    Forecast points
                  </div>
                  <p className="mt-2 text-xl font-bold text-slate-950 sm:mt-3 sm:text-2xl">{forecastCount}</p>
                  <p className="mt-1 text-[11px] text-slate-500 sm:text-xs">Saved model estimates in this view</p>
                </article>
                <article className="rounded-xl bg-slate-50 p-3 sm:p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 sm:text-sm">
                    <CalendarClock className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                    Displayed period
                  </div>
                  <p className="mt-2 text-xl font-bold text-slate-950 sm:mt-3 sm:text-2xl">{history.data.hours} hours</p>
                  <p className="mt-1 text-[11px] text-slate-500 sm:text-xs">Stored data available for this range</p>
                </article>
              </div>
              <div className="mt-6 border-t border-slate-100 pt-5 sm:mt-8 sm:pt-6">
                <AirQualityChart history={history.data} expanded frameless />
              </div>
            </>
          )
        )}
      </section>

      <section className="mt-6 grid gap-3.5 sm:gap-4 md:grid-cols-2" aria-label="Chart guide">
        <article className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
          <div className="flex items-center gap-2">
            <span className="size-2.5 sm:size-3 rounded-full bg-teal-700" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-slate-950 sm:text-base">Observed line</h2>
          </div>
          <p className="mt-1.5 text-xs leading-5 text-slate-600 sm:mt-2 sm:text-sm sm:leading-6">Solid teal values are approved PM2.5 readings from the monitoring station.</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
          <div className="flex items-center gap-2">
            <BarChart3 className="size-3.5 text-blue-600 sm:size-4" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-slate-950 sm:text-base">Forecast and range</h2>
          </div>
          <p className="mt-1.5 text-xs leading-5 text-slate-600 sm:mt-2 sm:text-sm sm:leading-6">
            The dashed blue line is the saved forecast. The shaded band shows its lower and upper range.
          </p>
        </article>
      </section>

      <aside className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 text-xs leading-5 text-slate-600 sm:p-5 sm:text-sm sm:leading-6">
        <p className="font-semibold text-slate-800">Important</p>
        <p className="mt-1">Comparative timing guidance only; this is not a safety guarantee or medical advice.</p>
      </aside>
    </main>
  );
}
