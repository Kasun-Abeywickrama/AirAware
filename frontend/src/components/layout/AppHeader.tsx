import { useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Activity, Bell, Calendar, FileText, LayoutDashboard, MapPin, Menu, X } from "lucide-react";
import type { Availability } from "../../api/types";
import { StatusBadge } from "../common/StatusBadge";

export type Page = "dashboard" | "forecast" | "planner" | "alerts" | "methodology";

export function AppHeader({
  serviceState,
}: {
  page?: Page;
  serviceState: Availability | "checking";
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const desktopNavLinkClass = ({ isActive }: { isActive: boolean }) =>
    `border-b-2 py-2 text-sm font-semibold transition ${
      isActive
        ? "border-teal-700 text-teal-800"
        : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-950"
    }`;

  const mobileNavLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-semibold transition ${
      isActive
        ? "bg-teal-50 text-teal-800"
        : "text-slate-700 hover:bg-slate-100 hover:text-slate-950"
    }`;

  const closeMenu = () => setIsMobileMenuOpen(false);

  return (
    <header className="border-b border-slate-200 bg-white">
      <a className="skip-link rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white shadow-lg" href="#main-content">
        Skip to main content
      </a>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5 sm:px-8 sm:py-4">
        {/* Brand wordmark */}
        <Link
          to="/"
          onClick={closeMenu}
          className="flex items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-2 rounded-lg"
          aria-label="AirAware – go to dashboard"
        >
          <img
            src="/logo-wordmark.png"
            alt="AirAware"
            className="h-7 w-auto"
          />
        </Link>

        {/* Desktop Navigation (> 768px / md:) */}
        <div className="hidden md:flex md:items-center md:gap-x-4 lg:gap-x-5">
          <nav className="flex items-center gap-4 lg:gap-5" aria-label="Main navigation">
            <NavLink to="/" end className={desktopNavLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/forecast" className={desktopNavLinkClass}>
              Forecast
            </NavLink>
            <NavLink to="/planner" className={desktopNavLinkClass}>
              Planner
            </NavLink>
            <NavLink to="/alerts" className={desktopNavLinkClass}>
              Alerts
            </NavLink>
            <NavLink to="/methodology" className={desktopNavLinkClass}>
              Methodology
            </NavLink>
          </nav>
          <span className="hidden h-5 w-px bg-slate-200 lg:block" aria-hidden="true" />
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-700 lg:text-sm">
            <MapPin className="size-4 text-teal-700 shrink-0" aria-hidden="true" />
            <span className="whitespace-nowrap">New Delhi</span>
          </span>
          <StatusBadge status={serviceState} />
        </div>

        {/* Mobile / Small Tablet Bar (< 768px / md:) */}
        <div className="flex items-center gap-2.5 md:hidden">
          <StatusBadge status={serviceState} />
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen((prev) => !prev)}
            className="rounded-lg p-2 text-slate-700 hover:bg-slate-100 hover:text-slate-950 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
            aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
              <X className="size-5.5 text-slate-800" aria-hidden="true" />
            ) : (
              <Menu className="size-5.5 text-slate-800" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Dropdown Drawer */}
      {isMobileMenuOpen && (
        <div className="border-t border-slate-100 bg-white px-5 py-4 shadow-lg md:hidden" aria-label="Mobile menu">
          <nav className="flex flex-col space-y-1">
            <NavLink to="/" end onClick={closeMenu} className={mobileNavLinkClass}>
              <LayoutDashboard className="size-4 text-teal-700" aria-hidden="true" />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/forecast" onClick={closeMenu} className={mobileNavLinkClass}>
              <Activity className="size-4 text-teal-700" aria-hidden="true" />
              <span>Forecast</span>
            </NavLink>
            <NavLink to="/planner" onClick={closeMenu} className={mobileNavLinkClass}>
              <Calendar className="size-4 text-teal-700" aria-hidden="true" />
              <span>Planner</span>
            </NavLink>
            <NavLink to="/alerts" onClick={closeMenu} className={mobileNavLinkClass}>
              <Bell className="size-4 text-teal-700" aria-hidden="true" />
              <span>Alerts</span>
            </NavLink>
            <NavLink to="/methodology" onClick={closeMenu} className={mobileNavLinkClass}>
              <FileText className="size-4 text-teal-700" aria-hidden="true" />
              <span>Methodology</span>
            </NavLink>
          </nav>
          <div className="mt-3.5 border-t border-slate-100 pt-3 flex items-center justify-between text-xs text-slate-600">
            <span className="inline-flex items-center gap-1.5 font-medium">
              <MapPin className="size-3.5 text-teal-700" aria-hidden="true" />
              <span>New Delhi Station</span>
            </span>
            <span className="text-slate-400">CPCB CAAQMS</span>
          </div>
        </div>
      )}
    </header>
  );
}
