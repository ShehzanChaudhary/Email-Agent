import { Brain, Mail, Send, Sparkles, X } from "lucide-react";
import { EmailRecord } from "../types";
import { ClassificationBadge, StatusBadge } from "./Badges";

function formatFull(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface DetailPanelProps {
  email: EmailRecord | null;
  onClose: () => void;
}

export function DetailPanel({ email, onClose }: DetailPanelProps) {
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-900/20 transition-opacity ${
          email ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
      />
      <aside
        className={`fixed right-0 top-0 z-40 h-full w-full max-w-lg transform overflow-y-auto border-l border-slate-200 bg-white shadow-xl transition-transform duration-300 ${
          email ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {email && (
          <div className="flex h-full flex-col">
            <div className="sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h2 className="truncate text-base font-semibold text-slate-900">{email.subject}</h2>
                  <p className="mt-0.5 text-sm text-slate-500">
                    {email.sender} &lt;{email.senderEmail}&gt;
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <ClassificationBadge classification={email.classification} />
                <StatusBadge status={email.status} />
                <span className="text-xs text-slate-400">
                  Confidence: <span className="font-medium text-slate-600">{Math.round(email.confidence * 100)}%</span>
                </span>
                <span className="text-xs text-slate-400">{formatFull(email.receivedAt)}</span>
              </div>
            </div>

            <div className="flex-1 space-y-6 px-6 py-5">
              <section>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <Mail className="h-4 w-4 text-slate-400" />
                  Original Email
                </div>
                <div className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  {email.body}
                </div>
              </section>

              <section>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <Brain className="h-4 w-4 text-slate-400" />
                  Agent Reasoning
                </div>
                <ol className="space-y-3">
                  {email.thoughtProcess.map((step) => (
                    <li key={step.step} className="rounded-lg border border-slate-200 p-3">
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-brand-600">
                        Step {step.step}
                      </p>
                      <p className="text-sm text-slate-700">
                        <span className="font-medium text-slate-500">Observation: </span>
                        {step.observation}
                      </p>
                      <p className="mt-1.5 text-sm text-slate-700">
                        <span className="font-medium text-slate-500">Thought: </span>
                        {step.thought}
                      </p>
                      <p className="mt-1.5 text-sm text-slate-700">
                        <span className="font-medium text-slate-500">Action: </span>
                        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-700">{step.action}</code>
                      </p>
                    </li>
                  ))}
                </ol>
              </section>

              <section>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <Sparkles className="h-4 w-4 text-slate-400" />
                  Suggested Reply
                </div>
                <div className="whitespace-pre-wrap rounded-lg border border-brand-100 bg-brand-50/50 p-4 text-sm text-slate-700">
                  {email.suggestedReply}
                </div>
              </section>
            </div>

            <div className="sticky bottom-0 border-t border-slate-200 bg-white px-6 py-4">
              <button
                disabled
                title="Backend not connected yet"
                className="flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-lg bg-brand-500/50 px-4 py-2.5 text-sm font-medium text-white"
              >
                <Send className="h-4 w-4" />
                {email.replySent ? "Reply Sent" : "Send Reply"}
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
