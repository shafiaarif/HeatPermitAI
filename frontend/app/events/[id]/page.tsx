"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, EventItem, DecisionBundle, AssessResult } from "@/lib/api";

import EventOverview from "@/components/EventOverview";
import SummaryBanner from "@/components/SummaryBanner";
import HeatMapGrid from "@/components/HeatMapGrid";
import HeatTrendChart from "@/components/charts/HeatTrendChart";
import ExceedanceBarChart from "@/components/charts/ExceedanceBarChart";
import DecisionCard from "@/components/DecisionCard";
import RecommendedWindowCard from "@/components/RecommendedWindowCard";
import NoSafeAlternativeCard from "@/components/NoSafeAlternativeCard";
import RoleRecommendations from "@/components/RoleRecommendations";
import SafetyPlanCard from "@/components/SafetyPlanCard";
import WhatIfSimulator from "@/components/WhatIfSimulator";
import HistoryPanel from "@/components/HistoryPanel";
import IntelligenceReportButton from "@/components/IntelligenceReportButton";

type Tab = "overview" | "whatif" | "history" | "report";

export default function EventDashboardPage() {
  const params = useParams();
  const eventId = params.id as string;

  const [event, setEvent] = useState<EventItem | null>(null);
  const [bundle, setBundle] = useState<DecisionBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [progress, setProgress] = useState<string>("");

  useEffect(() => {
    if (!eventId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setProgress("Starting assessment...");
      try {
        const ev = await api.getEvent(eventId);
        if (cancelled) return;
        setEvent(ev);

        const { job_id } = await api.startDecisionJob(eventId);
        if (cancelled) return;

        // Poll every 3 seconds until the job is done or failed
        while (!cancelled) {
          await new Promise((r) => setTimeout(r, 3000));
          const status = await api.getDecisionJobStatus(job_id);
          if (cancelled) return;

          if (status.progress) setProgress(status.progress);

          if (status.status === "completed" && status.result) {
            setBundle(status.result);
            break;
          }
          if (status.status === "failed") {
            throw new Error(status.error || "Assessment failed");
          }
        }
      } catch (err: any) {
        if (!cancelled) setError(err.message || "Something went wrong");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  if (loading) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="card p-8 text-center">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white font-semibold text-sm mb-1">Running full AI heat assessment...</p>
          <p className="text-gray-500 text-xs">
            {progress || "Fetching live FortyGuard data and generating LLM decision — this can take 2-4 minutes."}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="card p-6 bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-sm font-semibold mb-1">Failed to load event</p>
          <p className="text-red-400/80 text-xs">{error}</p>
        </div>
      </div>
    );
  }

  if (!event || !bundle) return null;

  const assessment: AssessResult = {
    event_id: event.id,
    event_name: event.name,
    ...bundle.assessment,
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "whatif", label: "What-If" },
    { key: "history", label: "History" },
    { key: "report", label: "Report" },
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-5">
      <div className="flex gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-xs font-semibold transition-colors border-b-2 -mb-px ${
              tab === t.key
                ? "text-orange-400 border-orange-500"
                : "text-gray-500 border-transparent hover:text-gray-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-5">
          <SummaryBanner eventId={eventId} />
          <EventOverview event={event} assessment={assessment} />
          <HeatMapGrid eventId={eventId} />
          <HeatTrendChart hourly={bundle.assessment.hourly_timeline} />
          <ExceedanceBarChart hourly={bundle.assessment.hourly_timeline} />
          {bundle.decision && <DecisionCard decision={bundle.decision} />}
          {bundle.what_if_evidence && (
            <RecommendedWindowCard
              currentStatus={bundle.assessment.status}
              currentRiskScore={bundle.assessment.risk_score}
              currentPeakTemp={bundle.assessment.peak_temperature}
              evidence={bundle.what_if_evidence}
            />
          )}
          {bundle.no_safe_alternative && (
            <NoSafeAlternativeCard data={bundle.no_safe_alternative} />
          )}
          {bundle.role_recommendations && <RoleRecommendations roles={bundle.role_recommendations} />}
          {bundle.safety_plan && <SafetyPlanCard plan={bundle.safety_plan} />}
        </div>
      )}

      {tab === "whatif" && <WhatIfSimulator eventId={eventId} />}
      {tab === "history" && <HistoryPanel eventId={eventId} />}
      {tab === "report" && <IntelligenceReportButton eventId={eventId} />}
    </div>
  );
}