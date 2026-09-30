import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export const ONE_MINUTE = 60_000;
export const FIVE_MINUTES = 5 * 60_000;

export function useServiceStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: ONE_MINUTE,
    staleTime: ONE_MINUTE,
  });
}

export function useCurrentConditions() {
  return useQuery({
    queryKey: ["conditions"],
    queryFn: api.currentConditions,
    refetchInterval: FIVE_MINUTES,
    staleTime: FIVE_MINUTES,
  });
}

export function useLatestForecasts() {
  return useQuery({
    queryKey: ["forecasts"],
    queryFn: api.latestForecasts,
    refetchInterval: FIVE_MINUTES,
    staleTime: FIVE_MINUTES,
  });
}

export function useForecastHistory(hours: number = 72) {
  return useQuery({
    queryKey: ["history", hours],
    queryFn: () => api.forecastHistory(hours),
    refetchInterval: FIVE_MINUTES,
    staleTime: FIVE_MINUTES,
  });
}

export function useAlertPreference(browserId: string) {
  return useQuery({
    queryKey: ["alert-preference", browserId],
    queryFn: () => api.alertPreference(browserId),
    staleTime: FIVE_MINUTES,
  });
}

export function useSaveAlertPreference(browserId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ threshold, enabled }: { threshold: number; enabled: boolean }) =>
      api.saveAlertPreference(browserId, threshold, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert-preference", browserId] }),
  });
}

export function useActivityPlan() {
  return useMutation({
    mutationFn: ({ date, durationMinutes }: { date: string; durationMinutes: number }) =>
      api.activityPlan(date, durationMinutes),
  });
}
