"""
Safety Plan Generator —
Deterministic (NOT LLM): before-event action timeline, during-event
monitoring interval, emergency trigger condition. Times are computed
relative to the event's actual start_time.
"""
from datetime import datetime, timedelta


def _subtract_minutes(time_str: str, minutes: int) -> str:
    """time_str: 'HH:MM' -> returns 'HH:MM' shifted earlier by `minutes`."""
    t = datetime.strptime(time_str, "%H:%M")
    shifted = t - timedelta(minutes=minutes)
    return shifted.strftime("%H:%M")


def generate_safety_plan(status: str, start_time: str, risk_score: float) -> dict:
    """
    status: risk status string (HIGH RISK / MODERATE RISK / ...)
    start_time: event's start time as 'HH:MM'
    risk_score: 0-100, used to set the emergency trigger threshold
    """
    before_event = [
        {"time": _subtract_minutes(start_time, 60), "action": "Send heat advisory to attendees (SMS/app notification/signage)"},
        {"time": _subtract_minutes(start_time, 30), "action": "Activate hydration stations and confirm cooling equipment is operational"},
        {"time": start_time, "action": "Open cooling/shaded areas; brief on-site staff on the heat response plan"},
    ]

    monitor_interval_minutes = 15 if status == "HIGH RISK" else 30

    return {
        "before_event": before_event,
        "during_event": {
            "monitor_interval_minutes": monitor_interval_minutes,
            "monitoring_note": f"Re-check live conditions every {monitor_interval_minutes} minutes during the event.",
        },
        "emergency_trigger": {
            "condition": f"On-site heat index exceeds 40°C for 30+ continuous minutes, OR risk score (currently {risk_score}) is reassessed above 90",
            "action": "Pause outdoor activities, direct attendees to cooling areas, notify event operations and medical teams immediately.",
        },
    }