import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock, Inbox, MailWarning, RefreshCw } from "lucide-react";
import { fetchEmails } from "./api";
import { EmailRecord } from "./types";
import { KpiCard } from "./components/KpiCard";
import { ClassificationBreakdown } from "./components/ClassificationBreakdown";
import { EmailTable } from "./components/EmailTable";
import { DetailPanel } from "./components/DetailPanel";

function formatUpdatedAt(date: Date): string {
  return date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function App() {
  const [emails, setEmails] = useState<EmailRecord[]>([]);
  const [selected, setSelected] = useState<EmailRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEmails();
      setEmails(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load emails");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Keep the open detail panel in sync if a refresh changes that email's data.
  useEffect(() => {
    if (!selected) return;
    const updated = emails.find((e) => e.id === selected.id);
    setSelected(updated ?? null);
  }, [emails]); // eslint-disable-line react-hooks/exhaustive-deps

  const stats = useMemo(() => {
    const total = emails.length;
    const processed = emails.filter((e) => e.status === "processed").length;
    const pending = emails.filter((e) => e.status === "pending").length;
    const failed = emails.filter((e) => e.status === "failed").length;
    return { total, processed, pending, failed };
  }, [emails]);

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Email Agent Dashboard</h1>
            <p className="mt-0.5 text-sm text-slate-500">Live view of mailbox activity handled by the agent</p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && !error && (
              <span className="text-xs text-slate-400">Updated {formatUpdatedAt(lastUpdated)}</span>
            )}
            <button
              onClick={load}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-card transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-medium">Couldn't reach the agent backend</p>
              <p className="mt-0.5 text-red-600">{error}. Make sure the API is running (python api.py) and try refreshing.</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Total Emails" value={String(stats.total)} icon={Inbox} accent="brand" />
          <KpiCard label="Processed by Agent" value={String(stats.processed)} icon={CheckCircle2} accent="emerald" />
          <KpiCard label="Pending Review" value={String(stats.pending)} icon={Clock} accent="amber" />
          <KpiCard label="Failed / Escalated" value={String(stats.failed)} icon={MailWarning} accent="red" />
        </div>

        <ClassificationBreakdown emails={emails} />

        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Recent Emails</h2>
            <p className="text-xs text-slate-400">Click a row to view the agent's full reasoning</p>
          </div>
          {!loading && !error && emails.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white py-16 text-center">
              <p className="text-sm font-medium text-slate-600">No processed emails yet</p>
              <p className="mt-1 text-xs text-slate-400">Once the agent processes new mail, it'll show up here.</p>
            </div>
          ) : (
            <EmailTable emails={emails} selectedId={selected?.id ?? null} onSelect={setSelected} />
          )}
        </div>
      </main>

      <DetailPanel email={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
