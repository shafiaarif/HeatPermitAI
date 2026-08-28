"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const PRESET_LOCATIONS = [
  { label: "Phoenix, AZ", lat: 33.4484, lng: -112.074, icon: "🌵" },
  { label: "Las Vegas, NV", lat: 36.1699, lng: -115.1398, icon: "🎰" },
  { label: "Los Angeles, CA", lat: 34.0522, lng: -118.2437, icon: "🌊" },
];

const EVENT_TYPES = [
  { value: "concert", label: "Concert", icon: "🎤" },
  { value: "festival", label: "Festival", icon: "🎪" },
  { value: "sports", label: "Sports", icon: "🏟️" },
  { value: "general", label: "General", icon: "📋" },
];

interface Props {
  collapsedByDefault?: boolean;
}

export default function EventControlPanel({ collapsedByDefault = false }: Props) {
  const router = useRouter();
  const [expanded, setExpanded] = useState(!collapsedByDefault);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    event_type: "concert",
    latitude: "",
    longitude: "",
    event_date: "",
    start_time: "",
    end_time: "",
    attendance: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function applyPreset(preset: (typeof PRESET_LOCATIONS)[number]) {
    setSelectedPreset(preset.label);
    setForm((f) => ({
      ...f,
      latitude: String(preset.lat),
      longitude: String(preset.lng),
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const created = await api.createEvent({
        name: form.name,
        event_type: form.event_type,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        event_date: form.event_date,
        start_time: form.start_time,
        end_time: form.end_time,
        attendance: parseInt(form.attendance) || 0,
      });
      router.push(`/events/${created.id}`);
    } catch (err: any) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="card overflow-hidden relative">
      {/* Ambient accent glow */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="relative flex items-center justify-between px-6 py-5 border-b border-border bg-gradient-to-r from-orange-500/5 to-transparent">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/20 shrink-0">
            <span className="text-white text-sm">📍</span>
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">New Event Assessment</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Configure a US location and run a live FortyGuard heat assessment
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs font-medium text-gray-400 hover:text-white px-3 py-1.5 rounded-lg border border-border hover:border-orange-500/40 hover:bg-orange-500/5 transition-all duration-200"
        >
          {expanded ? "Collapse" : "Expand"}
        </button>
      </div>

      {expanded && (
        <form onSubmit={handleSubmit} className="relative p-6 space-y-6">
          {/* Event name */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 flex items-center gap-1.5">
              Event Name
              <span className="text-orange-500">*</span>
            </label>
            <input
              required
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="e.g. Summer Music Festival"
              className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50"
            />
          </div>

          {/* Location presets */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block">
              Quick Locations
            </label>
            <div className="flex flex-wrap gap-2">
              {PRESET_LOCATIONS.map((preset) => {
                const active = selectedPreset === preset.label;
                return (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => applyPreset(preset)}
                    className={`group flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium border transition-all duration-200 ${
                      active
                        ? "bg-orange-500/15 border-orange-500/50 text-orange-400 shadow-sm shadow-orange-500/10"
                        : "bg-base-800/40 border-border text-gray-400 hover:text-white hover:border-gray-600 hover:bg-base-800/70"
                    }`}
                  >
                    <span className={`transition-transform duration-200 ${active ? "scale-110" : "group-hover:scale-110"}`}>
                      {preset.icon}
                    </span>
                    {preset.label}
                    {active && <span className="text-orange-400 text-[10px]">✓</span>}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Coordinates + event type */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                Latitude
              </label>
              <input
                required
                type="number"
                step="any"
                value={form.latitude}
                onChange={(e) => {
                  update("latitude", e.target.value);
                  setSelectedPreset(null);
                }}
                placeholder="33.4484"
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                Longitude
              </label>
              <input
                required
                type="number"
                step="any"
                value={form.longitude}
                onChange={(e) => {
                  update("longitude", e.target.value);
                  setSelectedPreset(null);
                }}
                placeholder="-112.0740"
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                Event Type
              </label>
              <select
                value={form.event_type}
                onChange={(e) => update("event_type", e.target.value)}
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50 cursor-pointer"
              >
                {EVENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.icon} {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-1.5 -mt-3">
            <span className="w-1 h-1 rounded-full bg-gray-600" />
            <p className="text-[11px] text-gray-600">
              Coverage limited to the United States — non-US coordinates will fail
            </p>
          </div>

          {/* Date + times */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                Event Date
              </label>
              <input
                required
                type="date"
                value={form.event_date}
                onChange={(e) => update("event_date", e.target.value)}
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                Start Time
              </label>
              <input
                required
                type="time"
                value={form.start_time}
                onChange={(e) => update("start_time", e.target.value)}
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block">
                End Time
              </label>
              <input
                required
                type="time"
                value={form.end_time}
                onChange={(e) => update("end_time", e.target.value)}
                className="input transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50"
              />
            </div>
          </div>
          <div className="flex items-center gap-1.5 -mt-3">
            <span className="w-1 h-1 rounded-full bg-gray-600" />
            <p className="text-[11px] text-gray-600">
              Same-day windows only — overnight events crossing midnight aren't supported yet
            </p>
          </div>

          {/* Attendance */}
          <div className="max-w-xs">
            <label className="text-xs font-semibold text-gray-300 mb-2 block">
              Expected Attendance
            </label>
            <div className="relative">
              <input
                required
                type="number"
                min="0"
                value={form.attendance}
                onChange={(e) => update("attendance", e.target.value)}
                placeholder="5000"
                className="input pl-9 transition-all duration-200 focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">
                👥
              </span>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl p-3.5">
              <span className="shrink-0">⚠</span>
              <span>{error}</span>
            </div>
          )}

          {/* Submit */}
          <div className="flex items-center gap-3 pt-2 border-t border-border">
            <button
              type="submit"
              disabled={submitting}
              className="group relative bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 text-sm shadow-lg shadow-orange-500/20 hover:shadow-orange-500/30 hover:-translate-y-0.5 mt-4"
            >
              <span className="flex items-center gap-2">
                {submitting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    Running Assessment...
                  </>
                ) : (
                  <>
                    Create Event & Run Assessment
                    <span className="transition-transform duration-200 group-hover:translate-x-0.5">→</span>
                  </>
                )}
              </span>
            </button>
            {submitting && (
              <p className="text-xs text-gray-500 mt-4">
                This can take 2–4 minutes — fetching live FortyGuard data
              </p>
            )}
          </div>
        </form>
      )}
    </div>
  );
}