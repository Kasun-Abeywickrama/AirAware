import { useEffect, useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastHistory } from "../../api/types";
import { formatDateTime, formatPm25 } from "../../utils/format";
import { InfoTooltip } from "../../components/common/InfoTooltip";

export interface ChartPoint {
  timestamp: string;
  observation?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
}

export function buildChartData(history: ForecastHistory): ChartPoint[] {
  const points = new Map<string, ChartPoint>();
  history.observations.forEach((item) => points.set(item.observed_at, { timestamp: item.observed_at, observation: item.value_ug_m3 }));
  history.forecasts.forEach((item) => {
    const existing = points.get(item.target_at) ?? { timestamp: item.target_at };
    points.set(item.target_at, { ...existing, forecast: item.predicted_value_ug_m3, lower: item.lower_bound_ug_m3, upper: item.upper_bound_ug_m3 });
  });
  return [...points.values()].sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
}

function formatChartAxisDate(value: string): string {
  const d = new Date(value);
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    hour: "numeric",
    hour12: true,
  }).format(d);
}

function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(() => {
    if (typeof window === "undefined") return true;
    return window.matchMedia("(min-width: 1024px)").matches;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const media = window.matchMedia("(min-width: 1024px)");
    const listener = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);

  return isDesktop;
}

export function AirQualityChart({
  history,
  expanded = false,
  frameless = false,
}: {
  history: ForecastHistory;
  expanded?: boolean;
  frameless?: boolean;
}) {
  const isDesktop = useIsDesktop();
  const data = useMemo(() => buildChartData(history), [history]);
  return (
    <section
      className={
        frameless
          ? "w-full"
          : "rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
      }
      aria-labelledby="trend-heading"
    >
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <h2 id="trend-heading" className="text-base font-semibold text-slate-950 sm:text-lg">Recent PM2.5 and forecast</h2>
            <InfoTooltip
              title="Time-Series Trend"
              content="Solid line shows actual past measurements. Dashed line shows future forecasts with shaded uncertainty range."
            />
          </div>
          <p className="mt-1 text-xs text-slate-600 sm:text-sm">Observed values are solid. Forecast values and their ranges are shown ahead.</p>
        </div>
        <div className="flex items-center justify-between gap-3 text-xs text-slate-500 sm:justify-end">
          {/* Mobile indicator chips */}
          <div className="flex items-center gap-3 text-[11px] font-medium sm:hidden">
            <span className="flex items-center gap-1 text-teal-800">
              <span className="h-0.5 w-3 rounded-full bg-teal-700" aria-hidden="true" />
              Observed
            </span>
            <span className="flex items-center gap-1 text-blue-800">
              <span className="h-0.5 w-3 rounded-full bg-blue-600 border-dashed" aria-hidden="true" />
              Forecast
            </span>
          </div>
          <span className="font-medium">Last {history.hours}h</span>
        </div>
      </div>
      <div className={`mt-4 sm:mt-6 ${expanded ? "h-80 sm:h-[28rem]" : "h-64 sm:h-72"}`} role="img" aria-label="PM2.5 observations and forecast chart">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 16, right: 8, left: isDesktop ? -16 : -8, bottom: isDesktop ? 0 : 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="timestamp" tickFormatter={formatChartAxisDate} minTickGap={32} tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              axisLine={false}
              tickLine={false}
              width={isDesktop ? 75 : 44}
              tick={(props: { x: number; y: number; payload: { value: number } }) => {
                const { x, y, payload } = props;
                if (isDesktop) {
                  return (
                    <text x={x} y={y} dy={4} textAnchor="end" fill="#475569" fontSize={11}>
                      {payload.value} µg/m³
                    </text>
                  );
                }
                return (
                  <text x={x} y={y} textAnchor="end" fill="#475569">
                    <tspan x={x} dy={-3} fontSize={10} fontWeight="600">
                      {payload.value}
                    </tspan>
                    <tspan x={x} dy={11} fontSize={8.5} fill="#64748b">
                      µg/m³
                    </tspan>
                  </text>
                );
              }}
            />
            <Tooltip
              labelFormatter={(value) => formatDateTime(String(value))}
              formatter={(value: number, name) => [`${formatPm25(value)} µg/m³`, name === "observation" ? "Observed" : name === "forecast" ? "Forecast" : name]}
            />
            <Area connectNulls type="monotone" dataKey="upper" stroke="none" fill="#99f6e4" fillOpacity={0.55} name="Upper range" />
            <Area connectNulls type="monotone" dataKey="lower" stroke="none" fill="#ffffff" fillOpacity={1} name="Lower range" />
            <Line
              type="monotone"
              dataKey="observation"
              stroke="#0f766e"
              strokeWidth={isDesktop ? 2.5 : 1.75}
              dot={false}
              name="observation"
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#2563eb"
              strokeWidth={isDesktop ? 2.5 : 1.5}
              strokeDasharray={isDesktop ? "6 5" : "4 3"}
              dot={isDesktop ? { r: 3 } : { r: 1.5, strokeWidth: 1 }}
              name="forecast"
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
