import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastHistory } from "../../api/types";
import { formatDateTime, formatPm25 } from "../../utils/format";

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

export function AirQualityChart({ history, expanded = false }: { history: ForecastHistory; expanded?: boolean }) {
  const data = useMemo(() => buildChartData(history), [history]);
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="trend-heading">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h2 id="trend-heading" className="text-lg font-semibold text-slate-950">Recent PM2.5 and forecast</h2>
          <p className="mt-1 text-sm text-slate-600">Observed values are solid. Forecast values and their ranges are shown ahead.</p>
        </div>
        <span className="text-xs font-medium text-slate-500">Last {history.hours} hours</span>
      </div>
      <div className={`mt-6 ${expanded ? "h-96 sm:h-[28rem]" : "h-72"}`} role="img" aria-label="PM2.5 observations and forecast chart">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="timestamp" tickFormatter={formatDateTime} minTickGap={48} tick={{ fill: "#475569", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#475569", fontSize: 11 }} tickFormatter={(value) => `${value} µg/m³`} axisLine={false} tickLine={false} width={76} />
            <Tooltip
              labelFormatter={(value) => formatDateTime(String(value))}
              formatter={(value: number, name) => [`${formatPm25(value)} µg/m³`, name === "observation" ? "Observed" : name === "forecast" ? "Forecast" : name]}
            />
            <Area type="monotone" dataKey="upper" stroke="none" fill="#99f6e4" fillOpacity={0.55} name="Upper range" />
            <Area type="monotone" dataKey="lower" stroke="none" fill="#ffffff" fillOpacity={1} name="Lower range" />
            <Line type="monotone" dataKey="observation" stroke="#0f766e" strokeWidth={2.5} dot={false} name="observation" connectNulls />
            <Line type="monotone" dataKey="forecast" stroke="#2563eb" strokeWidth={2.5} strokeDasharray="6 5" dot={{ r: 3 }} name="forecast" connectNulls />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
