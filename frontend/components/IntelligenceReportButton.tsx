"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function IntelligenceReportButton({ eventId }: { eventId: string }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloaded, setDownloaded] = useState(false);

  async function download() {
    setDownloading(true);
    setError(null);
    try {
      const res = await fetch(api.intelligenceReportUrl(eventId), { method: "POST" });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "heat_intelligence_report.pdf";
      a.click();
      setDownloaded(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center gap-2">
        <span className="text-orange-400">📄</span>
        <div>
          <h2 className="text-sm font-semibold text-white">Heat Intelligence Report</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Full climate & air-quality breakdown for this event, powered by FortyGuard.
          </p>
        </div>
      </div>

      <div className="p-5 space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <ReportFeature icon="🌡️" label="Climate classification" />
          <ReportFeature icon="💨" label="Air quality index" />
          <ReportFeature icon="📈" label="Historical weather patterns" />
        </div>

        <div className="bg-orange-500/5 border border-orange-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400">
            Full 19-page Premium report — a comprehensive FortyGuard Heat Intelligence export covering
            long-range climate context, historical patterns, and detailed environmental parameters
            for this event's location and date.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={download}
            disabled={downloading}
            className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
          >
            {downloading ? "Generating (2-5 min)..." : "Download Full Report"}
          </button>
          {downloading && (
            <p className="text-xs text-gray-500">
              Fetching live FortyGuard data — this can take a few minutes.
            </p>
          )}
          {downloaded && !downloading && (
            <p className="text-xs text-green-400">✓ Report downloaded</p>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg p-3">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

function ReportFeature({ icon, label }: { icon: string; label: string }) {
  return (
    <div className="bg-base-800/50 border border-border rounded-lg p-3 text-center">
      <div className="text-lg mb-1">{icon}</div>
      <p className="text-[11px] text-gray-400 leading-tight">{label}</p>
    </div>
  );
}