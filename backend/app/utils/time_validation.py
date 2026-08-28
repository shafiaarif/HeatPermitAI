"""
Shared time-window validation.

FortyGuard's heatmap API does not reliably support windows that cross
midnight (end_time <= start_time on the same calendar day) — such windows
either return a 500 Internal Server Error, or hang/stall on the polling
side until they time out. Until that's supported, we reject same-day
windows where the end time isn't after the start time.
"""


class InvalidTimeWindowError(ValueError):
    """Raised when a start/end time pair isn't a valid same-day window."""
    pass


def validate_same_day_window(start_time_str: str, end_time_str: str) -> None:
    """
    Raises InvalidTimeWindowError if end_time is not strictly after start_time
    on the same day (i.e. the window would cross midnight).

    Expects "HH:MM" or "HH:MM:SS" formatted strings.
    """
    start_h, start_m = _parse_hm(start_time_str)
    end_h, end_m = _parse_hm(end_time_str)

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if end_minutes <= start_minutes:
        raise InvalidTimeWindowError(
            f"End time ({end_time_str}) must be after start time ({start_time_str}) "
            "on the same day. Overnight windows crossing midnight aren't supported yet — "
            "please split the event into two same-day windows, or choose times where "
            "the end is later than the start."
        )


def _parse_hm(time_str: str) -> tuple[int, int]:
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])