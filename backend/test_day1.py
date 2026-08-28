import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from app.services.fortyguard_client import create_heatmap, get_environmental_parameters, clean_value

LAT, LON = 33.4484, -112.0740  # Phoenix, AZ
DATE = "2024-07-15"

print("=== Heatmap: tcm, single day ===")
tcm_result = create_heatmap(LAT, LON, start_date=DATE, filter_type=3, analytic_type="tcm")
print(tcm_result.get("stats_data", {}).get("Temperature_stats") or tcm_result.get("stats_data"))

print("\n=== Heatmap: exceedance, range of days ===")
exc_result = create_heatmap(
    LAT, LON, start_date=DATE, end_date="2024-07-21", filter_type=4,
    analytic_type="exceedance", threshold=35.0, direction="above"
)
print(exc_result.get("stats_data"))

print("\n=== Heatmap: persistence, range of days ===")
per_result = create_heatmap(
    LAT, LON, start_date=DATE, end_date="2024-07-21", filter_type=4,
    analytic_type="persistence", threshold=35.0, direction="above"
)
print(per_result.get("stats_data"))

print("\n=== Environmental Parameters ===")
env_result = get_environmental_parameters(
    LAT, LON, temperature=40.0, start_date=DATE, filter_type=1, start_time="14:00",
    analysis=["heat_index_celsius", "wet_bulb_temperature_celsius", "relative_humidity_percent"]
)
loc = env_result["locations"][0]["parameters"]
print("heat_index:", clean_value(loc["heat_index_celsius"][0]))
print("wet_bulb  :", clean_value(loc["wet_bulb_temperature_celsius"][0]))
print("humidity  :", clean_value(loc["relative_humidity_percent"][0]))