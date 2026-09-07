import { Classification, EmailRecord } from "../types";

const order: Classification[] = [
  "Enquiry",
  "Complaint",
  "Order Update",
  "Support Request",
  "Promotional",
  "Spam",
];

const barColor: Record<Classification, string> = {
  Enquiry: "bg-blue-500",
  Complaint: "bg-red-500",
  "Order Update": "bg-amber-500",
  "Support Request": "bg-purple-500",
  Promotional: "bg-slate-400",
  Spam: "bg-rose-500",
};

export function ClassificationBreakdown({ emails }: { emails: EmailRecord[] }) {
  const total = emails.length || 1;
  const counts = order.map((classification) => ({
    classification,
    count: emails.filter((e) => e.classification === classification).length,
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
      <p className="text-sm font-medium text-slate-500">Classification Breakdown</p>
      <div className="mt-4 space-y-3">
        {counts.map(({ classification, count }) => (
          <div key={classification} className="flex items-center gap-3">
            <span className="w-32 shrink-0 text-xs text-slate-600">{classification}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${barColor[classification]}`}
                style={{ width: `${(count / total) * 100}%` }}
              />
            </div>
            <span className="w-6 shrink-0 text-right text-xs font-medium text-slate-700">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
