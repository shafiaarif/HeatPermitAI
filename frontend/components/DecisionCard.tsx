import { Decision } from "@/lib/api";

const REC_STYLES: Record<string, string> = {
  PROCEED: "bg-green-500/10 text-green-400",
  MODIFY: "bg-orange-500/10 text-orange-400",
  ADD_INTERVENTIONS: "bg-yellow-500/10 text-yellow-400",
  POSTPONE: "bg-red-500/10 text-red-400",
};

export default function DecisionCard({ decision }: { decision: Decision }) {
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-3">AI Decision Agent</p>
      <span className={`text-xs font-bold px-2.5 py-1 rounded ${REC_STYLES[decision.recommendation] || REC_STYLES.ADD_INTERVENTIONS}`}>
        {decision.recommendation.replace("_", " ")}
      </span>
      <p className="text-gray-300 text-sm leading-relaxed mt-3">{decision.reasoning}</p>
      {decision.suggested_schedule_change && (
        <div className="mt-3 bg-base-800/50 border border-border rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Suggested change</p>
          <p className="text-sm text-orange-400">{decision.suggested_schedule_change}</p>
        </div>
      )}
      {decision.interventions.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-2">Recommended interventions</p>
          <ul className="space-y-1.5">
            {decision.interventions.map((item, i) => (
              <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                <span className="text-orange-400 mt-0.5">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}