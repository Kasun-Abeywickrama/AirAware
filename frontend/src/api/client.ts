import type { ActivityPlan, AlertPreference, CurrentConditions, ForecastHistory, LatestForecasts, SystemStatus } from "./types";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  const data = (await response.json()) as T & { message?: string };
  if (!response.ok) {
    throw new ApiError(data.message ?? "Data is temporarily unavailable.", response.status);
  }
  return data;
}

async function sendJson<T>(path: string, body: object): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await response.json()) as T & { message?: string };
  if (!response.ok) {
    throw new ApiError(data.message ?? "Data is temporarily unavailable.", response.status);
  }
  return data;
}

async function putJson<T>(path: string, body: object): Promise<T> {
  const response = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await response.json()) as T & { message?: string };
  if (!response.ok) {
    throw new ApiError(data.message ?? "Data is temporarily unavailable.", response.status);
  }
  return data;
}

export const api = {
  status: () => getJson<SystemStatus>("/api/v1/status"),
  currentConditions: () => getJson<CurrentConditions>("/api/v1/current-conditions"),
  latestForecasts: () => getJson<LatestForecasts>("/api/v1/forecasts/latest"),
  forecastHistory: (hours = 72) => getJson<ForecastHistory>(`/api/v1/forecasts/history?hours=${hours}`),
  activityPlan: (date: string, durationMinutes: number) =>
    sendJson<ActivityPlan>("/api/v1/activity-plans", { date, duration_minutes: durationMinutes }),
  alertPreference: (browserId: string) => getJson<AlertPreference>(`/api/v1/alert-preferences/${browserId}`),
  saveAlertPreference: (browserId: string, thresholdUgM3: number, enabled: boolean) =>
    putJson<AlertPreference>(`/api/v1/alert-preferences/${browserId}`, { threshold_ug_m3: thresholdUgM3, enabled }),
};
