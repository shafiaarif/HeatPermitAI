"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SummaryBanner({ eventId }: { eventId: string }) {
  const [summary, setSummary] = useState<string | null>(null);

  useEffect(() => {
    api.summary(eventId).then((res) => setSummary(res.summary)).catch(() => {});
  }, [eventId]);

  if (!summary) return null;

  return (
    <div className="bg-orange-500/5 border border-orange-500/20 rounded-xl p-4">
      <p className="text-xs text-orange-400 font-semibold mb-1">Summary</p>
      <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>
    </div>
  );
}