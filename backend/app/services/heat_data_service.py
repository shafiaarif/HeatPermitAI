"""
Heat Data Agent.
Given an event's location + a time window (its own, OR an overridden
proposed window for What-If comparisons), returns peak temperature,
exceedance hours, persistence hours, heat index, wet bulb — cached per
event + time window to avoid redundant FortyGuard polling.
Exceedance/persistence now use filter_type=2 scoped to the actual window,
NOT filter_type=3 (whole day) — otherwise they never vary between the
current and proposed What-If windows, making comparisons meaningless.
"""
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.db_models import Event, HeatAssessment
from app.services.fortyguard_client import create_heatmap, get_environmental_parameters, clean_value

CACHE_TTL_MINUTES = 15
CALL_DELAY_SECONDS = 2


def get_event_heat_data(event: Event, db: Session, start_time: str = None, end_time: str = None) -> dict:
    start_time_str = start_time or str(event.start_time)[:5]
    end_time_str = end_time or str(event.end_time)[:5]
    start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()

    print(f"  [heat_data] Checking cache for window {start_time_str}-{end_time_str}...")

    cache_cutoff = datetime.now(timezone.utc) - timedelta(minutes=CACHE_TTL_MINUTES)
    cached = (
        db.query(HeatAssessment)
        .filter(HeatAssessment.event_id == event.id)
        .filter(HeatAssessment.assessed_start_time == start_time_obj)
        .filter(HeatAssessment.assessed_end_time == end_time_obj)
        .filter(HeatAssessment.fetched_at >= cache_cutoff)
        .order_by(desc(HeatAssessment.fetched_at))
        .first()
    )

    if cached:
        print(f"  [heat_data] CACHE HIT — skipping live calls")
        cached_timeline = (cached.raw_response or {}).get("hourly_timeline")
        return {
            "peak_temperature": cached.peak_temperature,
            "exceedance_hours": cached.exceedance_hours,
            "persistence_hours": cached.persistence_hours,
            "heat_index": cached.heat_index,
            "wet_bulb_temp": cached.wet_bulb_temp,
            "source": "cache",
            "fetched_at": cached.fetched_at.isoformat(),
            "cached_timeline": cached_timeline,
        }

    print(f"  [heat_data] CACHE MISS — calling FortyGuard live (4 calls)...")
    date_str = str(event.event_date)

    print(f"  [heat_data] [1/4] Fetching tcm (peak temperature)...")
    tcm_result = create_heatmap(
        event.latitude, event.longitude, start_date=date_str, filter_type=2,
        start_time=start_time_str, end_time=end_time_str, analytic_type="tcm",
    )
    temp_stats = tcm_result.get("stats_data", {}).get("temperature_stats") or tcm_result.get("stats_data", {})

    # Use explicit None-checks instead of `or` chaining — `or` treats 0.0 as falsy,
    # which would silently skip a genuine 0.0 "maximum" reading and fall through
    # to "mean" instead. Same bug pattern we fixed in what_if_service.py.
    maximum = temp_stats.get("maximum")
    peak_temp = maximum if maximum is not None else temp_stats.get("mean")

    print(f"  [heat_data] [1/4] Done — peak_temp={peak_temp}")
    time.sleep(CALL_DELAY_SECONDS)

    print(f"  [heat_data] [2/4] Fetching exceedance (scoped to {start_time_str}-{end_time_str})...")
    exceedance_result = create_heatmap(
        event.latitude, event.longitude, start_date=date_str, filter_type=2,
        start_time=start_time_str, end_time=end_time_str,
        analytic_type="exceedance", threshold=35.0, direction="above",
    )
    exceedance_hours = exceedance_result.get("stats_data", {}).get("mean", 0.0)
    print(f"  [heat_data] [2/4] Done — exceedance_hours={exceedance_hours}")
    time.sleep(CALL_DELAY_SECONDS)

    print(f"  [heat_data] [3/4] Fetching persistence (scoped to {start_time_str}-{end_time_str})...")
    persistence_result = create_heatmap(
        event.latitude, event.longitude, start_date=date_str, filter_type=2,
        start_time=start_time_str, end_time=end_time_str,
        analytic_type="persistence", threshold=35.0, direction="above",
    )
    persistence_hours = persistence_result.get("stats_data", {}).get("mean", 0.0)
    print(f"  [heat_data] [3/4] Done — persistence_hours={persistence_hours}")
    time.sleep(CALL_DELAY_SECONDS)

    print(f"  [heat_data] [4/4] Fetching env_params (heat_index, wet_bulb)...")
    env_result = get_environmental_parameters(
        event.latitude, event.longitude,
        temperature=peak_temp or 35.0,
        start_date=date_str, filter_type=1, start_time=start_time_str,
        analysis=["heat_index_celsius", "wet_bulb_temperature_celsius"],
    )
    params = env_result["locations"][0]["parameters"]
    heat_index = clean_value(params["heat_index_celsius"][0])
    wet_bulb = clean_value(params["wet_bulb_temperature_celsius"][0])
    print(f"  [heat_data] [4/4] Done — heat_index={heat_index}, wet_bulb={wet_bulb}")

    new_row = HeatAssessment(
        event_id=event.id,
        assessed_start_time=start_time_obj,
        assessed_end_time=end_time_obj,
        peak_temperature=peak_temp,
        exceedance_hours=exceedance_hours,
        persistence_hours=persistence_hours,
        heat_index=heat_index,
        wet_bulb_temp=wet_bulb,
        raw_response={"tcm": temp_stats, "env": env_result.get("metadata")},
    )
    db.add(new_row)
    db.commit()
    print(f"  [heat_data] Saved to cache")

    return {
        "peak_temperature": peak_temp,
        "exceedance_hours": exceedance_hours,
        "persistence_hours": persistence_hours,
        "heat_index": heat_index,
        "wet_bulb_temp": wet_bulb,
        "source": "live",
        "fetched_at": new_row.fetched_at.isoformat() if new_row.fetched_at else datetime.now(timezone.utc).isoformat(),
    }








def _extract_tile_grid(tcm_result: dict) -> list[dict]:
    """
    tcm's map_data.features is a GeoJSON grid of small rectangular tiles,
    each with a temperature reading. For frontend rendering we simplify
    each tile's polygon down to a bounding box (lat/lng min/max) — enough
    to draw a colored rectangle without needing full geo-rendering libraries.
    """
    map_data = tcm_result.get("map_data", {})
    features = map_data.get("features", [])
    tiles = []

    for f in features:
        props = f.get("properties", {})
        coords = (f.get("geometry", {}).get("coordinates") or [[]])[0]
        if not coords:
            continue

        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        temperature = props.get("average_temperature")

        if temperature is None:
            continue

        tiles.append({
            "lat_min": min(lats),
            "lat_max": max(lats),
            "lng_min": min(lngs),
            "lng_max": max(lngs),
            "temperature": temperature,
        })

    return tiles


def get_event_heatmap_tiles(event: Event, db: Session) -> dict:
    """
    Returns the full spatial tile grid (not just a single peak value) for
    an event's location, for rendering a heat map. Cached the same way as
    the rest of heat_data (15 min TTL), keyed off the event's own window,
    so this doesn't trigger an extra live FortyGuard call if heat data was
    already fetched recently for this event.
    """
    start_time_str = str(event.start_time)[:5]
    end_time_str = str(event.end_time)[:5]
    start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()

    cache_cutoff = datetime.now(timezone.utc) - timedelta(minutes=CACHE_TTL_MINUTES)
    cached = (
        db.query(HeatAssessment)
        .filter(HeatAssessment.event_id == event.id)
        .filter(HeatAssessment.assessed_start_time == start_time_obj)
        .filter(HeatAssessment.assessed_end_time == end_time_obj)
        .filter(HeatAssessment.fetched_at >= cache_cutoff)
        .order_by(desc(HeatAssessment.fetched_at))
        .first()
    )

    if cached and (cached.raw_response or {}).get("map_tiles"):
        print(f"  [heatmap_tiles] CACHE HIT")
        return {
            "tiles": cached.raw_response["map_tiles"],
            "source": "cache",
        }

    print(f"  [heatmap_tiles] CACHE MISS — fetching live tile grid...")
    date_str = str(event.event_date)

    tcm_result = create_heatmap(
        event.latitude, event.longitude, start_date=date_str, filter_type=2,
        start_time=start_time_str, end_time=end_time_str, analytic_type="tcm",
    )
    tiles = _extract_tile_grid(tcm_result)
    print(f"  [heatmap_tiles] Extracted {len(tiles)} tiles")

    if cached:
        existing = cached.raw_response or {}
        existing["map_tiles"] = tiles
        cached.raw_response = existing
        db.commit()
        print(f"  [heatmap_tiles] Saved to existing cache row")

    return {
        "tiles": tiles,
        "source": "live",
    }