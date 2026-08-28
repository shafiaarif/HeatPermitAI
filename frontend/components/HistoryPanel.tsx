"use client";

import { useEffect, useState } from "react";
import { api, HistoryResult } from "@/lib/api";

export default function HistoryPanel({ eventId }: { eventId: string }) {
  const [history, setHistory] = useState<HistoryResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .history(eventId)
      .then((res) => {
        if (!cancelled) setHistory(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load history");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  if (loading) {
    return (
      <div className="card p-8 text-center">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-500 text-xs">Loading assessment history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6 bg-red-500/10 border border-red-500/20">
        <p className="text-red-400 text-sm font-semibold mb-1">Failed to load history</p>
        <p className="text-red-400/80 text-xs">{error}</p>
      </div>
    );
  }

  if (!history) return null;

  const hasSafetyPlans = history.safety_plans.length > 0;
  const hasWhatIfs = history.what_if_comparisons.length > 0;

  return (
    <div className="space-y-5">
      {/* Header row with counts */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Safety Plans Generated</p>
          <p className="text-2xl font-bold text-white">{history.safety_plans.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">What-If Comparisons Run</p>
          <p className="text-2xl font-bold text-white">{history.what_if_comparisons.length}</p>
        </div>
      </div>

      {/* Safety Plans list */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-orange-400">📋</span>
          <h2 className="text-sm font-semibold text-white">Safety Plans</h2>
        </div>

        {!hasSafetyPlans ? (
          <p className="text-xs text-gray-600">No safety plans generated yet for this event.</p>
        ) : (
          <div className="space-y-2">
            {history.safety_plans.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between bg-base-800/50 border border-border rounded-lg px-3 py-2.5"
              >
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                  <span className="text-xs font-mono text-gray-500">{p.id.slice(0, 8)}...</span>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(p.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* What-If Comparisons list */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-teal-400">🔄</span>
          <h2 className="text-sm font-semibold text-white">What-If Comparisons</h2>
        </div>

        {!hasWhatIfs ? (
          <p className="text-xs text-gray-600">No what-if comparisons run yet for this event.</p>
        ) : (
          <div className="space-y-2">
            {history.what_if_comparisons.map((w) => {
              const pct = w.exposure_reduction_percent;
              const isReduction = pct !== null && pct > 0;
              const isIncrease = pct !== null && pct < 0;
              return (
                <div
                  key={w.id}
                  className="flex items-center justify-between bg-base-800/50 border border-border rounded-lg px-3 py-2.5"
                >
                  <div className="flex items-center gap-2">
                    {pct !== null ? (
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded ${
                          isReduction
                            ? "bg-green-500/10 text-green-400"
                            : isIncrease
                            ? "bg-red-500/10 text-red-400"
                            : "bg-gray-500/10 text-gray-400"
                        }`}
                      >
                        {isReduction ? "−" : isIncrease ? "+" : ""}
                        {Math.abs(pct)}%
                      </span>
                    ) : (
                      <span className="text-xs text-gray-600">—</span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(w.created_at).toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}