import { CheckCircle2, CircleAlert, CircleX } from "lucide-react";
import type { Availability } from "../../api/types";

const labels: Record<Availability | "checking", string> = {
  available: "Live data available",
  limited: "Limited service",
  unavailable: "Data unavailable",
  not_started: "Not started",
  checking: "Checking service",
};

export function StatusBadge({ status }: { status: Availability | "checking" }) {
  const style = status === "available"
    ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
    : status === "limited" || status === "checking"
      ? "bg-amber-50 text-amber-800 ring-amber-200"
      : "bg-rose-50 text-rose-800 ring-rose-200";
  const Icon = status === "available" ? CheckCircle2 : status === "limited" || status === "checking" ? CircleAlert : CircleX;
  return <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ring-1 ${style}`}><Icon className="size-4" aria-hidden="true" />{labels[status]}</span>;
}
