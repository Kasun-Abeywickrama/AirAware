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
const AlertPreferencesPage = lazy(() =>
  import("./features/alerts/AlertPreferencesPage").then((module) => ({ default: module.AlertPreferencesPage })),
);

function pageFromHash(): Page {
  if (window.location.hash === "#forecast") return "forecast";
  if (window.location.hash === "#alerts") return "alerts";
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
      ) : (
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
      )}
    </div>
  );
}
