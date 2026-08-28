// "use client";

// import {
//   AreaChart,
//   Area,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
// } from "recharts";
// import { HourlyTimelineEntry } from "@/lib/api";

// const TIER_DOT_COLORS: Record<string, string> = {
//   Safe: "#22c55e",
//   Caution: "#eab308",
//   Danger: "#f97316",
//   Extreme: "#ef4444",
//   Unknown: "#6b7280",
// };

// function CustomTooltip({ active, payload, label }: any) {
//   if (!active || !payload || !payload.length) return null;
//   const entry = payload[0].payload as HourlyTimelineEntry;
//   return (
//     <div className="bg-base-900 border border-border rounded-lg px-3 py-2 text-xs shadow-lg">
//       <p className="text-white font-semibold mb-1">
//         {label} —{" "}
//         <span style={{ color: TIER_DOT_COLORS[entry.tier] || "#6b7280" }}>
//           {entry.tier}
//         </span>
//       </p>
//       <p className="text-gray-400">Heat index: {entry.heat_index ?? "—"}°C</p>
//       <p className="text-gray-400">Wet bulb: {entry.wet_bulb_temp ?? "—"}°C</p>
//     </div>
//   );
// }

// export default function HeatTrendChart({ hourly }: { hourly: HourlyTimelineEntry[] }) {
//   const data = hourly.map((h) => ({
//     ...h,
//     hour: h.hour,
//   }));

//   return (
//     <div className="card p-5">
//       <div className="mb-3">
//         <h2 className="text-sm font-semibold text-white">Heat Index & Wet-Bulb Trend</h2>
//         <p className="text-xs text-gray-500 mt-0.5">
//           Hourly heat index vs wet-bulb temperature across the event window.
//         </p>
//       </div>

//       <ResponsiveContainer width="100%" height={260}>
//         <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
//           <defs>
//             <linearGradient id="heatIndexGradient" x1="0" y1="0" x2="0" y2="1">
//               <stop offset="5%" stopColor="#f97316" stopOpacity={0.35} />
//               <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
//             </linearGradient>
//             <linearGradient id="wetBulbGradient" x1="0" y1="0" x2="0" y2="1">
//               <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
//               <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
//             </linearGradient>
//           </defs>
//           <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
//           <XAxis
//             dataKey="hour"
//             tick={{ fill: "#6b7280", fontSize: 10 }}
//             axisLine={{ stroke: "#27272a" }}
//             tickLine={false}
//           />
//           <YAxis
//             tick={{ fill: "#6b7280", fontSize: 10 }}
//             axisLine={false}
//             tickLine={false}
//             unit="°C"
//             width={44}
//           />
//           <Tooltip content={<CustomTooltip />} />
//           <Area
//             type="monotone"
//             dataKey="heat_index"
//             name="Heat Index"
//             stroke="#f97316"
//             strokeWidth={2}
//             fill="url(#heatIndexGradient)"
//           />
//           <Area
//             type="monotone"
//             dataKey="wet_bulb_temp"
//             name="Wet Bulb"
//             stroke="#14b8a6"
//             strokeWidth={2}
//             fill="url(#wetBulbGradient)"
//           />
//         </AreaChart>
//       </ResponsiveContainer>

//       <div className="flex gap-4 mt-2 text-[11px]">
//         <div className="flex items-center gap-1.5">
//           <span className="w-2 h-2 rounded-full bg-orange-500" />
//           <span className="text-gray-500">Heat Index</span>
//         </div>
//         <div className="flex items-center gap-1.5">
//           <span className="w-2 h-2 rounded-full bg-teal-500" />
//           <span className="text-gray-500">Wet Bulb</span>
//         </div>
//       </div>
//     </div>
//   );
// }







"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { HourlyTimelineEntry } from "@/lib/api";

const TIER_DOT_COLORS: Record<string, string> = {
  Safe: "#22c55e",
  Caution: "#eab308",
  Danger: "#f97316",
  Extreme: "#ef4444",
  Unknown: "#6b7280",
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  const entry = payload[0].payload as HourlyTimelineEntry;
  return (
    <div className="bg-base-900 border border-border rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-white font-semibold mb-1">
        {label} —{" "}
        <span style={{ color: TIER_DOT_COLORS[entry.tier] || "#6b7280" }}>
          {entry.tier}
        </span>
      </p>
      <p className="text-gray-400">Heat index: {entry.heat_index ?? "—"}°C</p>
      <p className="text-gray-400">Wet bulb: {entry.wet_bulb_temp ?? "—"}°C</p>
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

export default function HeatTrendChart({ hourly }: { hourly: HourlyTimelineEntry[] }) {
  const data = hourly.map((h) => ({
    ...h,
    hour: h.hour,
  }));

  const yDomain = computeYDomain(
    data.flatMap((d) => [d.heat_index, d.wet_bulb_temp])
  );

  return (
    <div className="card p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-white">Heat Index & Wet-Bulb Trend</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Hourly heat index vs wet-bulb temperature across the event window.
        </p>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="heatIndexGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="wetBulbGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
            </linearGradient>
          </defs>
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
          <Area
            type="monotone"
            dataKey="heat_index"
            name="Heat Index"
            stroke="#f97316"
            strokeWidth={2}
            fill="url(#heatIndexGradient)"
          />
          <Area
            type="monotone"
            dataKey="wet_bulb_temp"
            name="Wet Bulb"
            stroke="#14b8a6"
            strokeWidth={2}
            fill="url(#wetBulbGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="flex gap-4 mt-2 text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-orange-500" />
          <span className="text-gray-500">Heat Index</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-teal-500" />
          <span className="text-gray-500">Wet Bulb</span>
        </div>
      </div>
    </div>
  );
}