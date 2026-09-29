import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, CheckCircle2, Info, SlidersHorizontal } from "lucide-react";
import { api } from "../api/client";
import { formatDateTime } from "../lib/format";
import { LoadingBlock, UnavailablePanel } from "./DataState";

const BROWSER_ID_KEY = "airaware-browser-id";
const QUICK_THRESHOLDS = [50, 100, 150];

function anonymousBrowserId() {
  const savedId = window.localStorage.getItem(BROWSER_ID_KEY);
  if (savedId) return savedId;
  const id = crypto.randomUUID();
  window.localStorage.setItem(BROWSER_ID_KEY, id);
  return id;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Your preference could not be saved. Please try again.";
}

export function AlertPreferencesPage() {
  const [browserId] = useState(anonymousBrowserId);
  const [threshold, setThreshold] = useState(70);
  const [enabled, setEnabled] = useState(true);
  const [initialised, setInitialised] = useState(false);
  const queryClient = useQueryClient();
  const preference = useQuery({ queryKey: ["alert-preference", browserId], queryFn: () => api.alertPreference(browserId), staleTime: 5 * 60_000 });
  const savePreference = useMutation({
    mutationFn: () => api.saveAlertPreference(browserId, threshold, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert-preference", browserId] }),
  });

  useEffect(() => {
    if (!preference.data || initialised) return;
    if (preference.data.threshold_ug_m3 !== null) setThreshold(preference.data.threshold_ug_m3);
    setEnabled(preference.data.enabled);
    setInitialised(true);
  }, [initialised, preference.data]);

  const isValidThreshold = Number.isFinite(threshold) && threshold > 0 && threshold <= 2000;

  return <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
    <section className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Alert preferences</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Choose your PM2.5 threshold.</h1>
      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">Set a personal PM2.5 threshold for this browser. You can update or turn it off anytime.</p>
    </section>

    {preference.isLoading ? <div className="mt-8"><LoadingBlock label="Loading alert preferences" /></div> : preference.isError ? <div className="mt-8"><UnavailablePanel title="Alert preferences are unavailable" message={errorMessage(preference.error)} /></div> : <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7" aria-labelledby="preference-form-heading">
      <div className="flex items-start gap-3"><div className="rounded-xl bg-teal-50 p-2.5 text-teal-700"><BellRing className="size-5" aria-hidden="true" /></div><div><h2 id="preference-form-heading" className="text-lg font-semibold text-slate-950">Your preference</h2><p className="mt-1 text-sm leading-6 text-slate-600">Choose the PM2.5 value you want to save as your reference.</p></div></div>

      <form className="mt-7 grid gap-5 lg:grid-cols-2" onSubmit={(event) => { event.preventDefault(); if (isValidThreshold) savePreference.mutate(); }}>
        <section className="rounded-xl border border-slate-200 bg-slate-50 p-5 sm:p-6" aria-label="PM2.5 threshold setting">
          <label className="grid gap-3 text-sm font-semibold text-slate-800" htmlFor="threshold"><span className="flex items-center gap-2"><SlidersHorizontal className="size-4 text-teal-700" aria-hidden="true" />PM2.5 threshold</span><span className="flex items-center gap-2"><input id="threshold" className="w-40 rounded-lg border border-slate-300 bg-white px-4 py-3 text-2xl font-bold text-slate-950 shadow-sm focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-100" type="number" min="1" max="2000" step="1" value={threshold} onChange={(event) => setThreshold(event.target.valueAsNumber)} required /><span className="text-sm font-medium text-slate-600">µg/m³</span></span></label>
          <div className="mt-6"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Quick values</p><div className="mt-2 flex gap-2">{QUICK_THRESHOLDS.map((value) => <button key={value} type="button" onClick={() => setThreshold(value)} className={`rounded-lg border px-4 py-2 text-sm font-semibold transition ${threshold === value ? "border-teal-700 bg-teal-700 text-white" : "border-slate-300 bg-white text-slate-700 hover:border-teal-500"}`}>{value}</button>)}</div></div>
          {!isValidThreshold && <p className="mt-4 text-sm font-medium text-rose-700">Enter a number from 1 to 2,000 µg/m³.</p>}
        </section>

        <section className="flex flex-col rounded-xl border border-slate-200 p-5 sm:p-6" aria-label="Preference activation setting">
          <label className="flex cursor-pointer items-center justify-between gap-5"><span><span className="block font-semibold text-slate-900">Keep this preference active</span><span className="mt-1 block text-sm leading-6 text-slate-600">Turn it off without deleting your saved threshold.</span></span><span className="relative inline-flex shrink-0"><input className="peer sr-only" type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} /><span className="h-7 w-12 rounded-full bg-slate-300 transition peer-checked:bg-teal-700 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-teal-700" aria-hidden="true" /><span className="pointer-events-none absolute left-1 top-1 size-5 rounded-full bg-white shadow-sm transition peer-checked:translate-x-5" aria-hidden="true" /></span></label>
          <div className="mt-auto pt-7"><button type="submit" disabled={!isValidThreshold || savePreference.isPending} className="rounded-lg bg-teal-700 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400">{savePreference.isPending ? "Saving…" : "Save preference"}</button>{savePreference.isSuccess && <p className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-teal-800"><CheckCircle2 className="size-4" aria-hidden="true" />Saved{preference.data?.updated_at ? ` · ${formatDateTime(preference.data.updated_at)}` : ""}</p>}</div>
        </section>
        {savePreference.isError && <p className="text-sm font-medium text-rose-700 lg:col-span-2" role="alert">{errorMessage(savePreference.error)}</p>}
      </form>
    </section>}

    <aside className="mt-6 rounded-2xl border border-teal-100 bg-teal-50 p-5 text-sm leading-6 text-slate-700"><div className="flex gap-3"><Info className="mt-0.5 size-5 shrink-0 text-teal-700" aria-hidden="true" /><div><p className="font-semibold text-slate-800">Your privacy</p><p className="mt-1">Your preference is saved privately for this browser.</p></div></div></aside>
  </main>;
}
