"""
Window Candidate Finder — searches same-day, realistic-event-hour windows
and ranks them by peak temperature (cheap: one tcm call each). Returns the
TOP 3 candidates (not just the single coldest) so a downstream reasoning
step can weigh trade-offs — e.g. a slightly warmer daytime slot might be
a better real-world recommendation than the coldest slot if that coldest
slot has poor expected attendance.
"""
from app.services.fortyguard_client import create_heatmap
from app.utils.time_validation import validate_same_day_window, InvalidTimeWindowError

# Realistic public-event start hours only — early morning through late
# evening. Deep-night hours are excluded even though they are often
# thermally "safest", because no organizer will realistically schedule
# attendees at that time.
CANDIDATE_START_HOURS = [5, 8, 11, 14, 17, 20]


def _quick_peak_temperature(event, start_time_str: str, end_time_str: str) -> float:
    """Cheapest possible signal: one tcm call, no exceedance/persistence/env_params."""
    result = create_heatmap(
        event.latitude, event.longitude,
        start_date=str(event.event_date), filter_type=2,
        start_time=start_time_str, end_time=end_time_str, analytic_type="tcm",
    )
    temp_stats = result.get("stats_data", {}).get("temperature_stats") or result.get("stats_data", {})
    maximum = temp_stats.get("maximum")
    return maximum if maximum is not None else temp_stats.get("mean", 999.0)


def find_candidate_windows(event, duration_hours: int, top_n: int = 3):
    """
    Returns up to top_n candidates as a list of (start_str, end_str, peak_temp)
    tuples, sorted from coolest to warmest. Skips windows that would cross
    midnight or run past a realistic end time, and skips any candidate
    whose FortyGuard call fails.
    """
    candidates = []

    for start_h in CANDIDATE_START_HOURS:
        end_h = start_h + duration_hours
        if end_h > 23:
            continue

        start_str = f"{start_h:02d}:00"
        end_str = f"{end_h:02d}:00"

        try:
            validate_same_day_window(start_str, end_str)
        except InvalidTimeWindowError:
            continue

        try:
            peak = _quick_peak_temperature(event, start_str, end_str)
            candidates.append((start_str, end_str, peak))
            print(f"  [window_optimizer] Candidate {start_str}-{end_str}: peak={peak}")
        except Exception as e:
            print(f"  [window_optimizer] Candidate {start_str}-{end_str} failed: {e}")
            continue

    candidates.sort(key=lambda c: c[2])
    return candidates[:top_n]