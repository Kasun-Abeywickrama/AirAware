import { lazy, Suspense, useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";
import { AppHeader } from "./components/layout/AppHeader";
import { AppFooter } from "./components/layout/AppFooter";
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

/**
 * Handles backwards-compatible redirects for legacy URLs with hash fragments
 * (e.g. `/#forecast` -> `/forecast`, `/#planner` -> `/planner`).
 */
function HashRedirect() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.hash) {
      const cleanTarget = location.hash.replace("#", "");
      if (["forecast", "planner", "alerts", "methodology"].includes(cleanTarget)) {
        navigate(`/${cleanTarget}`, { replace: true });
      }
    }
  }, [location.hash, navigate]);

  return null;
}

function AppContent() {
  const status = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: ONE_MINUTE,
    staleTime: ONE_MINUTE,
  });
  const serviceState = status.data?.status ?? (status.isError ? "unavailable" : "checking");

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <HashRedirect />
      <AppHeader serviceState={serviceState} />
      <div className="flex-1">
        <Suspense
          fallback={
            <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
              <LoadingBlock label="Loading content" />
            </main>
          }
        >
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/forecast" element={<ForecastHistoryPage />} />
            <Route path="/planner" element={<ActivityPlannerPage />} />
            <Route path="/alerts" element={<AlertPreferencesPage />} />
            <Route path="/methodology" element={<MethodologyPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </div>
      <AppFooter />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
