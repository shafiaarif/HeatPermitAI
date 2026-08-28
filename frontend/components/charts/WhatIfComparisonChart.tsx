"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { WhatIfWindow } from "@/lib/api";

interface Props {
  current: WhatIfWindow;
  proposed: WhatIfWindow;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-base-900 border border-border rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-white font-semibold mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value !== null && p.value !== undefined ? `${p.value}°C` : "—"}
        </p>
      ))}
    </div>
  );
}

function computeYDomain(values: (number | null | undefined)[]): [number, number] {
  const valid = values.filter((v): v is number => v !== null && v !== undefined);
  if (valid.length === 0) return [0, 50];
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const padding = Math.max((max - min) * 0.15, 2);
  return [Math.max(0, Math.floor(min - padding)), Math.ceil(max + padding)];
}

export default function WhatIfComparisonChart({ current, proposed }: Props) {
  if (!current?.hourly_timeline || !proposed?.hourly_timeline) {
    return null;
  }

  // Merge both timelines by hour so they plot on a shared X-axis.
  const hourMap = new Map<string, { hour: string; current?: number | null; proposed?: number | null }>();

  current.hourly_timeline.forEach((h) => {
    hourMap.set(h.hour, { hour: h.hour, current: h.heat_index });
  });
  proposed.hourly_timeline.forEach((h) => {
    const existing = hourMap.get(h.hour);
    if (existing) {
      existing.proposed = h.heat_index;
    } else {
      hourMap.set(h.hour, { hour: h.hour, proposed: h.heat_index });
    }
  });

  const data = Array.from(hourMap.values()).sort((a, b) => a.hour.localeCompare(b.hour));

  const yDomain = computeYDomain(data.flatMap((d) => [d.current, d.proposed]));

  return (
    <div className="card p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-white">Current vs Proposed — Heat Index</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Overlaying both time windows shows exactly where the proposed schedule runs hotter or cooler.
        </p>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
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
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#9ca3af" }}
            iconType="circle"
          />
          <Line
            type="monotone"
            dataKey="current"
            name={`Current (${current.start_time}–${current.end_time})`}
            stroke="#6b7280"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="proposed"
            name={`Proposed (${proposed.start_time}–${proposed.end_time})`}
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}