import { lazy, Suspense, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, CloudSun } from "lucide-react";
import { api } from "../../api/client";
import { useAlertPreference } from "../../hooks/useAirData";
import { getBrowserId } from "../../utils/browserId";
import { sendThresholdNotification } from "../../utils/notifications";
import { LoadingBlock, UnavailablePanel } from "../../components/common/DataState";
import { AqiBadge } from "../../components/common/AqiBadge";
import { ThresholdAlertBanner } from "../../components/common/ThresholdAlertBanner";
import { ForecastCard } from "../forecast/ForecastCard";
import { formatDateTime, formatPm25, formatRelativeAge } from "../../utils/format";
import { EPA_AQI_SCALE, getAqiCategory } from "../../utils/aqi";

const FIVE_MINUTES = 5 * 60_000;
const ONE_MINUTE = 60_000;
const AirQualityChart = lazy(() =>
  import("./AirQualityChart").then((module) => ({ default: module.AirQualityChart })),
);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function AqiScaleLegend({ currentPm25 }: { currentPm25: number }) {
  const active = getAqiCategory(currentPm25);
  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 sm:px-4">
      <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">EPA AQI Scale</span>
        <span className="text-[11px] text-slate-400">PM2.5 (µg/m³)</span>
      </div>
      <ol className="flex overflow-x-auto pb-1.5 pt-0.5 gap-1.5 custom-scrollbar sm:pb-0 sm:pt-0 sm:overflow-visible sm:gap-1.5" aria-label="US EPA AQI PM2.5 air quality scale">
        {EPA_AQI_SCALE.map(({ category, shortLabel, range, colors }) => {
          const isCurrent = active.category === category;
          return (
            <li
              key={category}
              className={`flex min-w-[110px] shrink-0 items-center justify-between gap-1.5 rounded-lg px-2.5 py-1.5 text-xs transition-all duration-200 sm:min-w-0 sm:flex-1 sm:flex-col sm:items-center sm:justify-center sm:py-2 sm:px-1 text-center ${
                isCurrent
                  ? `${colors.badge} font-semibold ring-1.5 ring-slate-400/50 shadow-xs`
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100/70"
              }`}
              aria-current={isCurrent ? "true" : undefined}
            >
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className={`size-2 shrink-0 rounded-full ${colors.dot}`} aria-hidden="true" />
                <span className={`whitespace-nowrap font-semibold sm:whitespace-normal ${isCurrent ? colors.text : "text-slate-800"}`}>
                  {shortLabel}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 sm:text-[11px]">{range}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}


export function DashboardPage() {
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: ONE_MINUTE, staleTime: ONE_MINUTE });
  const conditions = useQuery({ queryKey: ["conditions"], queryFn: api.currentConditions, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const forecasts = useQuery({ queryKey: ["forecasts"], queryFn: api.latestForecasts, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const history = useQuery({ queryKey: ["history", 72], queryFn: () => api.forecastHistory(72), refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const browserId = getBrowserId();
  const alertPreference = useAlertPreference(browserId);

  // Dispatch native browser notification if threshold is exceeded and notifications are allowed
  useEffect(() => {
    if (
      conditions.data &&
      alertPreference.data?.enabled &&
      alertPreference.data.threshold_ug_m3 !== null
    ) {
      sendThresholdNotification({
        currentPm25: conditions.data.pm25.value_ug_m3,
        threshold: alertPreference.data.threshold_ug_m3,
        locationName: conditions.data.source.location_name,
      });
    }
  }, [conditions.data, alertPreference.data]);

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
        <section className="mb-6 max-w-3xl sm:mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700 sm:text-sm">Live air information</p>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl lg:text-4xl">Understand the latest PM2.5 data and forecast.</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600 sm:mt-3 sm:text-base sm:leading-7">
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

        {conditions.data && (
          <div className="mb-6">
            <ThresholdAlertBanner
              currentPm25={conditions.data.pm25.value_ug_m3}
              preference={alertPreference.data}
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
                <article className="rounded-2xl bg-gradient-to-br from-teal-800 to-cyan-800 p-5 text-white shadow-lg sm:p-8">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-medium text-teal-100 sm:text-sm">Latest approved observation</p>
                      <p className="mt-2 text-4xl font-bold tracking-tight sm:mt-3 sm:text-6xl">
                        {formatPm25(conditions.data.pm25.value_ug_m3)} <span className="text-base font-medium text-teal-100 sm:text-xl">µg/m³</span>
                      </p>

                      {/* Threshold status badge only when alerts are actively enabled */}
                      {alertPreference.data?.enabled && alertPreference.data.threshold_ug_m3 !== null ? (
                        <div className="mt-2.5 inline-flex items-center gap-1.5 sm:mt-3.5">
                          {conditions.data.pm25.value_ug_m3 > alertPreference.data.threshold_ug_m3 ? (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/25 px-2.5 py-0.5 text-xs font-semibold text-rose-100 ring-1 ring-rose-300/40 sm:py-1">
                              <span className="size-1.5 rounded-full bg-rose-400" />
                              Above your limit ({alertPreference.data.threshold_ug_m3} µg/m³)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/25 px-2.5 py-0.5 text-xs font-semibold text-emerald-100 ring-1 ring-emerald-300/40 sm:py-1">
                              <span className="size-1.5 rounded-full bg-emerald-400" />
                              Below your limit ({alertPreference.data.threshold_ug_m3} µg/m³)
                            </span>
                          )}
                        </div>
                      ) : null}
                    </div>
                    <div className="hidden sm:block">
                      <AqiBadge pm25={conditions.data.pm25.value_ug_m3} variant="hero" />
                    </div>
                  </div>
                  <div className="mt-6 flex flex-col gap-2 pt-4 border-t border-white/10 sm:mt-8 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-xs text-teal-100 sm:text-sm">
                      Observed {formatDateTime(conditions.data.pm25.observed_at)} · {formatRelativeAge(conditions.data.pm25.received_at)}
                    </p>
                    <div className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium text-teal-100 sm:text-sm">
                      <span className="size-2 rounded-full bg-emerald-400" aria-hidden="true" />
                      <span>{conditions.data.source.location_name}</span>
                    </div>
                  </div>
                </article>
                <AqiScaleLegend currentPm25={conditions.data.pm25.value_ug_m3} />
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
                <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3 sm:gap-4">
                  {forecasts.data.forecasts.map((forecast) => (
                    <ForecastCard key={forecast.horizon_hours} forecast={forecast} />
                  ))}
                </div>
                <p className="mt-2.5 text-right text-xs text-slate-500 sm:mt-3">Forecast issued {formatDateTime(forecasts.data.issued_at)}</p>
              </>
            )
          )}
        </section>

        <section className="mt-8 sm:mt-10">
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
        <aside className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 text-xs leading-5 text-slate-600 sm:mt-8 sm:p-5 sm:text-sm sm:leading-6">
          <p className="font-semibold text-slate-800">Important</p>
          <p className="mt-1">
            Comparative timing guidance only; this is not a safety guarantee or medical advice. Measurements and forecasts are shown in µg/m³ with their source times.
          </p>
        </aside>
      </main>
  );
}
