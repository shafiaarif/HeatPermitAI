"""
Heat Intelligence Report Generator — Premium-tier feature.
Unlike heatmap/env_params, this endpoint returns a PDF (via a temporary
download_link), not JSON data. Report generation can take several minutes.
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.fortyguard.com/v1"
API_KEY = os.getenv("FORTYGUARD_API_KEY")
HEADERS = {"api-key": API_KEY}

REPORT_POLL_ATTEMPTS = 60   # up to 5 min (report generation is slower than other endpoints)
REPORT_POLL_DELAY = 5


def generate_heat_intelligence_report(
    latitude: float, longitude: float, temperature: float, date_str: str,
    analysis: list = None, output_dir: str = "reports"
) -> str:
    """
    Submits a Heat Intelligence request, polls until the PDF is ready,
    downloads it, and returns the local file path.
    """
    analysis = analysis or ["environmental", "events"]

    print(f"  [heat_intelligence] Submitting report request...")
    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "temperature": temperature,
        "date": date_str,
        "analysis": analysis,
    }
    resp = requests.post(f"{BASE_URL}/heat_intelligence", headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("error"):
        raise ValueError(f"Heat Intelligence error: {data.get('message')}")

    activity_id = data["data"]["activity_id"]
    print(f"  [heat_intelligence] Submitted — activity_id={activity_id}")

    status_url = f"{BASE_URL}/status/{activity_id}"
    for attempt in range(REPORT_POLL_ATTEMPTS):
        try:
            status_resp = requests.get(status_url, headers=HEADERS, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"  [heat_intelligence] Transient network error ({type(e).__name__}) — retrying...")
            time.sleep(REPORT_POLL_DELAY)
            continue

        status_resp.raise_for_status()
        result_data = status_resp.json()["data"]
        status = (result_data.get("status") or "").lower()

        if status in ("completed", "succeeded"):
            download_link = (result_data.get("result") or {}).get("download_link")
            if not download_link:
                raise RuntimeError(f"Activity {activity_id} completed without a download_link")

            print(f"  [heat_intelligence] Report ready — downloading...")
            report_resp = requests.get(download_link, timeout=60)
            report_resp.raise_for_status()

            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, f"heat_intelligence_{activity_id}.pdf")
            with open(file_path, "wb") as f:
                f.write(report_resp.content)

            print(f"  [heat_intelligence] Saved to {file_path}")
            return file_path

        if status == "failed":
            raise RuntimeError(f"Heat Intelligence activity {activity_id} failed")

        if attempt % 6 == 0 and attempt > 0:
            print(f"  [heat_intelligence] Still processing... ({attempt * REPORT_POLL_DELAY}s elapsed)")
        time.sleep(REPORT_POLL_DELAY)

    raise TimeoutError(f"Heat Intelligence report did not complete in time")