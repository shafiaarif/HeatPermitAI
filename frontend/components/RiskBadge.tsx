const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  "HIGH RISK": { bg: "bg-red-500/10", text: "text-red-400", dot: "bg-red-500" },
  "MODERATE RISK": { bg: "bg-yellow-500/10", text: "text-yellow-400", dot: "bg-yellow-500" },
  "LOW-MODERATE RISK": { bg: "bg-lime-500/10", text: "text-lime-400", dot: "bg-lime-500" },
  "LOW RISK": { bg: "bg-green-500/10", text: "text-green-400", dot: "bg-green-500" },
};

export default function RiskBadge({ status, score }: { status: string; score: number }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES["MODERATE RISK"];
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${style.bg}`}>
      <span className={`w-2 h-2 rounded-full ${style.dot}`} />
      <span className={`text-sm font-semibold ${style.text}`}>
        {status} — {score}/100
      </span>
    </div>
  );
}