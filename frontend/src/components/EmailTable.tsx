import clsx from "clsx";
import { ChevronRight } from "lucide-react";
import { EmailRecord } from "../types";
import { ClassificationBadge, StatusBadge } from "./Badges";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface EmailTableProps {
  emails: EmailRecord[];
  selectedId: string | null;
  onSelect: (email: EmailRecord) => void;
}

export function EmailTable({ emails, selectedId, onSelect }: EmailTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Subject</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Sender</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Classification</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Received</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {emails.map((email) => (
            <tr
              key={email.id}
              onClick={() => onSelect(email)}
              className={clsx(
                "cursor-pointer transition-colors hover:bg-slate-50",
                selectedId === email.id && "bg-brand-50/60 hover:bg-brand-50"
              )}
            >
              <td className="max-w-xs px-4 py-3">
                <p className="truncate text-sm font-medium text-slate-900">{email.subject}</p>
                <p className="truncate text-xs text-slate-400">{email.snippet}</p>
              </td>
              <td className="px-4 py-3">
                <p className="text-sm text-slate-700">{email.sender}</p>
                <p className="text-xs text-slate-400">{email.senderEmail}</p>
              </td>
              <td className="px-4 py-3">
                <ClassificationBadge classification={email.classification} />
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={email.status} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-500">{formatTime(email.receivedAt)}</td>
              <td className="px-4 py-3 text-right">
                <ChevronRight className="h-4 w-4 text-slate-300" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
