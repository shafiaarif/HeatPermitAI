import EventControlPanel from "@/components/EventControlPanel";

export default function HomePage() {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="relative">
        <div className="absolute -top-8 -left-8 w-40 h-40 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/25">
            <span className="text-white text-lg">🌡️</span>
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              HeatPermit AI
            </h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded-full">
              Live
            </span>
          </div>
        </div>
        <p className="text-gray-500 text-sm relative pl-[52px]">
          Select an event from the sidebar, or create a new one below to run a live AI heat-safety assessment.
        </p>
      </div>

      <EventControlPanel />

      <div className="card p-8 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/[0.03] to-transparent pointer-events-none" />
        <p className="relative text-gray-500 text-sm">
          👈 Your past events are listed in the sidebar. Click any event to view its full dashboard —
          risk score, hourly timeline, AI decision, role guidance, and safety plan.
        </p>
      </div>
    </div>
  );
}