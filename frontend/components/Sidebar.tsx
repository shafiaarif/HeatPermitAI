"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, EventItem } from "@/lib/api";

export default function Sidebar() {
  const pathname = usePathname();
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadEvents() {
      try {
        const data = await api.listEvents();
        if (!cancelled) setEvents(data);
      } catch (err) {
        // silently fail — sidebar just shows empty state
        if (!cancelled) setEvents([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadEvents();
    return () => {
      cancelled = true;
    };
  }, [pathname]); // re-fetch when navigating, so a newly created event shows up

  return (
    <aside className="w-64 shrink-0 bg-base-900 border-r border-border min-h-screen flex flex-col relative">
      {/* Ambient glow */}
      <div className="absolute top-0 left-0 w-40 h-40 bg-orange-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <div className="relative p-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-bold text-xs shadow-lg shadow-orange-500/20">
            H
          </div>
          <div>
            <p className="text-white font-semibold text-xs leading-tight tracking-tight">
              HeatPermit AI
            </p>
            <p className="text-gray-500 text-[10px] leading-tight">Event Heat Safety</p>
          </div>
        </div>
      </div>

      {/* New Event button */}
      <div className="relative p-2.5">
        <Link
          href="/"
          className="group flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 shadow-md shadow-orange-500/15 hover:shadow-orange-500/25 transition-all duration-200 hover:-translate-y-0.5"
        >
          <span className="text-sm w-3.5 text-center transition-transform duration-200 group-hover:rotate-90">
            +
          </span>
          New Event
        </Link>
      </div>

      {/* Events list */}
      <div className="relative flex-1 overflow-y-auto px-2.5 pb-2.5">
        <div className="flex items-center justify-between px-2 mb-2 mt-3">
          <p className="text-[10px] uppercase tracking-wider text-gray-600 font-semibold">
            Events
          </p>
          {!loading && events.length > 0 && (
            <span className="text-[10px] text-gray-600 bg-base-800/50 px-1.5 py-0.5 rounded-full">
              {events.length}
            </span>
          )}
        </div>

        {loading && (
          <div className="flex items-center gap-2 px-2 py-2">
            <span className="w-3 h-3 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
            <p className="text-xs text-gray-600">Loading events...</p>
          </div>
        )}

        {!loading && events.length === 0 && (
          <p className="text-xs text-gray-600 px-2 py-2">No events yet — create your first one above.</p>
        )}

        <div className="space-y-1">
          {events.map((event) => {
            const isActive = pathname === `/events/${event.id}`;
            return (
              <Link
                key={event.id}
                href={`/events/${event.id}`}
                className={`relative block px-3 py-2.5 rounded-xl text-xs transition-all duration-200 ${
                  isActive
                    ? "bg-base-800 text-white shadow-sm"
                    : "text-gray-400 hover:bg-base-800/50 hover:text-gray-200"
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-orange-500 rounded-r-full" />
                )}
                <p className="font-semibold truncate">{event.name}</p>
                <p className="text-[10px] text-gray-500 mt-0.5 capitalize">
                  {event.event_type} · {event.event_date}
                </p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Status footer */}
      <div className="relative p-3 border-t border-border">
        <div className="flex items-center gap-2 px-1 text-[11px] text-gray-500">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500" />
          </span>
          Live · FortyGuard API
        </div>
      </div>
    </aside>
  );
}