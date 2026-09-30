import { lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, CloudSun } from "lucide-react";
import { api } from "../../api/client";
import { ActivityPlanner } from "./ActivityPlanner";
import { LoadingBlock, UnavailablePanel } from "../../components/common/DataState";
import { WhoAqiBadge } from "../../components/common/WhoAqiBadge";
import { ForecastCard } from "../forecast/ForecastCard";
import { AppHeader } from "../../components/layout/AppHeader";
import { formatDateTime, formatPm25, formatRelativeAge } from "../../utils/format";
import { type WhoCategory, type WhoCategoryInfo, getWhoCategory } from "../../utils/whoAqi";

const FIVE_MINUTES = 5 * 60_000;
const ONE_MINUTE = 60_000;
const AirQualityChart = lazy(() =>
  import("./AirQualityChart").then((module) => ({ default: module.AirQualityChart })),
);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

const WHO_SCALE: Array<{ category: WhoCategory; label: string; range: string; colors: WhoCategoryInfo["colors"] }> = [
  { category: "good",                label: "Good",                          range: "0–15",   colors: { badge: "bg-emerald-100", text: "text-emerald-800", dot: "bg-emerald-500", heroBadge: "", heroText: "" } },
  { category: "moderate",            label: "Moderate",                      range: "15–35",  colors: { badge: "bg-yellow-100",  text: "text-yellow-800",  dot: "bg-yellow-500",  heroBadge: "", heroText: "" } },
  { category: "unhealthy_sensitive", label: "Unhealthy for Sensitive Groups", range: "35–75",  colors: { badge: "bg-orange-100", text: "text-orange-800", dot: "bg-orange-500", heroBadge: "", heroText: "" } },
  { category: "unhealthy",           label: "Unhealthy",                      range: "75–150", colors: { badge: "bg-red-100",    text: "text-red-800",    dot: "bg-red-500",    heroBadge: "", heroText: "" } },
  { category: "hazardous",           label: "Hazardous",                      range: ">150",   colors: { badge: "bg-purple-100", text: "text-purple-900", dot: "bg-purple-700", heroBadge: "", heroText: "" } },
];

function WhoScaleLegend({ currentPm25 }: { currentPm25: number }) {
  const active = getWhoCategory(currentPm25);
  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">WHO 2021 PM2.5 Scale</p>
      <ol className="mt-3 flex flex-col gap-2 sm:flex-row sm:gap-0" aria-label="WHO PM2.5 air quality scale">
        {WHO_SCALE.map(({ category, label, range, colors }) => {
          const isCurrent = active.category === category;
          return (
            <li
              key={category}
              className={`flex flex-1 items-center gap-2 rounded-lg px-3 py-2 transition sm:flex-col sm:items-start sm:rounded-none sm:first:rounded-l-lg sm:last:rounded-r-lg ${
                isCurrent ? `${colors.badge} ring-2 ring-inset ring-slate-400/30` : "bg-slate-50"
              }`}
              aria-current={isCurrent ? "true" : undefined}
            >
              <span className={`size-2.5 shrink-0 rounded-full ${colors.dot}`} aria-hidden="true" />
              <span className="min-w-0">
                <span className={`block text-xs font-semibold ${isCurrent ? colors.text : "text-slate-700"}`}>
                  {label}
                  {isCurrent && <span className="ml-1.5 text-[10px] font-bold uppercase tracking-wide opacity-70">◄ now</span>}
                </span>
                <span className="block text-[11px] text-slate-500">{range} µg/m³</span>
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-3 text-[11px] text-slate-400">
        Based on <a href="https://www.who.int/publications/i/item/9789240034228" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-600">WHO Air Quality Guidelines 2021</a> 24-hour mean breakpoints.
      </p>
    </div>
  );
}


export function DashboardPage() {
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: ONE_MINUTE, staleTime: ONE_MINUTE });
  const conditions = useQuery({ queryKey: ["conditions"], queryFn: api.currentConditions, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const forecasts = useQuery({ queryKey: ["forecasts"], queryFn: api.latestForecasts, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const history = useQuery({ queryKey: ["history", 72], queryFn: () => api.forecastHistory(72), refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const serviceState = status.data?.status ?? (status.isError ? "unavailable" : "checking");

  return (
    <>
      <AppHeader page="dashboard" serviceState={serviceState} />
      <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
        <section className="mb-8 max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Live air information</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Understand the latest PM2.5 data and forecast.</h1>
          <p className="mt-3 text-base leading-7 text-slate-600">
            AirAware presents live measurements and model forecasts from the configured New Delhi monitoring station.
          </p>
        </section>
        {status.data?.status === "limited" && (
          <div className="mb-6">
            <UnavailablePanel
              title="Some services are limited"
              message="Available information is still shown below. Missing data is clearly marked instead of being estimated."
            />
          </div>
        )}
        <section aria-labelledby="current-heading">
          <div className="mb-4 flex items-center gap-2">
            <Activity className="size-5 text-teal-700" aria-hidden="true" />
            <h2 id="current-heading" className="text-xl font-semibold">
              Current PM2.5
            </h2>
          </div>
          {conditions.isLoading ? (
            <LoadingBlock label="Loading current PM2.5" />
          ) : conditions.isError ? (
            <UnavailablePanel
              title="Current PM2.5 is unavailable"
              message={errorMessage(conditions.error, "Current conditions are temporarily unavailable.")}
            />
          ) : (
            conditions.data && (
              <>
                <article className="rounded-2xl bg-gradient-to-br from-teal-800 to-cyan-800 p-6 text-white shadow-lg sm:p-8">
                  <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                    <div>
                      <p className="text-sm font-medium text-teal-100">Latest approved observation</p>
                      <p className="mt-3 text-5xl font-bold tracking-tight sm:text-6xl">
                        {formatPm25(conditions.data.pm25.value_ug_m3)} <span className="text-xl font-medium text-teal-100">µg/m³</span>
                      </p>
                      <p className="mt-4 text-sm text-teal-100">
                        Observed {formatDateTime(conditions.data.pm25.observed_at)} · {formatRelativeAge(conditions.data.pm25.received_at)}
                      </p>
                      <div className="mt-5">
                        <WhoAqiBadge pm25={conditions.data.pm25.value_ug_m3} variant="hero" />
                      </div>
                    </div>
                    <div className="rounded-xl bg-white/10 p-4 text-sm text-teal-50">
                      <p className="font-semibold">{conditions.data.source.location_name}</p>
                      <p className="mt-1 capitalize">Source: {conditions.data.source.provider}</p>
                    </div>
                  </div>
                </article>
                <WhoScaleLegend currentPm25={conditions.data.pm25.value_ug_m3} />
              </>
            )
          )}
        </section>
        <section className="mt-10" aria-labelledby="forecast-heading">
          <div className="mb-4 flex items-center gap-2">
            <CloudSun className="size-5 text-teal-700" aria-hidden="true" />
            <h2 id="forecast-heading" className="text-xl font-semibold">
              Saved forecasts
            </h2>
          </div>
          {forecasts.isLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              <LoadingBlock />
              <LoadingBlock />
              <LoadingBlock />
            </div>
          ) : forecasts.isError ? (
            <UnavailablePanel title="Forecasts are unavailable" message={errorMessage(forecasts.error, "Forecasts are temporarily unavailable.")} />
          ) : (
            forecasts.data && (
              <>
                <div className="grid gap-4 md:grid-cols-3">
                  {forecasts.data.forecasts.map((forecast) => (
                    <ForecastCard key={forecast.horizon_hours} forecast={forecast} />
                  ))}
                </div>
                <p className="mt-3 text-right text-xs text-slate-500">Forecast issued {formatDateTime(forecasts.data.issued_at)}</p>
              </>
            )
          )}
        </section>
        <section className="mt-10">
          <ActivityPlanner />
        </section>
        <section className="mt-10">
          {history.isLoading ? (
            <LoadingBlock label="Loading PM2.5 trend" />
          ) : history.isError ? (
            <UnavailablePanel title="Chart data is unavailable" message={errorMessage(history.error, "Recent history is temporarily unavailable.")} />
          ) : (
            history.data && (
              <Suspense fallback={<LoadingBlock label="Loading PM2.5 chart" />}>
                <AirQualityChart history={history.data} />
              </Suspense>
            )
          )}
        </section>
        <aside className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-600">
          <p className="font-semibold text-slate-800">Important</p>
          <p className="mt-1">
            Comparative timing guidance only; this is not a safety guarantee or medical advice. Measurements and forecasts are shown in µg/m³ with their source times.
          </p>
        </aside>
      </main>
    </>
  );
}
