"use client";

import { useState } from "react";
import { api, WhatIfResult } from "@/lib/api";
import WhatIfComparisonChart from "@/components/charts/WhatIfComparisonChart";

export default function WhatIfSimulator({ eventId }: { eventId: string }) {
  const [startTime, setStartTime] = useState("06:00");
  const [endTime, setEndTime] = useState("12:00");
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string>("");

  async function runWhatIf() {
    setLoading(true);
    setError(null);
    setProgress("Starting comparison...");
    try {
      const { job_id } = await api.startWhatIfJob(eventId, startTime, endTime);

      let final = null;
      const MAX_ATTEMPTS = 100; // ~5 minutes at 3s intervals — safety limit
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        await new Promise((r) => setTimeout(r, 3000));
        const status = await api.getWhatIfJobStatus(job_id);
        if (status.progress) setProgress(status.progress);

        if (status.status === "completed" && status.result) {
          final = status.result;
          break;
        }
        if (status.status === "failed") {
          throw new Error(status.error || "What-If comparison failed");
        }
      }

      if (!final) {
        throw new Error("Comparison timed out — please try again.");
      }
      setResult(final);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-4">What-If Simulator</p>
      <p className="text-xs text-gray-500 mb-4">
        Try an alternate time window and see the quantified risk difference.
      </p>

      <div className="flex items-end gap-3 mb-4 flex-wrap">
        <div>
          <label className="text-[11px] text-gray-500 block mb-1">Proposed start</label>
          <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="input w-32" />
        </div>
        <div>
          <label className="text-[11px] text-gray-500 block mb-1">Proposed end</label>
          <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="input w-32" />
        </div>
        <button
          onClick={runWhatIf}
          disabled={loading}
          className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {loading ? "Running..." : "Compare"}
        </button>
      </div>

      {loading && (
        <p className="text-xs text-gray-500">{progress || "Fetching live FortyGuard data..."}</p>
      )}
      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="space-y-4 mt-2">
          <div className="grid md:grid-cols-2 gap-3">
            <WindowCard label="Current" window={result.current_schedule} />
            <WindowCard label="Proposed" window={result.proposed_schedule} highlight />
          </div>

          <WhatIfComparisonChart current={result.current_schedule} proposed={result.proposed_schedule} />

          {result.exposure_reduction_percent !== null && (
            <div className="bg-base-800/50 border border-border rounded-lg p-4 text-center">
              <p className="text-xs text-gray-500 mb-1">Exposure Change</p>
              <p
                className={`text-2xl font-bold ${
                  result.exposure_reduction_percent > 0
                    ? "text-green-400"
                    : result.exposure_reduction_percent < 0
                    ? "text-red-400"
                    : "text-gray-400"
                }`}
              >
                {result.exposure_reduction_percent > 0 ? "−" : result.exposure_reduction_percent < 0 ? "+" : ""}
                {Math.abs(result.exposure_reduction_percent)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {result.exposure_reduction_percent > 0
                  ? "exposure reduction with proposed window"
                  : result.exposure_reduction_percent < 0
                  ? "the proposed window is actually riskier"
                  : "no meaningful difference — both windows carry similar risk"}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function WindowCard({ label, window, highlight }: { label: string; window: any; highlight?: boolean }) {
  return (
    <div className={`rounded-lg p-3 border ${highlight ? "border-orange-500/30 bg-orange-500/5" : "border-border bg-base-800/50"}`}>
      <p className="text-[11px] text-gray-500 mb-1">
        {label} ({window.start_time}–{window.end_time})
      </p>
      <p className="text-sm font-bold text-white">{window.status} — {window.risk_score}/100</p>
      <p className="text-xs text-gray-500 mt-1">Peak: {window.peak_temperature.toFixed(1)}°C</p>
    </div>
  );
}