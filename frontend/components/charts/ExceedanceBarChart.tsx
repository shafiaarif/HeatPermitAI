"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { HourlyTimelineEntry } from "@/lib/api";

const TIER_BAR_COLORS: Record<string, string> = {
  Safe: "#22c55e",
  Caution: "#eab308",
  Danger: "#f97316",
  Extreme: "#ef4444",
  Unknown: "#4b5563",
};

const EXCEEDANCE_THRESHOLD_C = 35; // matches backend's exceedance threshold

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  const entry = payload[0].payload as HourlyTimelineEntry;
  const exceeds =
    entry.heat_index !== null && entry.heat_index >= EXCEEDANCE_THRESHOLD_C;
  return (
    <div className="bg-base-900 border border-border rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-white font-semibold mb-1">
        {label} —{" "}
        <span style={{ color: TIER_BAR_COLORS[entry.tier] || "#6b7280" }}>
          {entry.tier}
        </span>
      </p>
      <p className="text-gray-400">Heat index: {entry.heat_index ?? "—"}°C</p>
      {exceeds && (
        <p className="text-red-400 mt-1">⚠ Exceeds {EXCEEDANCE_THRESHOLD_C}°C threshold</p>
      )}
    </div>
  );
}

function computeYDomain(values: (number | null | undefined)[], mustInclude: number): [number, number] {
  const valid = values.filter((v): v is number => v !== null && v !== undefined);
  if (valid.length === 0) return [0, Math.ceil(mustInclude * 1.2)];
  const min = 0; // bars should still start at zero for a fair visual comparison
  const max = Math.max(...valid, mustInclude);
  const padding = Math.max((max - min) * 0.15, 2);
  return [0, Math.ceil(max + padding)];
}

export default function ExceedanceBarChart({ hourly }: { hourly: HourlyTimelineEntry[] }) {
  const data = hourly.map((h) => ({
    ...h,
    hour: h.hour,
  }));

  const exceedanceCount = data.filter(
    (h) => h.heat_index !== null && h.heat_index >= EXCEEDANCE_THRESHOLD_C
  ).length;

  const yDomain = computeYDomain(
    data.map((d) => d.heat_index),
    EXCEEDANCE_THRESHOLD_C
  );

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Hourly Heat Index vs Exceedance Threshold
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Bars crossing the dashed line exceed the {EXCEEDANCE_THRESHOLD_C}°C safety threshold.
          </p>
        </div>
        {exceedanceCount > 0 && (
          <span className="text-xs font-semibold text-red-400 bg-red-500/10 px-2.5 py-1 rounded-full">
            {exceedanceCount} {exceedanceCount === 1 ? "hour" : "hours"} over threshold
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis
            dataKey="hour"
            tick={{ fill: "#6b7280", fontSize: 10 }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
          />
          <YAxis
            domain={yDomain}
            tick={{ fill: "#6b7280", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            unit="°C"
            width={44}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={EXCEEDANCE_THRESHOLD_C}
            stroke="#eab308"
            strokeDasharray="4 4"
            label={{
              value: "Threshold",
              position: "insideTopRight",
              fill: "#eab308",
              fontSize: 10,
            }}
          />
          <Bar dataKey="heat_index" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={TIER_BAR_COLORS[entry.tier] || "#4b5563"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex gap-4 mt-2 text-[11px] flex-wrap">
        {Object.entries(TIER_BAR_COLORS)
          .filter(([tier]) => tier !== "Unknown")
          .map(([tier, color]) => (
            <div key={tier} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: color }} />
              <span className="text-gray-500">{tier}</span>
            </div>
          ))}
      </div>
    </div>
  );
}