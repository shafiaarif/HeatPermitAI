"""
Deterministic Heat Risk Score engine — pure function, unit-testable.
No DB/API calls here. Score 0-100, built from peak temperature,
exceedance hours, and persistence hours relative to event duration.
"""

def compute_risk_score(peak_temp: float, exceedance_hours: float,
                        persistence_hours: float, event_duration_hours: float) -> dict:
    """
    Weights: temperature 40%, exceedance 35%, persistence 25%.
    """
    if event_duration_hours <= 0:
        raise ValueError("event_duration_hours must be positive")
    if peak_temp is None:
        raise ValueError("peak_temp is required")

    temp_score = min(100, max(0, (peak_temp - 25) / (45 - 25) * 100))
    exceedance_ratio = min(1.0, (exceedance_hours or 0.0) / event_duration_hours)
    exceedance_score = exceedance_ratio * 100
    persistence_score = min(100, ((persistence_hours or 0.0) / event_duration_hours) * 100)

    final_score = round(temp_score * 0.40 + exceedance_score * 0.35 + persistence_score * 0.25, 1)

    if final_score >= 75:
        status = "HIGH RISK"
    elif final_score >= 50:
        status = "MODERATE RISK"
    elif final_score >= 25:
        status = "LOW-MODERATE RISK"
    else:
        status = "LOW RISK"

    return {
        "risk_score": final_score,
        "status": status,
        "peak_temperature": peak_temp,
        "exceedance_hours": exceedance_hours,
        "persistence_hours": persistence_hours,
    }


def classify_hourly_tier(heat_index: float = None, wet_bulb_temp: float = None) -> str:
    """
    4-tier classifier for a single hour. Takes the more severe of the two
    metrics — wet_bulb alone under-estimates dry-heat risk (lesson from
    testing Phoenix vs. humid-city data).
    """
    values = [v for v in (heat_index, wet_bulb_temp) if v is not None]
    if not values:
        return "Unknown"
    worst = max(values)

    if worst > 40:
        return "Extreme"
    elif worst >= 35:
        return "Danger"
    elif worst >= 30:
        return "Caution"
    else:
        return "Safe"


def generate_hour_range(start_time: str, end_time: str) -> list[str]:
    """
    Returns ['HH:00', ...] from start_time to end_time (exclusive of end).
    Handles overnight events (e.g. '22:00' to '02:00' wraps past midnight).
    """
    start_h = int(start_time.split(":")[0])
    end_h = int(end_time.split(":")[0])

    if end_h <= start_h:
        end_h += 24

    return [f"{h % 24:02d}:00" for h in range(start_h, end_h)]