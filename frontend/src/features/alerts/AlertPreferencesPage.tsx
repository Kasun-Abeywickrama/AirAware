import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2, Info, SlidersHorizontal } from "lucide-react";
import { api } from "../../api/client";
import { formatDateTime } from "../../utils/format";
import { LoadingBlock, UnavailablePanel } from "../../components/common/DataState";
import { getBrowserId } from "../../utils/browserId";
import { InfoTooltip } from "../../components/common/InfoTooltip";
import {
  getNotificationPermission,
  requestNotificationPermission,
  sendTestNotification,
} from "../../utils/notifications";

const QUICK_THRESHOLDS: Array<{ value: number; label: string; desc: string }> = [
  { value: 35, label: "35 µg/m³", desc: "Moderate limit" },
  { value: 55, label: "55 µg/m³", desc: "Sensitive limit" },
  { value: 125, label: "125 µg/m³", desc: "Unhealthy limit" },
];

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Your preference could not be saved. Please try again.";
}

export function AlertPreferencesPage() {
  const [browserId] = useState(getBrowserId);
  const [threshold, setThreshold] = useState(55);
  const [enabled, setEnabled] = useState(true);
  const [initialised, setInitialised] = useState(false);
  const [permission, setPermission] = useState(getNotificationPermission);
  const [sentTest, setSentTest] = useState(false);
  const queryClient = useQueryClient();
  const preference = useQuery({ queryKey: ["alert-preference", browserId], queryFn: () => api.alertPreference(browserId), staleTime: 5 * 60_000 });
  const savePreference = useMutation({
    mutationFn: () => api.saveAlertPreference(browserId, threshold, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert-preference", browserId] }),
  });

  useEffect(() => {
    if (!preference.data || initialised) return;
    if (preference.data.status === "configured" && preference.data.threshold_ug_m3 !== null) {
      setThreshold(preference.data.threshold_ug_m3);
      setEnabled(preference.data.enabled);
    } else {
      // First-time configuration defaults to active so alerts work immediately
      setEnabled(true);
    }
    setInitialised(true);
  }, [initialised, preference.data]);

  const isValidThreshold = Number.isFinite(threshold) && threshold > 0 && threshold <= 2000;

  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <section className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700 sm:text-sm">Alert preferences</p>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl lg:text-4xl">Choose your PM2.5 threshold.</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 sm:mt-3 sm:text-base sm:leading-7">
          Set a personal PM2.5 threshold for this browser. You can update or turn it off anytime.
        </p>
      </section>

      {preference.isLoading ? (
        <div className="mt-6 sm:mt-8">
          <LoadingBlock label="Loading alert preferences" />
        </div>
      ) : preference.isError ? (
        <div className="mt-6 sm:mt-8">
          <UnavailablePanel title="Alert preferences are unavailable" message={errorMessage(preference.error)} />
        </div>
      ) : (
        <section id="tour-alerts-hero" className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mt-8 sm:p-6" aria-labelledby="preference-form-heading">
          <div>
            <h2 id="preference-form-heading" className="text-base font-semibold text-slate-950 sm:text-lg">
              Your preference
            </h2>
            <p className="mt-1 text-xs leading-5 text-slate-600 sm:text-sm sm:leading-6">Choose the PM2.5 value you want to save as your reference.</p>
          </div>

          <form
            className="mt-6 grid gap-4 sm:gap-5 lg:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (isValidThreshold) savePreference.mutate();
            }}
          >
            <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5" aria-label="PM2.5 threshold setting">
              <label className="grid gap-2 text-xs font-semibold text-slate-800 sm:gap-3 sm:text-sm" htmlFor="threshold">
                <span className="flex items-center gap-2">
                  <SlidersHorizontal className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                  <span>PM2.5 threshold</span>
                  <InfoTooltip
                    title="Alert Trigger Level"
                    content="When the live PM2.5 level exceeds this value, an alert notification and banner will be triggered."
                  />
                </span>
                <span className="flex items-center gap-2">
                  <input
                    id="threshold"
                    className="w-36 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xl font-bold text-slate-950 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-100 sm:w-40 sm:px-4 sm:py-3 sm:text-2xl"
                    type="number"
                    min="1"
                    max="2000"
                    step="1"
                    value={threshold}
                    onChange={(event) => setThreshold(event.target.valueAsNumber)}
                    required
                  />
                  <span className="text-xs font-medium text-slate-600 sm:text-sm">µg/m³</span>
                </span>
              </label>
              <div className="mt-5 sm:mt-6">
                <div className="flex items-center gap-1.5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    EPA Reference Thresholds
                  </p>
                  <InfoTooltip
                    title="Standard EPA Limits"
                    content="Quick presets aligned with US EPA health categories: Moderate (35 µg/m³), Sensitive (55 µg/m³), and Unhealthy (125 µg/m³)."
                  />
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {QUICK_THRESHOLDS.map(({ value, label, desc }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setThreshold(value)}
                      className={`flex flex-col items-center justify-center rounded-lg border p-2 text-center transition ${
                        threshold === value
                          ? "border-teal-700 bg-teal-700 text-white shadow-xs"
                          : "border-slate-300 bg-white text-slate-700 hover:border-teal-500"
                      }`}
                    >
                      <span className="text-xs font-bold">{label}</span>
                      <span
                        className={`text-[10px] ${
                          threshold === value ? "text-teal-100" : "text-slate-500"
                        }`}
                      >
                        {desc}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
              {!isValidThreshold && <p className="mt-4 text-sm font-medium text-rose-700">Enter a number from 1 to 2,000 µg/m³.</p>}
            </section>

            <section className="flex flex-col rounded-xl border border-slate-200 p-4 sm:p-6" aria-label="Preference activation setting">
              <label className="flex cursor-pointer items-center justify-between gap-4 sm:gap-5">
                <div>
                  <span className="block text-sm font-semibold text-slate-900 sm:text-base">Keep this preference active</span>
                  <span className="mt-0.5 block text-xs leading-5 text-slate-600 sm:mt-1 sm:text-sm sm:leading-6">Turn it off without deleting your saved threshold.</span>
                </div>
                <span className="relative inline-flex shrink-0">
                  <input
                    className="peer sr-only"
                    type="checkbox"
                    checked={enabled}
                    onChange={(event) => setEnabled(event.target.checked)}
                  />
                  <span
                    className="h-6 w-11 sm:h-7 sm:w-12 rounded-full bg-slate-300 transition peer-checked:bg-teal-700 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-teal-700"
                    aria-hidden="true"
                  />
                  <span className="pointer-events-none absolute left-1 top-1 size-4 sm:size-5 rounded-full bg-white shadow-sm transition peer-checked:translate-x-5" aria-hidden="true" />
                </span>
              </label>
              <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-5 sm:gap-4 sm:pt-7">
                <button
                  type="submit"
                  disabled={!isValidThreshold || savePreference.isPending}
                  className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:px-5 sm:py-3 sm:text-sm"
                >
                  {savePreference.isPending ? "Saving…" : "Save preference"}
                </button>
                {savePreference.isSuccess && (
                  <p className="inline-flex items-center gap-1.5 text-xs font-medium text-teal-800 sm:text-sm">
                    <CheckCircle2 className="size-3.5 text-teal-700 sm:size-4" aria-hidden="true" />
                    Saved{preference.data?.updated_at ? ` · ${formatDateTime(preference.data.updated_at)}` : ""}
                  </p>
                )}
              </div>
            </section>
            {savePreference.isError && (
              <p className="text-xs sm:text-sm font-medium text-rose-700 lg:col-span-2" role="alert">
                {errorMessage(savePreference.error)}
              </p>
            )}
          </form>
        </section>
      )}

      {/* Desktop / Browser Notifications Card */}
      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6" aria-labelledby="desktop-alerts-heading">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <div className="flex items-start gap-2.5 sm:gap-3">
            <div className="rounded-xl bg-teal-50 p-2 text-teal-700 sm:p-2.5">
              <Bell className="size-4 sm:size-5" aria-hidden="true" />
            </div>
            <div>
              <h2 id="desktop-alerts-heading" className="text-base font-semibold text-slate-950 sm:text-lg">
                Desktop Notifications
              </h2>
              <p className="mt-0.5 text-xs leading-5 text-slate-600 sm:mt-1 sm:text-sm sm:leading-6">
                Receive browser alerts when PM2.5 crosses your threshold, even while browsing other tabs.
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-3 self-start sm:self-center">
            {permission === "granted" ? (
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200">
                  <CheckCircle2 className="size-3.5" aria-hidden="true" />
                  Notifications Active
                </span>
                <button
                  type="button"
                  onClick={() => {
                    sendTestNotification();
                    setSentTest(true);
                    setTimeout(() => setSentTest(false), 2500);
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-semibold shadow-2xs transition ${
                    sentTest
                      ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                      : "border-slate-300 bg-white text-slate-700 hover:border-teal-600 hover:text-teal-800"
                  }`}
                >
                  {sentTest ? "✓ Alert sent!" : "Test alert"}
                </button>
              </div>
            ) : permission === "denied" ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800 ring-1 ring-amber-200">
                Blocked in browser settings
              </span>
            ) : permission === "unsupported" ? (
              <span className="text-xs text-slate-500">Not supported by this browser</span>
            ) : (
              <button
                type="button"
                onClick={async () => {
                  const res = await requestNotificationPermission();
                  setPermission(res);
                  if (res === "granted") {
                    sendTestNotification();
                  }
                }}
                className="rounded-lg bg-teal-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-teal-800"
              >
                Enable browser alerts
              </button>
            )}
          </div>
        </div>
      </section>

      <aside className="mt-6 rounded-2xl border border-teal-100 bg-teal-50 p-5 text-sm leading-6 text-slate-700">
        <div className="flex gap-3">
          <Info className="mt-0.5 size-5 shrink-0 text-teal-700" aria-hidden="true" />
          <div>
            <p className="font-semibold text-slate-800">Private & Real-Time Alerts</p>
            <p className="mt-1">
              Your preference is saved privately for this browser. When live PM2.5 measurements or upcoming forecasts exceed this threshold, AirAware alerts you immediately on your dashboard.
            </p>
          </div>
        </div>
      </aside>
    </main>
  );
}
