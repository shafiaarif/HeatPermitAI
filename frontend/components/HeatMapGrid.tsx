"use client";

import { useEffect, useState } from "react";
import { api, HeatmapTile } from "@/lib/api";

interface Props {
  eventId: string;
}

function temperatureToColor(temp: number, min: number, max: number): string {
  const ratio = max > min ? (temp - min) / (max - min) : 0.5;
  const clamped = Math.max(0, Math.min(1, ratio));

  if (clamped < 0.33) {
    const t = clamped / 0.33;
    return `rgb(${Math.round(34 + t * (234 - 34))}, ${Math.round(197 + t * (179 - 197))}, ${Math.round(94 + t * (8 - 94))})`;
  } else if (clamped < 0.66) {
    const t = (clamped - 0.33) / 0.33;
    return `rgb(${Math.round(234 + t * (249 - 234))}, ${Math.round(179 + t * (115 - 179))}, ${Math.round(8 + t * (22 - 8))})`;
  } else {
    const t = (clamped - 0.66) / 0.34;
    return `rgb(${Math.round(249 + t * (239 - 249))}, ${Math.round(115 + t * (68 - 115))}, ${Math.round(22 + t * (68 - 22))})`;
  }
}

export default function HeatMapGrid({ eventId }: Props) {
  const [tiles, setTiles] = useState<HeatmapTile[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredTile, setHoveredTile] = useState<HeatmapTile | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .heatmapTiles(eventId)
      .then((data) => {
        if (!cancelled) setTiles(data.tiles || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load heat map");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [eventId]);

  if (loading) {
    return (
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-white mb-3">Spatial Heat Map</h2>
        <div className="h-64 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !tiles || tiles.length === 0) {
    return (
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-white mb-2">Spatial Heat Map</h2>
        <p className="text-xs text-gray-600">
          {error ? `Failed to load: ${error}` : "No tile data available for this location."}
        </p>
      </div>
    );
  }

  const temps = tiles.map((t) => t.temperature);
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);

  const latMin = Math.min(...tiles.map((t) => t.lat_min));
  const latMax = Math.max(...tiles.map((t) => t.lat_max));
  const lngMin = Math.min(...tiles.map((t) => t.lng_min));
  const lngMax = Math.max(...tiles.map((t) => t.lng_max));

  const latSpan = latMax - latMin || 1;
  const lngSpan = lngMax - lngMin || 1;

  // Preserve the true aspect ratio of the tile grid instead of forcing it
  // into a fixed square — a wide-but-short grid was previously stretched
  // into a square viewBox, which squished/misaligned the tiles.
  const MAX_DIMENSION = 400;
  const aspectRatio = lngSpan / latSpan;

  let viewBoxW: number;
  let viewBoxH: number;
  if (aspectRatio >= 1) {
    viewBoxW = MAX_DIMENSION;
    viewBoxH = MAX_DIMENSION / aspectRatio;
  } else {
    viewBoxH = MAX_DIMENSION;
    viewBoxW = MAX_DIMENSION * aspectRatio;
  }

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">Spatial Heat Map</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            FortyGuard's hyperlocal tile grid ({tiles.length} tiles) around the event location.
          </p>
        </div>
        <div className="text-xs text-gray-500">
          {minTemp.toFixed(1)}°C – {maxTemp.toFixed(1)}°C
        </div>
      </div>

      <div className="flex justify-center">
        <div className="relative w-full flex justify-center">
          <svg
            viewBox={`0 0 ${viewBoxW} ${viewBoxH}`}
            className="rounded-lg border border-border bg-base-950"
            style={{ maxHeight: 360, maxWidth: "100%", width: "auto" }}
          >
            {tiles.map((tile, i) => {
              const x = ((tile.lng_min - lngMin) / lngSpan) * viewBoxW;
              const y = viewBoxH - ((tile.lat_max - latMin) / latSpan) * viewBoxH;
              const w = ((tile.lng_max - tile.lng_min) / lngSpan) * viewBoxW;
              const h = ((tile.lat_max - tile.lat_min) / latSpan) * viewBoxH;

              return (
                <rect
                  key={i}
                  x={x}
                  y={y}
                  width={Math.max(w, 0.5)}
                  height={Math.max(h, 0.5)}
                  fill={temperatureToColor(tile.temperature, minTemp, maxTemp)}
                  stroke="#0a0a0a"
                  strokeWidth={0.3}
                  onMouseEnter={() => setHoveredTile(tile)}
                  onMouseLeave={() => setHoveredTile(null)}
                  className="cursor-pointer"
                />
              );
            })}
          </svg>

          {hoveredTile && (
            <div className="absolute top-2 left-2 bg-base-900 border border-border rounded-lg px-3 py-2 text-xs shadow-lg pointer-events-none">
              <p className="text-white font-semibold">{hoveredTile.temperature.toFixed(2)}°C</p>
              <p className="text-gray-500">
                {hoveredTile.lat_min.toFixed(4)}, {hoveredTile.lng_min.toFixed(4)}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <span className="text-[10px] text-gray-500">Cooler</span>
        <div
          className="flex-1 h-2 rounded-full"
          style={{
            background: "linear-gradient(to right, #22c55e, #eab308, #f97316, #dc2626)",
          }}
        />
        <span className="text-[10px] text-gray-500">Hotter</span>
      </div>
    </div>
  );
}