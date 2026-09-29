import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, CloudSun, MapPin, Wind } from "lucide-react";
import { api } from "./api/client";
import type { Availability } from "./api/types";
import { ActivityPlanner } from "./components/ActivityPlanner";
import { LoadingBlock, UnavailablePanel } from "./components/DataState";
import { ForecastCard } from "./components/ForecastCard";
import { StatusBadge } from "./components/StatusBadge";
import { formatDateTime, formatPm25, formatRelativeAge } from "./lib/format";

const FIVE_MINUTES = 5 * 60_000;
const ONE_MINUTE = 60_000;
const AirQualityChart = lazy(() =>
  import("./components/AirQualityChart").then((module) => ({ default: module.AirQualityChart })),
);
const ForecastHistoryPage = lazy(() =>
  import("./components/ForecastHistoryPage").then((module) => ({ default: module.ForecastHistoryPage })),
);
const AlertPreferencesPage = lazy(() =>
  import("./components/AlertPreferencesPage").then((module) => ({ default: module.AlertPreferencesPage })),
);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

type Page = "dashboard" | "forecast" | "alerts";

function pageFromHash(): Page {
  if (window.location.hash === "#forecast") return "forecast";
  if (window.location.hash === "#alerts") return "alerts";
  return "dashboard";
}

function AppHeader({ page, serviceState }: { page: Page; serviceState: Availability | "checking" }) {
  return <header className="border-b border-slate-200 bg-white">
    <a className="skip-link rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white shadow-lg" href="#main-content">Skip to main content</a>
    <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
      <div className="flex items-center gap-3"><div className="rounded-xl bg-teal-700 p-2.5 text-white"><Wind className="size-6" aria-hidden="true" /></div><div><p className="text-xl font-bold tracking-tight">AirAware</p><p className="text-sm text-slate-600">PM2.5 decision-support dashboard</p></div></div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 sm:justify-end"><nav className="flex items-center gap-5" aria-label="Main navigation"><a href="#" className={`border-b-2 py-2 text-sm font-semibold transition ${page === "dashboard" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"}`} aria-current={page === "dashboard" ? "page" : undefined}>Dashboard</a><a href="#forecast" className={`border-b-2 py-2 text-sm font-semibold transition ${page === "forecast" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"}`} aria-current={page === "forecast" ? "page" : undefined}>Forecast</a><a href="#alerts" className={`border-b-2 py-2 text-sm font-semibold transition ${page === "alerts" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"}`} aria-current={page === "alerts" ? "page" : undefined}>Alerts</a></nav><span className="hidden h-5 w-px bg-slate-200 sm:block" aria-hidden="true" /><span className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-700"><MapPin className="size-4 text-teal-700" aria-hidden="true" />New Delhi</span><StatusBadge status={serviceState} /></div>
    </div>
  </header>;
}

function DashboardPage() {
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: ONE_MINUTE, staleTime: ONE_MINUTE });
  const conditions = useQuery({ queryKey: ["conditions"], queryFn: api.currentConditions, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const forecasts = useQuery({ queryKey: ["forecasts"], queryFn: api.latestForecasts, refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const history = useQuery({ queryKey: ["history", 72], queryFn: () => api.forecastHistory(72), refetchInterval: FIVE_MINUTES, staleTime: FIVE_MINUTES });
  const serviceState = status.data?.status ?? (status.isError ? "unavailable" : "checking");

  return <>
      <AppHeader page="dashboard" serviceState={serviceState} />
      <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
        <section className="mb-8 max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Live air information</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Understand the latest PM2.5 data and forecast.</h1><p className="mt-3 text-base leading-7 text-slate-600">AirAware presents live measurements and model forecasts from the configured New Delhi monitoring station.</p></section>
        {status.data?.status === "limited" && <div className="mb-6"><UnavailablePanel title="Some services are limited" message="Available information is still shown below. Missing data is clearly marked instead of being estimated." /></div>}
        <section aria-labelledby="current-heading">
          <div className="mb-4 flex items-center gap-2"><Activity className="size-5 text-teal-700" aria-hidden="true" /><h2 id="current-heading" className="text-xl font-semibold">Current PM2.5</h2></div>
          {conditions.isLoading ? <LoadingBlock label="Loading current PM2.5" /> : conditions.isError ? <UnavailablePanel title="Current PM2.5 is unavailable" message={errorMessage(conditions.error, "Current conditions are temporarily unavailable.")} /> : conditions.data && <article className="rounded-2xl bg-gradient-to-br from-teal-800 to-cyan-800 p-6 text-white shadow-lg sm:p-8"><div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-sm font-medium text-teal-100">Latest approved observation</p><p className="mt-3 text-5xl font-bold tracking-tight sm:text-6xl">{formatPm25(conditions.data.pm25.value_ug_m3)} <span className="text-xl font-medium text-teal-100">µg/m³</span></p><p className="mt-4 text-sm text-teal-100">Observed {formatDateTime(conditions.data.pm25.observed_at)} · {formatRelativeAge(conditions.data.pm25.received_at)}</p></div><div className="rounded-xl bg-white/10 p-4 text-sm text-teal-50"><p className="font-semibold">{conditions.data.source.location_name}</p><p className="mt-1 capitalize">Source: {conditions.data.source.provider}</p></div></div></article>}
        </section>
        <section className="mt-10" aria-labelledby="forecast-heading"><div className="mb-4 flex items-center gap-2"><CloudSun className="size-5 text-teal-700" aria-hidden="true" /><h2 id="forecast-heading" className="text-xl font-semibold">Saved forecasts</h2></div>{forecasts.isLoading ? <div className="grid gap-4 md:grid-cols-3"><LoadingBlock /><LoadingBlock /><LoadingBlock /></div> : forecasts.isError ? <UnavailablePanel title="Forecasts are unavailable" message={errorMessage(forecasts.error, "Forecasts are temporarily unavailable.")} /> : forecasts.data && <><div className="grid gap-4 md:grid-cols-3">{forecasts.data.forecasts.map((forecast) => <ForecastCard key={forecast.horizon_hours} forecast={forecast} />)}</div><p className="mt-3 text-right text-xs text-slate-500">Forecast issued {formatDateTime(forecasts.data.issued_at)}</p></>}</section>
        <section className="mt-10"><ActivityPlanner /></section>
        <section className="mt-10">{history.isLoading ? <LoadingBlock label="Loading PM2.5 trend" /> : history.isError ? <UnavailablePanel title="Chart data is unavailable" message={errorMessage(history.error, "Recent history is temporarily unavailable.")} /> : history.data && <Suspense fallback={<LoadingBlock label="Loading PM2.5 chart" />}><AirQualityChart history={history.data} /></Suspense>}</section>
        <aside className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-600"><p className="font-semibold text-slate-800">Important</p><p className="mt-1">Comparative timing guidance only; this is not a safety guarantee or medical advice. Measurements and forecasts are shown in µg/m³ with their source times.</p></aside>
      </main>
  </>;
}

export default function App() {
  const [page, setPage] = useState<Page>(pageFromHash);
  useEffect(() => {
    const syncPage = () => setPage(pageFromHash());
    window.addEventListener("hashchange", syncPage);
    return () => window.removeEventListener("hashchange", syncPage);
  }, []);

  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: ONE_MINUTE, staleTime: ONE_MINUTE });
  const serviceState = status.data?.status ?? (status.isError ? "unavailable" : "checking");

  return <div className="min-h-screen bg-slate-50 text-slate-900">
    {page === "dashboard" ? <DashboardPage /> : page === "forecast" ? <><AppHeader page="forecast" serviceState={serviceState} /><Suspense fallback={<main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10"><LoadingBlock label="Loading forecast history" /></main>}><ForecastHistoryPage /></Suspense></> : <><AppHeader page="alerts" serviceState={serviceState} /><Suspense fallback={<main id="main-content" className="mx-auto max-w-3xl px-5 py-8 sm:px-8 sm:py-10"><LoadingBlock label="Loading alert preferences" /></main>}><AlertPreferencesPage /></Suspense></>}
  </div>;
}
