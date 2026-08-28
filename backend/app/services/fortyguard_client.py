

"""
FortyGuard API client — polygon builder + heatmap wrapper + env_params wrapper.
Wraps both in a retry layer: if a submitted job doesn't complete within a
short window, we abandon it and submit a FRESH request rather than keep
polling an activity that may be stuck server-side — fresh submissions are
consistently fast in practice, unlike waiting on an already-stuck job.
"""
import os
import requests
from dotenv import load_dotenv
from app.services.status_poller import poll_until_complete, FortyGuardTaskTimeout

load_dotenv()

BASE_URL = "https://api.fortyguard.com/v1"
API_KEY = os.getenv("FORTYGUARD_API_KEY")
HEADERS = {"api-key": API_KEY}

MAX_SUBMIT_RETRIES = 2
POLL_ATTEMPTS_PER_TRY = 30


def build_polygon_from_center(latitude: float, longitude: float, delta: float = 0.02) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [longitude - delta, latitude - delta],
                    [longitude + delta, latitude - delta],
                    [longitude + delta, latitude + delta],
                    [longitude - delta, latitude + delta],
                    [longitude - delta, latitude - delta],
                ]]
            }
        }]
    }


def _submit_and_poll(url: str, payload: dict, label: str) -> dict:
    last_error = None

    for attempt in range(1, MAX_SUBMIT_RETRIES + 2):
        print(f"  [{label}] Submit attempt {attempt}...")
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("error"):
            raise ValueError(f"{label} error: {data.get('message')}")

        activity_id = data["data"]["activity_id"]

        try:
            return poll_until_complete(activity_id, HEADERS, max_attempts=POLL_ATTEMPTS_PER_TRY, delay_seconds=3)
        except FortyGuardTaskTimeout as e:
            last_error = e
            print(f"  [{label}] Attempt {attempt} stalled after ~{POLL_ATTEMPTS_PER_TRY * 3}s — retrying with a fresh request...")
            continue

    raise last_error


def create_heatmap(
    latitude: float, longitude: float, start_date: str, filter_type: int = 1,
    start_time: str = None, end_time: str = None, end_date: str = None,
    granularity: int = 100, analytic_type: str = "tcm",
    threshold: float = 30.0, direction: str = "above",
) -> dict:
    date_time = {"start_date": start_date, "filter_type": filter_type}
    if filter_type in (1, 2) and start_time:
        date_time["start_time"] = start_time
    if filter_type == 2 and end_time:
        date_time["end_time"] = end_time
    if filter_type == 4 and end_date:
        date_time["end_date"] = end_date

    payload = {
        "polygon_aoi": build_polygon_from_center(latitude, longitude),
        "date_time": date_time,
        "granularity": granularity,
        "analytic_type": analytic_type,
    }
    if analytic_type in ("exceedance", "persistence"):
        payload["threshold"] = threshold
        payload["direction"] = direction

    return _submit_and_poll(f"{BASE_URL}/heatmap", payload, label=f"heatmap:{analytic_type}")


def get_environmental_parameters(
    latitude: float, longitude: float, temperature: float, start_date: str,
    filter_type: int = 1, start_time: str = None, end_time: str = None,
    end_date: str = None, analysis: list = None,
) -> dict:
    date_time = {"start_date": start_date, "filter_type": filter_type}
    if filter_type in (1, 2) and start_time:
        date_time["start_time"] = start_time
    if filter_type == 2 and end_time:
        date_time["end_time"] = end_time
    if filter_type == 4 and end_date:
        date_time["end_date"] = end_date

    payload = {
        "latitude": latitude, "longitude": longitude,
        "temperature": temperature, "date_time": date_time,
    }
    if analysis:
        payload["analysis"] = analysis

    return _submit_and_poll(f"{BASE_URL}/env_params", payload, label="env_params")


def clean_value(v):
    if v is None or v == -999:
        return None
    return v