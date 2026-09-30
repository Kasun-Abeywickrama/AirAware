import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CalendarDays, ChevronDown, Clock3, Grid2X2, Sparkles, Table2 } from "lucide-react";
import { api } from "../../api/client";
import type { ActivityPlan, ActivityPlanWindow } from "../../api/types";
import { formatPm25 } from "../../utils/format";
import { UnavailablePanel } from "../../components/common/DataState";

const DURATIONS = [60, 120, 180, 240, 360, 480];

function newDelhiDate() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const value = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return `${value("year")}-${value("month")}-${value("day")}`;
}

function formatSelectedDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "long",
  }).format(new Date(`${value}T12:00:00+05:30`));
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(value));
}

type ViewMode = "clock" | "cards" | "table";

function WindowCards({ plan }: { plan: ActivityPlan }) {
  return (
    <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {plan.windows.map((window, index) => (
        <li key={`${window.start_at}-${window.end_at}`} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-teal-700">Option {index + 1}</p>
          <p className="mt-2 font-semibold text-slate-950">
            {formatTime(window.start_at)} – {formatTime(window.end_at)}
          </p>
          <p className="mt-3 text-sm text-slate-600">
            Mean forecast: <span className="font-semibold text-slate-900">{formatPm25(window.mean_predicted_value_ug_m3)} µg/m³</span>
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Mean upper range: <span className="font-semibold text-slate-900">{formatPm25(window.mean_upper_bound_ug_m3)} µg/m³</span>
          </p>
        </li>
      ))}
    </ol>
  );
}

function WindowTable({ plan }: { plan: ActivityPlan }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full text-left text-sm">
        <caption className="sr-only">Activity plan options and forecast values</caption>
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th className="px-4 py-3 font-semibold">Option</th>
            <th className="px-4 py-3 font-semibold">Time</th>
            <th className="px-4 py-3 font-semibold">Mean forecast</th>
            <th className="px-4 py-3 font-semibold">Upper range</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {plan.windows.map((window, index) => (
            <tr key={`${window.start_at}-${window.end_at}`}>
              <td className="px-4 py-3 font-semibold text-teal-700">{index + 1}</td>
              <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
                {formatTime(window.start_at)} – {formatTime(window.end_at)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-700">{formatPm25(window.mean_predicted_value_ug_m3)} µg/m³</td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-700">{formatPm25(window.mean_upper_bound_ug_m3)} µg/m³</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function newDelhiHour(value: string) {
  const hour = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    hourCycle: "h23",
  }).formatToParts(new Date(value)).find((part) => part.type === "hour")?.value;
  return Number(hour ?? 0) % 12;
}

function rangeColour(window: ActivityPlanWindow, windows: ActivityPlanWindow[]) {
  const values = windows.map((item) => item.mean_predicted_value_ug_m3);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const ratio = maximum === minimum ? 0 : (window.mean_predicted_value_ug_m3 - minimum) / (maximum - minimum);

  if (ratio < 0.25) return "#0f766e";
  if (ratio < 0.5) return "#0d9488";
  if (ratio < 0.75) return "#2dd4bf";
  return "#99f6e4";
}

function ClockFace({ window, windows }: { window: ActivityPlanWindow; windows: ActivityPlanWindow[] }) {
  const circumference = 2 * Math.PI * 42;
  const startHour = newDelhiHour(window.start_at);
  const durationHours = Math.max(1, Math.round((new Date(window.end_at).getTime() - new Date(window.start_at).getTime()) / 3_600_000));
  const rangeLength = Math.min(durationHours, 12) * (circumference / 12);
  const colour = rangeColour(window, windows);
  const handAngle = ((startHour * 30 - 90) * Math.PI) / 180;
  const handX = 50 + 23 * Math.cos(handAngle);
  const handY = 50 + 23 * Math.sin(handAngle);

  return (
    <svg
      viewBox="0 0 100 100"
      className="mx-auto block w-full max-w-44"
      role="img"
      aria-label={`${formatTime(window.start_at)} to ${formatTime(window.end_at)} highlighted on the clock`}
    >
      <defs>
        <marker id="clock-hand-arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="3" markerHeight="3" orient="auto">
          <path d="M 0 0 L 6 3 L 0 6 z" fill="#cbd5e1" />
        </marker>
      </defs>
      <circle cx="50" cy="50" r="42" fill="white" stroke="#e2e8f0" strokeWidth="7" />
      <circle
        cx="50"
        cy="50"
        r="42"
        fill="none"
        stroke={colour}
        strokeWidth="7"
        strokeLinecap="round"
        strokeDasharray={`${rangeLength} ${circumference - rangeLength}`}
        strokeDashoffset={-startHour * (circumference / 12)}
        transform="rotate(-90 50 50)"
      />
      <line x1="50" y1="50" x2={handX} y2={handY} stroke="#cbd5e1" strokeWidth="1.25" strokeLinecap="round" markerEnd="url(#clock-hand-arrow)" />
      {Array.from({ length: 12 }, (_, index) => {
        const hour = index + 1;
        const angle = ((hour * 30 - 90) * Math.PI) / 180;
        const x = 50 + 30 * Math.cos(angle);
        const y = 50 + 30 * Math.sin(angle) + 1.5;
        return (
          <text key={hour} x={x} y={y} textAnchor="middle" className="fill-slate-600 text-[7px] font-semibold">
            {hour}
          </text>
        );
      })}
      <circle cx="50" cy="50" r="2.5" fill={colour} />
    </svg>
  );
}

function ClockCircles({ plan }: { plan: ActivityPlan }) {
  return (
    <ol className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-5">
      {plan.windows.map((window, index) => (
        <li key={`${window.start_at}-${window.end_at}`} className="text-center">
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-teal-700">Option {index + 1}</p>
          <ClockFace window={window} windows={plan.windows} />
          <p className="mt-2 text-sm font-semibold text-slate-900">
            {formatTime(window.start_at)} – {formatTime(window.end_at)}
          </p>
          <p className="mt-1 text-xs text-slate-600">
            Forecast <span className="font-semibold text-slate-800">{formatPm25(window.mean_predicted_value_ug_m3)} µg/m³</span> · Upper{" "}
            {formatPm25(window.mean_upper_bound_ug_m3)}
          </p>
        </li>
      ))}
    </ol>
  );
}

function PlanResults({ plan }: { plan: ActivityPlan }) {
  const [view, setView] = useState<ViewMode>("clock");
  const modes: Array<{ id: ViewMode; label: string; Icon: typeof Grid2X2 }> = [
    { id: "clock", label: "Clock", Icon: Clock3 },
    { id: "cards", label: "Cards", Icon: Grid2X2 },
    { id: "table", label: "Table", Icon: Table2 },
  ];
  return (
    <div className="mt-6" aria-live="polite">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="font-semibold text-slate-900">
          Best available times for {formatSelectedDate(plan.date)} · {plan.duration_minutes / 60}-hour activity
        </h3>
        <div className="inline-flex w-fit rounded-lg bg-slate-100 p-1" role="tablist" aria-label="Result display mode">
          {modes.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={view === id}
              className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition ${
                view === id ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
              onClick={() => setView(id)}
            >
              <Icon className="size-3.5" aria-hidden="true" />
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4" role="tabpanel">
        {view === "clock" && <ClockCircles plan={plan} />}
        {view === "cards" && <WindowCards plan={plan} />}
        {view === "table" && <WindowTable plan={plan} />}
      </div>
      <p className="mt-4 text-xs leading-5 text-slate-500">{plan.disclaimer}</p>
    </div>
  );
}

export function ActivityPlannerPage() {
  const [date, setDate] = useState(newDelhiDate);
  const [duration, setDuration] = useState(60);
  const planner = useMutation({ mutationFn: () => api.activityPlan(date, duration) });

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
      <section className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Outdoor planning</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Activity Planner</h1>
        <p className="mt-3 text-base leading-7 text-slate-600">
          Find the cleanest air windows for outdoor exercise, errands, and commuting in New Delhi based on hourly PM2.5 forecasts.
        </p>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="planner-heading">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-teal-50 p-2 text-teal-700">
            <Sparkles className="size-5" aria-hidden="true" />
          </div>
          <div>
            <h2 id="planner-heading" className="text-lg font-semibold text-slate-950">
              Plan your outdoor activity
            </h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">Select your intended date and activity duration to calculate optimal windows.</p>
          </div>
        </div>
        <form
          className="mt-6 grid gap-4 md:grid-cols-[1fr_1fr_auto] md:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            planner.mutate();
          }}
        >
          <label className="grid gap-2 text-sm font-medium text-slate-800">
            <span className="flex items-center gap-1.5">
              <CalendarDays className="size-4 text-teal-700" aria-hidden="true" />
              Date
            </span>
            <input
              className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 shadow-sm focus:border-teal-700"
              type="date"
              value={date}
              min={newDelhiDate()}
              onChange={(event) => setDate(event.target.value)}
              required
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-800">
            <span className="flex items-center gap-1.5">
              <Clock3 className="size-4 text-teal-700" aria-hidden="true" />
              Duration
            </span>
            <div className="relative">
              <select
                className="w-full appearance-none rounded-lg border border-slate-300 bg-white py-2.5 pl-3.5 pr-10 text-slate-900 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-1 focus:ring-teal-700"
                value={duration}
                onChange={(event) => setDuration(Number(event.target.value))}
              >
                {DURATIONS.map((minutes) => (
                  <option key={minutes} value={minutes}>
                    {minutes / 60} {minutes === 60 ? "hour" : "hours"}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-500" aria-hidden="true" />
            </div>
          </label>
          <button
            className="rounded-lg bg-teal-700 px-5 py-2.5 font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            type="submit"
            disabled={planner.isPending}
          >
            {planner.isPending ? "Finding times…" : "Find best times"}
          </button>
        </form>
        {planner.isError && (
          <div className="mt-5">
            <UnavailablePanel
              title="No complete plan is available"
              message={planner.error instanceof Error ? planner.error.message : "Try a different future date or duration."}
            />
          </div>
        )}
        {planner.data && <PlanResults plan={planner.data} />}
      </section>
    </main>
  );
}
