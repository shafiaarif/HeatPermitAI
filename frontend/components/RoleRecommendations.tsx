const ROLE_ICONS: Record<string, string> = {
  attendees: "👥",
  medical_team: "⛑️",
  event_staff: "🧑‍💼",
  performers: "🎤",
  event_manager: "📋",
};

const ROLE_LABELS: Record<string, string> = {
  attendees: "Attendees",
  medical_team: "Medical Team",
  event_staff: "Event Staff",
  performers: "Performers",
  event_manager: "Event Manager",
};

export default function RoleRecommendations({ roles }: { roles: Record<string, string> }) {
  const entries = Object.entries(roles);

  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-4">Role-Specific Guidance</p>
      <div className="grid md:grid-cols-2 gap-3">
        {entries.map(([key, text], i) => {
          const isLastOdd = entries.length % 2 !== 0 && i === entries.length - 1;
          return (
            <div
              key={key}
              className={`bg-base-800/50 border border-border rounded-lg p-3 ${
                isLastOdd ? "md:col-span-2" : ""
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm">{ROLE_ICONS[key] || "•"}</span>
                <p className="text-xs font-semibold text-white">{ROLE_LABELS[key] || key}</p>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}