export default function SafetyPlanCard({
  plan,
}: {
  plan: {
    before_event: { time: string; action: string }[];
    during_event: { monitor_interval_minutes: number; monitoring_note: string };
    emergency_trigger: { condition: string; action: string };
  };
}) {
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-4">Safety Plan</p>

      <div className="mb-4">
        <p className="text-xs font-semibold text-gray-400 mb-2">Before Event</p>
        <div className="space-y-2">
          {plan.before_event.map((step, i) => (
            <div key={i} className="flex items-start gap-3 text-xs">
              <span className="text-orange-400 font-mono w-12 shrink-0">{step.time}</span>
              <span className="text-gray-300">{step.action}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xs font-semibold text-gray-400 mb-1">During Event</p>
        <p className="text-xs text-gray-300">{plan.during_event.monitoring_note}</p>
      </div>

      <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
        <p className="text-xs font-semibold text-red-400 mb-1">⚠ Emergency Trigger</p>
        <p className="text-xs text-gray-400 mb-2">{plan.emergency_trigger.condition}</p>
        <p className="text-xs text-gray-300">{plan.emergency_trigger.action}</p>
      </div>
    </div>
  );
}