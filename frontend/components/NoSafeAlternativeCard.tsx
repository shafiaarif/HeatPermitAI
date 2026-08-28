import { NoSafeAlternative } from "@/lib/api";

export default function NoSafeAlternativeCard({ data }: { data: NoSafeAlternative }) {
  return (
    <div className="card overflow-hidden border-red-500/20">
      <div className="px-5 py-4 flex items-center gap-2">
        <span className="text-red-400">✕</span>
        <div>
          <h2 className="text-sm font-semibold text-white">No Safe Alternative Found</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            The system checked realistic same-day time windows — none brought the risk
            down to a safe level.
          </p>
        </div>
      </div>

      <div className="px-5 pb-5">
        <div className="bg-base-800/50 border border-border rounded-lg p-3">
          <p className="text-xs text-gray-400 leading-relaxed">
            The best available window ({data.checked_window}) was still{" "}
            <span className="text-red-400 font-semibold">
              {data.best_status} ({data.best_risk_score}/100)
            </span>
            . {data.reasoning}
          </p>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Postponing or rescheduling to a different day remains the safest option.
        </p>
      </div>
    </div>
  );
}