"""
Shared async status polling utility for FortyGuard's submit-then-poll pattern.
Used by every analysis endpoint (heatmap, env_params) — none of them are synchronous.
"""
import time
import requests

BASE_URL = "https://api.fortyguard.com/v1"


class FortyGuardTaskFailed(Exception):
    pass


class FortyGuardTaskTimeout(Exception):
    pass


def poll_until_complete(activity_id: str, headers: dict, max_attempts: int = 100, delay_seconds: int = 3) -> dict:
    """
    Status strings match case-insensitively ('Completed', 'completed', 'succeeded' all terminate).
    A transient 404 right after submit is normal (the id exists before the record does) — retry.
    Transient network errors (read timeouts, connection resets) are also retried instead of
    crashing the whole request — FortyGuard occasionally responds slowly to a single status
    check, and that shouldn't fail the entire polling loop.
    Prints progress every 5 attempts so it's clear this is actively polling, not stuck.
    """
    print(f"    [poller] Waiting on activity {activity_id}...")

    for attempt in range(max_attempts):
        try:
            resp = requests.get(f"{BASE_URL}/status/{activity_id}", headers=headers, timeout=15)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"    [poller] Transient network error ({type(e).__name__}) — retrying...")
            time.sleep(delay_seconds)
            continue

        if resp.status_code == 404 and attempt < 3:
            time.sleep(delay_seconds)
            continue

        resp.raise_for_status()
        data = resp.json()

        if data.get("error"):
            raise FortyGuardTaskFailed(f"Activity {activity_id} error: {data.get('message')}")

        status = (data.get("data", {}).get("status") or "").lower()

        if status in ("completed", "succeeded"):
            elapsed = attempt * delay_seconds
            print(f"    [poller] Completed after ~{elapsed}s ({attempt + 1} attempts)")
            return data["data"]["result"]
        if status == "failed":
            raise FortyGuardTaskFailed(f"Activity {activity_id} failed")

        if attempt % 5 == 0 and attempt > 0:
            elapsed = attempt * delay_seconds
            print(f"    [poller] Still processing... ({elapsed}s elapsed, attempt {attempt}/{max_attempts})")

        time.sleep(delay_seconds)

    raise FortyGuardTaskTimeout(f"Activity {activity_id} did not complete in time")