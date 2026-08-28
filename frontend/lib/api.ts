const API_BASE = "http://127.0.0.1:8000/api/events";

export interface EventItem {
  id: string;
  name: string;
  event_type: string;
  latitude: number;
  longitude: number;
  event_date: string;
  start_time: string;
  end_time: string;
  attendance: number;
}

export interface HourlyTimelineEntry {
  hour: string;
  heat_index: number | null;
  wet_bulb_temp: number | null;
  tier: "Safe" | "Caution" | "Danger" | "Extreme" | "Unknown";
}

export interface Decision {
  recommendation: "PROCEED" | "MODIFY" | "ADD_INTERVENTIONS" | "POSTPONE";
  reasoning: string;
  suggested_schedule_change: string | null;
  interventions: string[];
}

export interface WhatIfWindow {
  start_time: string;
  end_time: string;
  duration_hours: number;
  risk_score: number;
  status: string;
  peak_temperature: number;
  exceedance_hours: number;
  persistence_hours: number;
  hourly_timeline: HourlyTimelineEntry[];
  selection_reasoning?: string;
}

export interface NoSafeAlternative {
  checked_window: string;
  best_status: string;
  best_risk_score: number;
  reasoning: string;
}

export interface AssessResult {
  event_id: string;
  event_name: string;
  duration_hours: number;
  risk_score: number;
  status: string;
  peak_temperature: number;
  exceedance_hours: number;
  persistence_hours: number;
  hourly_timeline: HourlyTimelineEntry[];
  decision?: Decision;
  what_if_evidence?: WhatIfWindow;
}

export interface WhatIfResult {
  current_schedule: WhatIfWindow;
  proposed_schedule: WhatIfWindow;
  exposure_reduction_percent: number | null;
}

export interface DecisionBundle {
  event_id: string;
  event_name: string;
  assessment: {
    duration_hours: number;
    risk_score: number;
    status: string;
    peak_temperature: number;
    exceedance_hours: number;
    persistence_hours: number;
    hourly_timeline: HourlyTimelineEntry[];
  };
  decision?: Decision;
  what_if_evidence?: WhatIfWindow;
  no_safe_alternative?: NoSafeAlternative;
  role_recommendations?: Record<string, string>;
  safety_plan?: {
    before_event: { time: string; action: string }[];
    during_event: { monitor_interval_minutes: number; monitoring_note: string };
    emergency_trigger: { condition: string; action: string };
  };
}

export interface HistoryResult {
  event_id: string;
  safety_plans: { id: string; plan: any; created_at: string }[];
  what_if_comparisons: { id: string; exposure_reduction_percent: number | null; created_at: string }[];
}

export interface SummaryResult {
  event_id: string;
  event_name: string;
  summary: string;
}

export interface HeatmapTile {
  lat_min: number;
  lat_max: number;
  lng_min: number;
  lng_max: number;
  temperature: number;
}

export interface HeatmapTilesResult {
  event_id: string;
  event_name: string;
  tiles: HeatmapTile[];
  source: "cache" | "live";
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listEvents: () => apiFetch<EventItem[]>(""),
  getEvent: (id: string) => apiFetch<EventItem>(`/${id}`),
  createEvent: (data: Omit<EventItem, "id">) =>
    apiFetch<EventItem>("", { method: "POST", body: JSON.stringify(data) }),
  deleteEvent: (id: string) => apiFetch<void>(`/${id}`, { method: "DELETE" }),

  assessEvent: (id: string) => apiFetch<AssessResult>(`/${id}/assess`, { method: "POST" }),

  heatmapTiles: (id: string) => apiFetch<HeatmapTilesResult>(`/${id}/heatmap-tiles`),

  whatIf: (id: string, startTime: string, endTime: string) =>
    apiFetch<WhatIfResult>(
      `/${id}/what-if?proposed_start_time=${startTime}&proposed_end_time=${endTime}`,
      { method: "POST" }
    ),

  decision: (id: string) => apiFetch<DecisionBundle>(`/${id}/decision`, { method: "POST" }),

  history: (id: string) => apiFetch<HistoryResult>(`/${id}/history`),

  summary: (id: string) => apiFetch<SummaryResult>(`/${id}/summary`),

  intelligenceReportUrl: (id: string) => `${API_BASE}/${id}/intelligence-report`,
};