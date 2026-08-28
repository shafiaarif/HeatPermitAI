import { WhatIfWindow } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  "HIGH RISK": "text-red-400",
  "MODERATE RISK": "text-yellow-400",
  "LOW-MODERATE RISK": "text-lime-400",
  "LOW RISK": "text-green-400",
};

interface Props {
  currentStatus: string;
  currentRiskScore: number;
  currentPeakTemp: number;
  evidence: WhatIfWindow;
}

export default function RecommendedWindowCard({
  currentStatus,
  currentRiskScore,
  currentPeakTemp,
  evidence,
}: Props) {
  const reductionPct =
    currentRiskScore > 0
      ? Math.round((1 - evidence.risk_score / currentRiskScore) * 100)
      : 0;

  return (
    <div className="card overflow-hidden border-green-500/20">
      <div className="px-5 py-4 border-b border-border flex items-center gap-2">
        <span className="text-green-400">✓</span>
        <div>
          <h2 className="text-sm font-semibold text-white">A Safer Window Was Found</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            The event doesn't need to be postponed — moving it to this same-day window
            brings the risk down to an acceptable level.
          </p>
        </div>
      </div>

      <div className="p-5">
        <div className="grid md:grid-cols-2 gap-3">
          <div className="rounded-lg p-3 border border-border bg-base-800/50">
            <p className="text-[11px] text-gray-500 mb-1">Current schedule</p>
            <p className={`text-sm font-bold ${STATUS_COLORS[currentStatus] || "text-gray-300"}`}>
              {currentStatus} — {currentRiskScore}/100
            </p>
            <p className="text-xs text-gray-500 mt-1">Peak: {currentPeakTemp.toFixed(1)}°C</p>
          </div>

          <div className="rounded-lg p-3 border border-green-500/30 bg-green-500/5">
            <p className="text-[11px] text-gray-500 mb-1">
              Recommended ({evidence.start_time}–{evidence.end_time})
            </p>
            <p className={`text-sm font-bold ${STATUS_COLORS[evidence.status] || "text-gray-300"}`}>
              {evidence.status} — {evidence.risk_score}/100
            </p>
            <p className="text-xs text-gray-500 mt-1">Peak: {evidence.peak_temperature.toFixed(1)}°C</p>
          </div>
        </div>

        <div className="mt-3 bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-green-400">−{reductionPct}%</p>
          <p className="text-xs text-gray-400">risk reduction with the recommended window</p>
        </div>

        {evidence.selection_reasoning && (
          <div className="mt-3 bg-base-800/50 border border-border rounded-lg p-3">
            <p className="text-[11px] text-gray-500 mb-1 uppercase tracking-wide">Why this window</p>
            <p className="text-xs text-gray-300 leading-relaxed">{evidence.selection_reasoning}</p>
          </div>
        )}
      </div>
    </div>
  );
}