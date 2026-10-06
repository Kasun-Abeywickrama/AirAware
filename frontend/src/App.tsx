import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";
import { AppHeader, type Page } from "./components/layout/AppHeader";
import { LoadingBlock } from "./components/common/DataState";
import { DashboardPage } from "./features/dashboard/DashboardPage";

const ONE_MINUTE = 60_000;

const ForecastHistoryPage = lazy(() =>
  import("./features/forecast/ForecastHistoryPage").then((module) => ({ default: module.ForecastHistoryPage })),
);
const ActivityPlannerPage = lazy(() =>
  import("./features/planner/ActivityPlannerPage").then((module) => ({ default: module.ActivityPlannerPage })),
);
const AlertPreferencesPage = lazy(() =>
  import("./features/alerts/AlertPreferencesPage").then((module) => ({ default: module.AlertPreferencesPage })),
);
const MethodologyPage = lazy(() =>
  import("./features/methodology/MethodologyPage").then((module) => ({ default: module.MethodologyPage })),
);

function pageFromHash(): Page {
  if (window.location.hash === "#forecast") return "forecast";
  if (window.location.hash === "#planner") return "planner";
  if (window.location.hash === "#alerts") return "alerts";
  if (window.location.hash === "#methodology") return "methodology";
  return "dashboard";
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

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {page === "dashboard" ? (
        <DashboardPage />
      ) : page === "forecast" ? (
        <>
          <AppHeader page="forecast" serviceState={serviceState} />
          <Suspense
            fallback={
              <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
                <LoadingBlock label="Loading forecast history" />
              </main>
            }
          >
            <ForecastHistoryPage />
          </Suspense>
        </>
      ) : page === "planner" ? (
        <>
          <AppHeader page="planner" serviceState={serviceState} />
          <Suspense
            fallback={
              <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
                <LoadingBlock label="Loading activity planner" />
              </main>
            }
          >
            <ActivityPlannerPage />
          </Suspense>
        </>
      ) : page === "alerts" ? (
        <>
          <AppHeader page="alerts" serviceState={serviceState} />
          <Suspense
            fallback={
              <main id="main-content" className="mx-auto max-w-3xl px-5 py-8 sm:px-8 sm:py-10">
                <LoadingBlock label="Loading alert preferences" />
              </main>
            }
          >
            <AlertPreferencesPage />
          </Suspense>
        </>
      ) : (
        <>
          <AppHeader page="methodology" serviceState={serviceState} />
          <Suspense
            fallback={
              <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
                <LoadingBlock label="Loading standards & methodology" />
              </main>
            }
          >
            <MethodologyPage />
          </Suspense>
        </>
      )}
    </div>
  );
}
