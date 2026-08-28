"""
Builds an hour-by-hour heat timeline for an event window.
Uses filter_type=2 (Range of Hours) to fetch the ENTIRE window in ONE
API call instead of one call per hour — much faster and avoids
overwhelming FortyGuard with repeated requests.
"""
from app.services.fortyguard_client import get_environmental_parameters, clean_value
from app.services.risk_scoring import classify_hourly_tier


def get_event_hourly_timeline(latitude: float, longitude: float, date_str: str,
                               start_time: str, end_time: str,
                               baseline_temperature: float) -> list[dict]:
    """
    Returns [{'hour': '14:00', 'heat_index': .., 'wet_bulb_temp': .., 'tier': 'Danger'}, ...]
    Single API call using filter_type=2, which returns time-aligned arrays.
    """
    print(f"  [timeline] Fetching entire window {start_time}-{end_time} in ONE call...")

    env_result = get_environmental_parameters(
        latitude, longitude,
        temperature=baseline_temperature,
        start_date=date_str,
        filter_type=2,
        start_time=start_time,
        end_time=end_time,
        analysis=["heat_index_celsius", "wet_bulb_temperature_celsius"],
    )

    location = env_result["locations"][0]
    params = location["parameters"]
    timestamps = env_result.get("metadata", {}).get("timestamps", [])

    heat_index_arr = params.get("heat_index_celsius", [])
    wet_bulb_arr = params.get("wet_bulb_temperature_celsius", [])

    timeline = []
    for i, ts in enumerate(timestamps):
        hour_label = ts[11:16]  # extract 'HH:MM' from ISO timestamp
        heat_index = clean_value(heat_index_arr[i]) if i < len(heat_index_arr) else None
        wet_bulb = clean_value(wet_bulb_arr[i]) if i < len(wet_bulb_arr) else None

        timeline.append({
            "hour": hour_label,
            "heat_index": heat_index,
            "wet_bulb_temp": wet_bulb,
            "tier": classify_hourly_tier(heat_index, wet_bulb),
        })

    print(f"  [timeline] Done — {len(timeline)} hours received in a single call")
    return timeline