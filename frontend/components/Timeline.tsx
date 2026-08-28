import { HourlyTimelineEntry } from "@/lib/api";

const TIER_COLORS: Record<string, string> = {
  Safe: "bg-green-500",
  Caution: "bg-yellow-500",
  Danger: "bg-orange-500",
  Extreme: "bg-red-500",
  Unknown: "bg-gray-600",
};

const TIER_ORDER = ["Safe", "Caution", "Danger", "Extreme"];

export default function Timeline({ hourly }: { hourly: HourlyTimelineEntry[] }) {
  const worstTier = hourly.reduce((worst, h) => {
    const idx = TIER_ORDER.indexOf(h.tier);
    return idx > TIER_ORDER.indexOf(worst) ? h.tier : worst;
  }, "Safe");

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="text-sm font-semibold text-white">Hourly Heat Timeline</h2>
        <div className="flex gap-3 text-[11px]">
          {TIER_ORDER.map((tier) => (
            <div key={tier} className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-sm ${TIER_COLORS[tier]}`} />
              <span className="text-gray-500">{tier}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex rounded-lg overflow-hidden border border-border">
        {hourly.map((entry, i) => (
          <div key={i} className={`flex-1 h-14 relative group cursor-default ${TIER_COLORS[entry.tier]}`}>
            <div className="absolute inset-x-0 -bottom-5 text-center text-[9px] text-gray-500">
              {entry.hour}
            </div>
            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-base-900 border border-border rounded px-2 py-1 text-xs whitespace-nowrap z-10">
              <p className="text-white font-semibold">{entry.hour} — {entry.tier}</p>
              <p className="text-gray-400">Heat index: {entry.heat_index}°C</p>
              <p className="text-gray-400">Wet bulb: {entry.wet_bulb_temp}°C</p>
            </div>
          </div>
        ))}
      </div>
      <div className="h-5" />

      {(worstTier === "Danger" || worstTier === "Extreme") && (
        <div className="mt-1 flex items-center gap-2 text-xs text-orange-400">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
          Critical window detected — peak risk tier: {worstTier}
        </div>
      )}
    </div>
  );
}