import { Link } from "react-router-dom";
import { Activity, Bell, Calendar, Cpu, Database, ExternalLink, FileText, LayoutDashboard, MapPin, ShieldCheck } from "lucide-react";

export function AppFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-slate-200 bg-white text-slate-600" aria-label="Site footer">
      <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 sm:py-16">
        {/* Main Footer Grid */}
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          {/* Column 1: Brand & Overview */}
          <div className="space-y-4">
            <Link
              to="/"
              className="inline-block focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 rounded-lg"
              aria-label="AirAware homepage"
            >
              <img
                src="/logo-wordmark.png"
                alt="AirAware"
                className="h-7 w-auto"
              />
            </Link>
            <p className="text-xs leading-relaxed text-slate-600">
              Actionable air quality forecasting and outdoor activity intelligence for New Delhi, powered by gradient boosting ensembles and conformal uncertainty quantification.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
              <span className="size-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
              <MapPin className="size-3.5 text-teal-700" aria-hidden="true" />
              <span>New Delhi, India · CPCB Network</span>
            </div>
          </div>

          {/* Column 2: Platform Features */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Platform Features
            </h3>
            <ul className="mt-4 space-y-2.5 text-xs">
              <li>
                <Link
                  to="/"
                  className="inline-flex items-center gap-2 text-slate-600 transition hover:text-teal-800"
                >
                  <LayoutDashboard className="size-3.5 text-slate-400" aria-hidden="true" />
                  <span>Live Dashboard</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/forecast"
                  className="inline-flex items-center gap-2 text-slate-600 transition hover:text-teal-800"
                >
                  <Activity className="size-3.5 text-slate-400" aria-hidden="true" />
                  <span>Forecast & History</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/planner"
                  className="inline-flex items-center gap-2 text-slate-600 transition hover:text-teal-800"
                >
                  <Calendar className="size-3.5 text-slate-400" aria-hidden="true" />
                  <span>Activity Planner</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/alerts"
                  className="inline-flex items-center gap-2 text-slate-600 transition hover:text-teal-800"
                >
                  <Bell className="size-3.5 text-slate-400" aria-hidden="true" />
                  <span>Alert Preferences</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/methodology"
                  className="inline-flex items-center gap-2 text-slate-600 transition hover:text-teal-800"
                >
                  <FileText className="size-3.5 text-slate-400" aria-hidden="true" />
                  <span>Research Methodology</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Standards & Guidelines */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Standards & Indices
            </h3>
            <ul className="mt-4 space-y-2.5 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <ShieldCheck className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>US EPA AQI Standard (2024 updated PM2.5 breakpoints)</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>WHO Air Quality Guidelines (15 µg/m³ 24h limit)</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Conformal Prediction (95% uncertainty intervals)</span>
              </li>
              <li className="flex items-start gap-2">
                <Database className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Continuous Ambient Air Quality Monitoring (CAAQMS)</span>
              </li>
            </ul>
          </div>

          {/* Column 4: System Architecture */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              System Architecture
            </h3>
            <ul className="mt-4 space-y-2.5 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <Cpu className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Model Ensemble: LightGBM, XGBoost & CatBoost</span>
              </li>
              <li className="flex items-start gap-2">
                <Cpu className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Inference Horizon: 24-Hour Lookahead Window</span>
              </li>
              <li className="flex items-start gap-2">
                <Cpu className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Update Cadence: Automated Hourly Pipeline</span>
              </li>
              <li className="flex items-start gap-2">
                <FileText className="size-3.5 shrink-0 text-teal-700 mt-0.5" aria-hidden="true" />
                <span>Final Year Research Project</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Disclaimer */}
        <div className="mt-12 border-t border-slate-100 pt-8 flex flex-col gap-4 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
          <p>
            © {currentYear} AirAware. Developed for air quality intelligence & research.
          </p>
          <p className="max-w-xl text-[11px] leading-relaxed text-slate-400">
            Disclaimer: Predictions and air quality recommendations are indicative and computed using statistical machine learning models. For sensitive health advisories, please refer to official healthcare guidelines.
          </p>
        </div>
      </div>
    </footer>
  );
}
