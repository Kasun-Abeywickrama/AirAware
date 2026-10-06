import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CalendarDays, ChevronDown, Clock3, Grid2X2, Info, Table2 } from "lucide-react";
import { api } from "../../api/client";
import type { ActivityPlan, ActivityPlanWindow } from "../../api/types";
import { formatPm25 } from "../../utils/format";
import { calculateAqi, getAqiCategory } from "../../utils/aqi";
import { UnavailablePanel } from "../../components/common/DataState";
import { InfoTooltip } from "../../components/common/InfoTooltip";

const DURATIONS = [60, 120, 180, 240, 360, 480];

export function newDelhiDate(offsetDays: number = 0): string {
  const target = new Date(Date.now() + offsetDays * 86_400_000);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(target);
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
      {plan.windows.map((window, index) => {
        const aqi = getAqiCategory(window.mean_predicted_value_ug_m3);
        const aqiScore = calculateAqi(window.mean_predicted_value_ug_m3);
        const isBest = index === 0;
        return (
          <li
            key={`${window.start_at}-${window.end_at}`}
            className={`rounded-xl border p-4 transition ${isBest
                ? "border-teal-300 bg-teal-50/40 shadow-sm ring-1 ring-teal-500/20"
                : "border-slate-200 bg-slate-50"
              }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-bold uppercase tracking-wide text-teal-700">Option {index + 1}</p>
                {isBest && (
                  <span className="rounded bg-teal-700 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                    Best
                  </span>
                )}
              </div>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${aqi.colors.badge} ${aqi.colors.text}`}
              >
                <span className={`size-1.5 rounded-full ${aqi.colors.dot}`} aria-hidden="true" />
                <span>{aqi.label}</span>
                <span className="font-bold opacity-80">· AQI {aqiScore}</span>
              </span>
            </div>
            <p className="mt-2 font-semibold text-slate-950">
              {formatTime(window.start_at)} – {formatTime(window.end_at)}
            </p>
            <p className="mt-3 text-sm text-slate-600">
              Mean forecast:{" "}
              <span className="font-semibold text-slate-900">{formatPm25(window.mean_predicted_value_ug_m3)} µg/m³</span>
            </p>
            <p className="mt-1 text-sm text-slate-600">
              Mean upper range:{" "}
              <span className="font-semibold text-slate-900">{formatPm25(window.mean_upper_bound_ug_m3)} µg/m³</span>
            </p>
            <p className="mt-2.5 text-xs leading-relaxed text-slate-500">
              {aqi.guidance}
            </p>
          </li>
        );
      })}
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
            <th className="px-4 py-3 font-semibold">Air Quality (EPA AQI)</th>
            <th className="px-4 py-3 font-semibold">Mean forecast</th>
            <th className="px-4 py-3 font-semibold">Upper range</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {plan.windows.map((window, index) => {
            const aqi = getAqiCategory(window.mean_predicted_value_ug_m3);
            const aqiScore = calculateAqi(window.mean_predicted_value_ug_m3);
            return (
              <tr key={`${window.start_at}-${window.end_at}`}>
                <td className="px-4 py-3 font-semibold text-teal-700">
                  <div className="flex items-center gap-1.5">
                    <span>{index + 1}</span>
                    {index === 0 && (
                      <span className="rounded bg-teal-100 px-1 py-0.5 text-[10px] font-bold text-teal-800">
                        BEST
                      </span>
                    )}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
                  {formatTime(window.start_at)} – {formatTime(window.end_at)}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${aqi.colors.badge} ${aqi.colors.text}`}
                  >
                    <span className={`size-1.5 rounded-full ${aqi.colors.dot}`} aria-hidden="true" />
                    <span>{aqi.label}</span>
                    <span className="font-bold opacity-80">· AQI {aqiScore}</span>
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {formatPm25(window.mean_predicted_value_ug_m3)} µg/m³
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {formatPm25(window.mean_upper_bound_ug_m3)} µg/m³
                </td>
              </tr>
            );
          })}
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

const RANK_TEAL_COLOURS = [
  "#0f766e", // Option 1 (Best) – Deepest dark teal
  "#0d9488", // Option 2 – Rich teal
  "#14b8a6", // Option 3 – Medium teal
  "#2dd4bf", // Option 4 – Soft teal
  "#99f6e4", // Option 5 – Light teal
];

function ClockFace({ window, rankIndex }: { window: ActivityPlanWindow; rankIndex: number }) {
  const circumference = 2 * Math.PI * 42;
  const startHour = newDelhiHour(window.start_at);
  const durationHours = Math.max(1, Math.round((new Date(window.end_at).getTime() - new Date(window.start_at).getTime()) / 3_600_000));
  const rangeLength = Math.min(durationHours, 12) * (circumference / 12);
  const colour = RANK_TEAL_COLOURS[rankIndex] ?? "#0d9488";
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
          <path d="M 0 0 L 6 3 L 0 6 z" fill="#94a3b8" />
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
      <line x1="50" y1="50" x2={handX} y2={handY} stroke="#94a3b8" strokeWidth="1.25" strokeLinecap="round" markerEnd="url(#clock-hand-arrow)" />
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
    <ol className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
      {plan.windows.map((window, index) => {
        const aqi = getAqiCategory(window.mean_predicted_value_ug_m3);
        const aqiScore = calculateAqi(window.mean_predicted_value_ug_m3);
        return (
          <li
            key={`${window.start_at}-${window.end_at}`}
            className="flex flex-col items-center rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-center"
          >
            <div className="flex items-center gap-1">
              <p className="text-xs font-bold uppercase tracking-wide text-teal-700">Option {index + 1}</p>
              {index === 0 && (
                <span className="rounded bg-teal-700 px-1 text-[9px] font-bold uppercase text-white">Best</span>
              )}
            </div>
            <div className="my-2">
              <ClockFace window={window} rankIndex={index} />
            </div>
            <p className="text-sm font-semibold text-slate-950">
              {formatTime(window.start_at)} – {formatTime(window.end_at)}
            </p>
            <span
              className={`mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${aqi.colors.badge} ${aqi.colors.text}`}
            >
              <span className={`size-1.5 rounded-full ${aqi.colors.dot}`} aria-hidden="true" />
              <span>{aqi.shortLabel}</span>
              <span className="font-bold opacity-80">· AQI {aqiScore}</span>
            </span>
            <p className="mt-1.5 text-xs text-slate-600">
              Forecast <span className="font-semibold text-slate-800">{formatPm25(window.mean_predicted_value_ug_m3)} µg/m³</span> · Upper{" "}
              {formatPm25(window.mean_upper_bound_ug_m3)}
            </p>
          </li>
        );
      })}
    </ol>
  );
}

function PlannerExplanation() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section className="mt-8" aria-label="Calculation methodology">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="size-4 text-teal-700" aria-hidden="true" />
          <h3 className="text-sm font-semibold text-slate-900">
            How these values are calculated
          </h3>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 transition hover:text-teal-900 hover:underline underline-offset-2"
          aria-expanded={isOpen}
        >
          <span>{isOpen ? "Hide calculation" : "View calculation steps"}</span>
          <ChevronDown
            className={`size-3.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </button>
      </div>

      {isOpen && (
        <div className="mt-6 max-w-3xl space-y-7 text-xs text-slate-700">
          {/* Step 1 */}
          <div className="relative pl-7 before:absolute before:left-2 before:top-2.5 before:bottom-0 before:w-px before:bg-slate-200">
            <span className="absolute left-0 top-0.5 flex size-4 items-center justify-center rounded-full bg-teal-700 text-[10px] font-bold text-white">
              1
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Step 1</span>
              <span className="text-slate-400">·</span>
              <h4 className="text-sm font-semibold text-slate-900">Time Window Selection</h4>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
              The model identifies all continuous hourly blocks matching your chosen activity duration (e.g. <strong>5:00 pm – 7:00 pm = 2 continuous hours</strong>).
            </p>
          </div>

          {/* Step 2 */}
          <div className="relative pl-7 before:absolute before:left-2 before:top-2.5 before:bottom-0 before:w-px before:bg-slate-200">
            <span className="absolute left-0 top-0.5 flex size-4 items-center justify-center rounded-full bg-teal-700 text-[10px] font-bold text-white">
              2
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Step 2</span>
              <span className="text-slate-400">·</span>
              <h4 className="text-sm font-semibold text-slate-900">Forecast PM2.5 (Hourly Average)</h4>
            </div>
            <p className="mt-1.5 text-xs text-slate-600">
              Calculates the arithmetic average of hourly PM2.5 predictions across the window:
            </p>
            <div className="mt-2.5 space-y-2 font-mono text-xs text-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">Mean =</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">Hour₁ + Hour₂</span>
                  <span className="pt-0.5">2</span>
                </span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <span>=</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">29.9 + 32.2</span>
                  <span className="pt-0.5">2</span>
                </span>
                <span>= <strong className="text-slate-950 font-bold">31.0 µg/m³</strong></span>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative pl-7 before:absolute before:left-2 before:top-2.5 before:bottom-0 before:w-px before:bg-slate-200">
            <span className="absolute left-0 top-0.5 flex size-4 items-center justify-center rounded-full bg-teal-700 text-[10px] font-bold text-white">
              3
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Step 3</span>
              <span className="text-slate-400">·</span>
              <h4 className="text-sm font-semibold text-slate-900">Upper Range (95% Confidence Bound)</h4>
            </div>
            <p className="mt-1.5 text-xs text-slate-600">
              Calculates the average of the model's 95% worst-case upper uncertainty estimates:
            </p>
            <div className="mt-2.5 space-y-2 font-mono text-xs text-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">Upper =</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">Upper₁ + Upper₂</span>
                  <span className="pt-0.5">2</span>
                </span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <span>=</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">75.5 + 77.8</span>
                  <span className="pt-0.5">2</span>
                </span>
                <span>= <strong className="text-slate-950 font-bold">76.6 µg/m³</strong></span>
              </div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="relative pl-7 before:absolute before:left-2 before:top-2.5 before:bottom-0 before:w-px before:bg-slate-200">
            <span className="absolute left-0 top-0.5 flex size-4 items-center justify-center rounded-full bg-amber-600 text-[10px] font-bold text-white">
              4
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Step 4</span>
              <span className="text-slate-400">·</span>
              <h4 className="text-sm font-semibold text-slate-900">US EPA 2024 Formula (AQI Conversion)</h4>
            </div>
            <p className="mt-1.5 text-xs text-slate-600">
              Maps PM2.5 to the standard 0–500 index using linear interpolation within the matching breakpoint band:
            </p>
            <div className="mt-2.5 space-y-2 font-mono text-xs text-slate-800">
              <div className="flex items-center gap-2 overflow-x-auto pb-0.5">
                <span className="font-semibold text-slate-900">AQI =</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">I<sub>high</sub> − I<sub>low</sub></span>
                  <span className="pt-0.5">C<sub>high</sub> − C<sub>low</sub></span>
                </span>
                <span>× (C − C<sub>low</sub>) + I<sub>low</sub></span>
              </div>
              <div className="flex items-center gap-2 overflow-x-auto text-slate-600">
                <span>=</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">100 − 51</span>
                  <span className="pt-0.5">35.4 − 9.1</span>
                </span>
                <span>× (31.0 − 9.1) + 51</span>
              </div>
              <div className="flex items-center gap-2 flex-wrap text-slate-600">
                <span>=</span>
                <span className="inline-flex flex-col items-center">
                  <span className="border-b border-slate-400 px-1.5 pb-0.5">49</span>
                  <span className="pt-0.5">26.3</span>
                </span>
                <span>× 21.9 + 51</span>
                <span>= 40.8 + 51</span>
                <span>= <strong className="rounded bg-amber-50 px-2 py-0.5 font-bold text-amber-900 border border-amber-200/80">AQI 92 (Moderate)</strong></span>
              </div>
            </div>
          </div>

          {/* Step 5 */}
          <div className="relative pl-7">
            <span className="absolute left-0 top-0.5 flex size-4 items-center justify-center rounded-full bg-teal-700 text-[10px] font-bold text-white">
              5
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Step 5</span>
              <span className="text-slate-400">·</span>
              <h4 className="text-sm font-semibold text-slate-900">Final Ranking (Option 1 [BEST])</h4>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
              All candidate windows across the 24-hour horizon are sorted in ascending order of predicted PM2.5. The window with the lowest pollution (31.0 µg/m³) is selected as <strong>Option 1 [BEST]</strong>.
            </p>
          </div>
        </div>
      )}
    </section>
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
        <div>
          <h3 className="font-semibold text-slate-900">
            Best available times for {formatSelectedDate(plan.date)} · {plan.duration_minutes / 60}-hour activity
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
          </p>
        </div>
        <div className="inline-flex w-fit rounded-lg bg-slate-100 p-1" role="tablist" aria-label="Result display mode">
          {modes.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={view === id}
              className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition ${view === id ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"
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
  const todayDate = newDelhiDate(0);
  const tomorrowDate = newDelhiDate(1);
  const [date, setDate] = useState(todayDate);
  const [duration, setDuration] = useState(60);

  const {
    data: plan,
    isPending,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["activityPlan", date, duration],
    queryFn: () => api.activityPlan(date, duration),
    staleTime: 60_000,
  });

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <section className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700 sm:text-sm">Outdoor planning</p>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl lg:text-4xl">Activity Planner</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:mt-3 sm:text-base sm:leading-7">
          Find the cleanest air windows for outdoor exercise, errands, and commuting in New Delhi based on hourly PM2.5 forecasts.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mt-8 sm:p-6" aria-labelledby="planner-heading">
        <div>
          <h2 id="planner-heading" className="text-base font-semibold text-slate-950 sm:text-lg">
            Plan your outdoor activity
          </h2>
          <p className="mt-1 text-xs leading-5 text-slate-600 sm:text-sm sm:leading-6">
            Select your intended date and activity duration to calculate optimal windows.
          </p>
        </div>

        <form
          className="mt-5 grid gap-3.5 sm:mt-6 sm:gap-4 md:grid-cols-[1.2fr_1fr_auto] md:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            refetch();
          }}
        >
          <div className="grid gap-1.5 text-xs font-medium text-slate-800 sm:gap-2 sm:text-sm">
            <div className="flex items-center justify-between">
              <label htmlFor="planner-date" className="flex items-center gap-1.5 font-medium text-slate-800">
                <CalendarDays className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                Date
              </label>
              <div className="inline-flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="Quick date selector">
                <button
                  type="button"
                  onClick={() => setDate(todayDate)}
                  className={`rounded-md px-2 py-0.5 text-xs font-semibold transition ${date === todayDate
                      ? "bg-white text-teal-800 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                    }`}
                >
                  Today
                </button>
                <button
                  type="button"
                  onClick={() => setDate(tomorrowDate)}
                  className={`rounded-md px-2 py-0.5 text-xs font-semibold transition ${date === tomorrowDate
                      ? "bg-white text-teal-800 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                    }`}
                >
                  Tomorrow
                </button>
              </div>
            </div>
            <input
              id="planner-date"
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-1 focus:ring-teal-700 sm:py-2"
              type="date"
              value={date}
              min={todayDate}
              max={tomorrowDate}
              onChange={(event) => setDate(event.target.value)}
              required
            />
          </div>

          <div className="grid gap-1.5 text-xs font-medium text-slate-800 sm:gap-2 sm:text-sm">
            <label htmlFor="planner-duration" className="flex items-center gap-1.5 font-medium text-slate-800">
              <Clock3 className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
              Duration
            </label>
            <div className="relative">
              <select
                id="planner-duration"
                className="w-full appearance-none rounded-lg border border-slate-300 bg-white py-1.5 pl-3 pr-8 text-sm text-slate-900 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-1 focus:ring-teal-700 sm:py-2 sm:pl-3.5 sm:pr-10"
                value={duration}
                onChange={(event) => setDuration(Number(event.target.value))}
              >
                {DURATIONS.map((minutes) => (
                  <option key={minutes} value={minutes}>
                    {minutes / 60} {minutes === 60 ? "hour" : "hours"}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-3.5 -translate-y-1/2 text-slate-500 sm:right-3.5 sm:size-4" aria-hidden="true" />
            </div>
          </div>

          <button
            className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:px-5 sm:py-2 sm:text-sm"
            type="submit"
            disabled={isPending || isFetching}
          >
            {isFetching ? "Updating times…" : "Refresh times"}
          </button>
        </form>

        <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-500"></div>

        {isPending && (
          <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-slate-100 bg-slate-50/50 py-12 text-center" aria-live="polite">
            <div className="size-6 animate-spin rounded-full border-2 border-teal-700 border-t-transparent" />
            <p className="mt-3 text-sm font-medium text-slate-700">Finding optimal outdoor windows…</p>
            <p className="mt-1 text-xs text-slate-500">Evaluating hourly PM2.5 forecasts for New Delhi</p>
          </div>
        )}

        {isError && !isPending && (
          <div className="mt-5">
            <UnavailablePanel
              title="No complete plan is available"
              message={
                error instanceof Error && error.message
                  ? error.message
                  : "No continuous forecast window is available for this combination. Try switching between Today and Tomorrow or selecting a shorter duration."
              }
            />
          </div>
        )}

        {plan && !isPending && <PlanResults plan={plan} />}
      </section>

      {plan && !isPending && <PlannerExplanation />}
    </main>
  );
}
