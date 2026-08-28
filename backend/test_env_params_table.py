"""
Prints env_params output in a clean table format — heat_index, wet_bulb,
humidity etc. per hour — for easy side-by-side comparison with FortyGuard's
own notebook output or your backend's /heat-data endpoint.
"""
from app.services.fortyguard_client import create_heatmap, get_environmental_parameters, clean_value

LATITUDE = 40.716452
LONGITUDE = -73.987041
DATE_STR = "2022-06-02"
START_TIME = "00:00"
END_TIME = "3:00"

def extract_peak_temperature(tcm_result: dict) -> float:
    """
    tcm returns {"map_data": {"features": [...]}, "stats_data": {...}}.
    Try stats_data first (likely a pre-computed summary), fall back to
    scanning all tile features under map_data for the max temperature.
    """
    # Option A: check if stats_data already has a direct peak/max value
    stats = tcm_result.get("stats_data", {})
    if isinstance(stats, dict):
        for key in ("max_temperature", "peak_temperature", "max"):
            if key in stats:
                return stats[key]

    # Option B: fall back to scanning all tiles under map_data
    map_data = tcm_result.get("map_data", {})
    features = map_data.get("features", [])
    max_temps = [
        f["properties"]["max_temperature"]
        for f in features
        if f.get("properties", {}).get("max_temperature") is not None
    ]
    return max(max_temps) if max_temps else None

def print_table(headers: list, rows: list):
    col_widths = [
        max(len(str(headers[i])), max((len(str(row[i])) for row in rows), default=0)) + 2
        for i in range(len(headers))
    ]
    header_line = "".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("".join(str(v).ljust(w) for v, w in zip(row, col_widths)))


print("=== STEP 1: tcm (peak temperature prediction) ===")
tcm_result = create_heatmap(
    latitude=LATITUDE,
    longitude=LONGITUDE,
    start_date=DATE_STR,
    filter_type=2,
    start_time=START_TIME,
    end_time=END_TIME,
    analytic_type="tcm",
)

# --- DEBUG: inspect the actual structure we got back ---
print("\n--- DEBUG: top-level keys ---")
print(list(tcm_result.keys()))
print("\n--- DEBUG: full result (first 1000 chars) ---")
print(str(tcm_result)[:1000])
print("--- END DEBUG ---\n")

peak_temp = extract_peak_temperature(tcm_result)
print(f"--> peak_temp (max across all tiles) = {peak_temp}\n")

if peak_temp is None:
    raise SystemExit("Could not extract peak_temp from tcm result — check the DEBUG output above.")

print("=== STEP 2: env_params (using tcm's peak_temp as baseline) ===")
env_result = get_environmental_parameters(
    latitude=LATITUDE,
    longitude=LONGITUDE,
    temperature=peak_temp,
    start_date=DATE_STR,
    start_time=START_TIME,
    end_time=END_TIME,
    filter_type=2,
    analysis=["heat_index_celsius", "wet_bulb_temperature_celsius", "relative_humidity_percent"],
)

location = env_result["locations"][0]
params = location["parameters"]
timestamps = env_result.get("metadata", {}).get("timestamps", [])

print(f"\nTotal timestamps: {len(timestamps)}\n")

headers = ["Hour", "Heat Index (C)", "Wet Bulb (C)", "Humidity (%)"]
rows = []
for i, ts in enumerate(timestamps):
    hour_label = ts[11:16]
    heat_index = clean_value(params.get("heat_index_celsius", [None] * len(timestamps))[i])
    wet_bulb = clean_value(params.get("wet_bulb_temperature_celsius", [None] * len(timestamps))[i])
    humidity = clean_value(params.get("relative_humidity_percent", [None] * len(timestamps))[i])
    rows.append([hour_label, heat_index, wet_bulb, humidity])

print_table(headers, rows)

print("\n=== DONE ===")
print(f"Baseline peak_temp used: {peak_temp}°C")