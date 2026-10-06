import type { ReactNode } from "react";
import { AlertCircle, LoaderCircle } from "lucide-react";

export function LoadingBlock({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6" aria-label={label}>
      <div className="h-4 w-28 rounded bg-slate-200" />
      <div className="mt-5 h-10 w-40 rounded bg-slate-100" />
      <div className="mt-4 h-4 w-52 rounded bg-slate-100" />
    </div>
  );
}

export function UnavailablePanel({ title, message, children }: { title: string; message: string; children?: ReactNode }) {
  return (
    <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-slate-800" aria-live="polite">
      <div className="flex gap-3">
        <AlertCircle className="mt-0.5 size-5 shrink-0 text-amber-700" aria-hidden="true" />
        <div>
          <h2 className="font-semibold">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">{message}</p>
          {children}
        </div>
      </div>
    </section>
  );
}

export function RefreshingLabel() {
  return <span className="inline-flex items-center gap-1 text-xs text-slate-500"><LoaderCircle className="size-3 animate-spin" /> Refreshing</span>;
}
