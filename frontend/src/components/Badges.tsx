import clsx from "clsx";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { Classification, ProcessStatus } from "../types";

const classificationStyles: Record<Classification, string> = {
  Enquiry: "bg-blue-50 text-blue-700 ring-blue-600/20",
  Complaint: "bg-red-50 text-red-700 ring-red-600/20",
  "Order Update": "bg-amber-50 text-amber-700 ring-amber-600/20",
  "Support Request": "bg-purple-50 text-purple-700 ring-purple-600/20",
  Promotional: "bg-slate-100 text-slate-600 ring-slate-500/20",
  Spam: "bg-rose-100 text-rose-700 ring-rose-600/20",
};

export function ClassificationBadge({ classification }: { classification: Classification | "" }) {
  if (!classification) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-400 ring-1 ring-inset ring-slate-300/40">
        Unclassified
      </span>
    );
  }
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        classificationStyles[classification]
      )}
    >
      {classification}
    </span>
  );
}

const statusConfig: Record<ProcessStatus, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  processed: { label: "Processed", className: "bg-emerald-50 text-emerald-700 ring-emerald-600/20", icon: CheckCircle2 },
  pending: { label: "Pending Review", className: "bg-amber-50 text-amber-700 ring-amber-600/20", icon: Clock },
  failed: { label: "Failed", className: "bg-red-50 text-red-700 ring-red-600/20", icon: XCircle },
};

export function StatusBadge({ status }: { status: ProcessStatus }) {
  const { label, className, icon: Icon } = statusConfig[status];
  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset", className)}>
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}
