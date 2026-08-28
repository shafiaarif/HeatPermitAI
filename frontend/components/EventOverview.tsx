import RiskBadge from "./RiskBadge";
import { AssessResult, EventItem } from "@/lib/api";

export default function EventOverview({
  event,
  assessment,
}: {
  event: EventItem;
  assessment: AssessResult;
}) {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">{event.name}</h1>
          <p className="text-sm text-gray-400 mt-1 capitalize">
            {event.event_type} · {event.event_date}
          </p>
        </div>
        <RiskBadge status={assessment.status} score={assessment.risk_score} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <StatCard label="Attendance" value={event.attendance.toLocaleString()} />
        <StatCard label="Duration" value={`${assessment.duration_hours} hrs`} />
        <StatCard label="Peak Temp" value={`${assessment.peak_temperature.toFixed(1)}°C`} color="orange" />
        <StatCard label="Exceedance" value={`${assessment.exceedance_hours.toFixed(1)} hrs`} color="teal" />
      </div>

      <p className="text-xs text-gray-500 mt-4">
        Scheduled: {event.start_time.slice(0, 5)} – {event.end_time.slice(0, 5)}
      </p>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: "orange" | "teal" }) {
  const textColor = color === "orange" ? "text-orange-400" : color === "teal" ? "text-teal-400" : "text-white";
  return (
    <div className="bg-base-800/50 rounded-lg p-3 border border-border">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-xl font-bold mt-1 ${textColor}`}>{value}</p>
    </div>
  );
}