import { MapPin } from "lucide-react";
import type { Availability } from "../../api/types";
import { StatusBadge } from "../common/StatusBadge";

export type Page = "dashboard" | "forecast" | "planner" | "alerts" | "methodology";

export function AppHeader({ page, serviceState }: { page: Page; serviceState: Availability | "checking" }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <a className="skip-link rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white shadow-lg" href="#main-content">
        Skip to main content
      </a>
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        {/* Brand wordmark */}
        <a href="#" className="flex items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-2 rounded-lg" aria-label="AirAware – go to dashboard">
          <img
            src="/logo-wordmark.png"
            alt="AirAware"
            className="h-7 w-auto"
          />
        </a>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 sm:justify-end">
          <nav className="flex items-center gap-5" aria-label="Main navigation">
            <a
              href="#"
              className={`border-b-2 py-2 text-sm font-semibold transition ${
                page === "dashboard" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
              }`}
              aria-current={page === "dashboard" ? "page" : undefined}
            >
              Dashboard
            </a>
            <a
              href="#forecast"
              className={`border-b-2 py-2 text-sm font-semibold transition ${
                page === "forecast" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
              }`}
              aria-current={page === "forecast" ? "page" : undefined}
            >
              Forecast
            </a>
            <a
              href="#planner"
              className={`border-b-2 py-2 text-sm font-semibold transition ${
                page === "planner" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
              }`}
              aria-current={page === "planner" ? "page" : undefined}
            >
              Planner
            </a>
            <a
              href="#alerts"
              className={`border-b-2 py-2 text-sm font-semibold transition ${
                page === "alerts" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
              }`}
              aria-current={page === "alerts" ? "page" : undefined}
            >
              Alerts
            </a>
            <a
              href="#methodology"
              className={`border-b-2 py-2 text-sm font-semibold transition ${
                page === "methodology" ? "border-teal-700 text-teal-800" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
              }`}
              aria-current={page === "methodology" ? "page" : undefined}
            >
              Methodology
            </a>
          </nav>
          <span className="hidden h-5 w-px bg-slate-200 sm:block" aria-hidden="true" />
          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-700">
            <MapPin className="size-4 text-teal-700" aria-hidden="true" />
            New Delhi
          </span>
          <StatusBadge status={serviceState} />
        </div>
      </div>
    </header>
  );
}

