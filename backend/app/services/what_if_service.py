# """
# What-If Simulator — Day 4 deliverable.
# Re-runs Heat Data + Risk Scoring for both the event's current schedule
# and a proposed alternate window, then compares them. Caches the hourly
# timeline alongside heat_data so re-testing the same window is instant.
# """
# from datetime import datetime
# from sqlalchemy.orm import Session
# from app.models.db_models import Event, HeatAssessment
# from app.services.heat_data_service import get_event_heat_data
# from app.services.timeline_service import get_event_hourly_timeline
# from app.services.risk_scoring import compute_risk_score
# from app.utils.time_validation import validate_same_day_window, InvalidTimeWindowError


# def _duration_hours(start_time_str: str, end_time_str: str) -> float:
#     start_h = int(start_time_str.split(":")[0])
#     end_h = int(end_time_str.split(":")[0])
#     return (end_h - start_h) if end_h > start_h else (end_h + 24 - start_h)


# def _save_timeline_to_cache(event, start_time_str, end_time_str, timeline, db):
#     start_obj = datetime.strptime(start_time_str, "%H:%M").time()
#     end_obj = datetime.strptime(end_time_str, "%H:%M").time()

#     row = (
#         db.query(HeatAssessment)
#         .filter(HeatAssessment.event_id == event.id)
#         .filter(HeatAssessment.assessed_start_time == start_obj)
#         .filter(HeatAssessment.assessed_end_time == end_obj)
#         .order_by(HeatAssessment.fetched_at.desc())
#         .first()
#     )
#     if row:
#         existing = row.raw_response or {}
#         existing["hourly_timeline"] = timeline
#         row.raw_response = existing
#         db.commit()
#         print(f"  [timeline] Saved to cache for future reuse")


# def assess_window(event: Event, start_time_str: str, end_time_str: str, db: Session, label: str = "") -> dict:
#     print(f"[{label}] Assessing window {start_time_str}-{end_time_str}...")

#     print(f"[{label}] Fetching heat data (peak temp, exceedance, persistence)...")
#     heat_data = get_event_heat_data(event, db, start_time=start_time_str, end_time=end_time_str)
#     print(f"[{label}] Heat data done — source={heat_data['source']}, peak_temp={heat_data['peak_temperature']}")

#     duration = _duration_hours(start_time_str, end_time_str)

#     risk = compute_risk_score(
#         peak_temp=heat_data["peak_temperature"],
#         exceedance_hours=heat_data["exceedance_hours"],
#         persistence_hours=heat_data["persistence_hours"],
#         event_duration_hours=duration,
#     )
#     print(f"[{label}] Risk score computed: {risk['risk_score']} ({risk['status']})")

#     cached_timeline = heat_data.get("cached_timeline")
#     if cached_timeline:
#         print(f"[{label}] Timeline CACHE HIT — skipping live fetch")
#         timeline = cached_timeline
#     else:
#         print(f"[{label}] Starting hourly timeline (1 call)...")
#         timeline = get_event_hourly_timeline(
#             latitude=event.latitude, longitude=event.longitude,
#             date_str=str(event.event_date),
#             start_time=start_time_str, end_time=end_time_str,
#             baseline_temperature=heat_data["peak_temperature"] or 35.0,
#         )
#         print(f"[{label}] Timeline done — {len(timeline)} hours processed")
#         _save_timeline_to_cache(event, start_time_str, end_time_str, timeline, db)

#     return {
#         "start_time": start_time_str,
#         "end_time": end_time_str,
#         "duration_hours": duration,
#         **risk,
#         "hourly_timeline": timeline,
#     }


# def _compute_exposure_reduction(current: dict, proposed: dict) -> float:
#     """
#     Computes how much safer (or riskier) the proposed window is vs the current one.

#     Primary metric: exceedance_hours (time spent above the 35C danger threshold) —
#     this is the most direct measure of dangerous heat exposure.

#     Fallback: if neither window has any exceedance hours (both are "Safe"/"Caution"
#     with 0.0 exceedance — common for low-risk events), we fall back to comparing
#     risk_score instead, so the metric doesn't just silently return None.

#     Note: using `> 0` explicitly here instead of truthy `if current["exceedance_hours"]`,
#     because in Python 0.0 is falsy — the old code's `if current["exceedance_hours"]:`
#     check was skipped whenever exceedance was exactly 0.0, causing this to always
#     return None for any low-risk comparison.
#     """
#     if current["exceedance_hours"] > 0:
#         return round(
#             (1 - proposed["exceedance_hours"] / current["exceedance_hours"]) * 100, 1
#         )

#     if current["risk_score"] > 0:
#         return round(
#             (1 - proposed["risk_score"] / current["risk_score"]) * 100, 1
#         )

#     # Both windows are essentially risk-free — nothing meaningful to reduce
#     return 0.0


# def run_what_if_comparison(event: Event, proposed_start_time: str, proposed_end_time: str, db: Session) -> dict:
#     current_start = str(event.start_time)[:5]
#     current_end = str(event.end_time)[:5]

#     # Validate both windows before making any FortyGuard calls. FortyGuard's
#     # heatmap API doesn't reliably support windows that cross midnight — they
#     # either 500 or hang until timeout. Reject early with a clear message
#     # instead of burning 1-2 minutes on calls that will fail anyway.
#     validate_same_day_window(current_start, current_end)
#     validate_same_day_window(proposed_start_time, proposed_end_time)

#     print("=" * 50)
#     print("WHAT-IF COMPARISON STARTED")
#     print("=" * 50)

#     current = assess_window(event, current_start, current_end, db, label="CURRENT")
#     print("-" * 50)
#     proposed = assess_window(event, proposed_start_time, proposed_end_time, db, label="PROPOSED")

#     print("=" * 50)
#     print("BOTH WINDOWS ASSESSED — computing comparison...")

#     reduction_pct = _compute_exposure_reduction(current, proposed)

#     print(f"Exposure reduction: {reduction_pct}%")
#     print("WHAT-IF COMPARISON COMPLETE")
#     print("=" * 50)

#     return {
#         "current_schedule": current,
#         "proposed_schedule": proposed,
#         "exposure_reduction_percent": reduction_pct,
#     }

"""
What-If Simulator — Day 4 deliverable.
Re-runs Heat Data + Risk Scoring for both the event's current schedule
and a proposed alternate window, then compares them. Caches the hourly
timeline alongside heat_data so re-testing the same window is instant.
Also persists the comparison as a WhatIfComparison row, so manual
What-If tests show up in the event's History tab — not just the
automatic comparisons the Decision Agent triggers internally.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.db_models import Event, HeatAssessment, WhatIfComparison
from app.services.heat_data_service import get_event_heat_data
from app.services.timeline_service import get_event_hourly_timeline
from app.services.risk_scoring import compute_risk_score
from app.utils.time_validation import validate_same_day_window, InvalidTimeWindowError


def _duration_hours(start_time_str: str, end_time_str: str) -> float:
    start_h = int(start_time_str.split(":")[0])
    end_h = int(end_time_str.split(":")[0])
    return (end_h - start_h) if end_h > start_h else (end_h + 24 - start_h)


def _save_timeline_to_cache(event, start_time_str, end_time_str, timeline, db):
    start_obj = datetime.strptime(start_time_str, "%H:%M").time()
    end_obj = datetime.strptime(end_time_str, "%H:%M").time()

    row = (
        db.query(HeatAssessment)
        .filter(HeatAssessment.event_id == event.id)
        .filter(HeatAssessment.assessed_start_time == start_obj)
        .filter(HeatAssessment.assessed_end_time == end_obj)
        .order_by(HeatAssessment.fetched_at.desc())
        .first()
    )
    if row:
        existing = row.raw_response or {}
        existing["hourly_timeline"] = timeline
        row.raw_response = existing
        db.commit()
        print(f"  [timeline] Saved to cache for future reuse")


def _get_heat_assessment_row(event: Event, start_time_str: str, end_time_str: str, db: Session):
    """Finds the most recent HeatAssessment row for this event + window —
    used to link a WhatIfComparison to its underlying assessed windows."""
    start_obj = datetime.strptime(start_time_str, "%H:%M").time()
    end_obj = datetime.strptime(end_time_str, "%H:%M").time()

    return (
        db.query(HeatAssessment)
        .filter(HeatAssessment.event_id == event.id)
        .filter(HeatAssessment.assessed_start_time == start_obj)
        .filter(HeatAssessment.assessed_end_time == end_obj)
        .order_by(HeatAssessment.fetched_at.desc())
        .first()
    )


def assess_window(event: Event, start_time_str: str, end_time_str: str, db: Session, label: str = "") -> dict:
    print(f"[{label}] Assessing window {start_time_str}-{end_time_str}...")

    print(f"[{label}] Fetching heat data (peak temp, exceedance, persistence)...")
    heat_data = get_event_heat_data(event, db, start_time=start_time_str, end_time=end_time_str)
    print(f"[{label}] Heat data done — source={heat_data['source']}, peak_temp={heat_data['peak_temperature']}")

    duration = _duration_hours(start_time_str, end_time_str)

    risk = compute_risk_score(
        peak_temp=heat_data["peak_temperature"],
        exceedance_hours=heat_data["exceedance_hours"],
        persistence_hours=heat_data["persistence_hours"],
        event_duration_hours=duration,
    )
    print(f"[{label}] Risk score computed: {risk['risk_score']} ({risk['status']})")

    cached_timeline = heat_data.get("cached_timeline")
    if cached_timeline:
        print(f"[{label}] Timeline CACHE HIT — skipping live fetch")
        timeline = cached_timeline
    else:
        print(f"[{label}] Starting hourly timeline (1 call)...")
        timeline = get_event_hourly_timeline(
            latitude=event.latitude, longitude=event.longitude,
            date_str=str(event.event_date),
            start_time=start_time_str, end_time=end_time_str,
            baseline_temperature=heat_data["peak_temperature"] or 35.0,
        )
        print(f"[{label}] Timeline done — {len(timeline)} hours processed")
        _save_timeline_to_cache(event, start_time_str, end_time_str, timeline, db)

    return {
        "start_time": start_time_str,
        "end_time": end_time_str,
        "duration_hours": duration,
        **risk,
        "hourly_timeline": timeline,
    }


def _compute_exposure_reduction(current: dict, proposed: dict) -> float:
    """
    Computes how much safer (or riskier) the proposed window is vs the current one.

    Primary metric: exceedance_hours (time spent above the 35C danger threshold) —
    this is the most direct measure of dangerous heat exposure.

    Fallback: if neither window has any exceedance hours (both are "Safe"/"Caution"
    with 0.0 exceedance — common for low-risk events), we fall back to comparing
    risk_score instead, so the metric doesn't just silently return None.

    Note: using `> 0` explicitly here instead of truthy `if current["exceedance_hours"]`,
    because in Python 0.0 is falsy — the old code's `if current["exceedance_hours"]:`
    check was skipped whenever exceedance was exactly 0.0, causing this to always
    return None for any low-risk comparison.
    """
    if current["exceedance_hours"] > 0:
        return round(
            (1 - proposed["exceedance_hours"] / current["exceedance_hours"]) * 100, 1
        )

    if current["risk_score"] > 0:
        return round(
            (1 - proposed["risk_score"] / current["risk_score"]) * 100, 1
        )

    # Both windows are essentially risk-free — nothing meaningful to reduce
    return 0.0


def run_what_if_comparison(event: Event, proposed_start_time: str, proposed_end_time: str, db: Session) -> dict:
    current_start = str(event.start_time)[:5]
    current_end = str(event.end_time)[:5]

    # Validate both windows before making any FortyGuard calls. FortyGuard's
    # heatmap API doesn't reliably support windows that cross midnight — they
    # either 500 or hang until timeout. Reject early with a clear message
    # instead of burning 1-2 minutes on calls that will fail anyway.
    validate_same_day_window(current_start, current_end)
    validate_same_day_window(proposed_start_time, proposed_end_time)

    print("=" * 50)
    print("WHAT-IF COMPARISON STARTED")
    print("=" * 50)

    current = assess_window(event, current_start, current_end, db, label="CURRENT")
    print("-" * 50)
    proposed = assess_window(event, proposed_start_time, proposed_end_time, db, label="PROPOSED")

    print("=" * 50)
    print("BOTH WINDOWS ASSESSED — computing comparison...")

    reduction_pct = _compute_exposure_reduction(current, proposed)

    print(f"Exposure reduction: {reduction_pct}%")

    # Persist this comparison so it shows up in the History tab — manual
    # What-If Simulator runs were previously never saved, only the
    # automatic ones the Decision Agent triggers internally.
    current_row = _get_heat_assessment_row(event, current_start, current_end, db)
    proposed_row = _get_heat_assessment_row(event, proposed_start_time, proposed_end_time, db)

    if current_row and proposed_row:
        comparison_row = WhatIfComparison(
            event_id=event.id,
            current_assessment_id=current_row.id,
            proposed_assessment_id=proposed_row.id,
            exposure_reduction_percent=reduction_pct,
        )
        db.add(comparison_row)
        db.commit()
        print(f"  [persistence] Saved manual what-if comparison (id={comparison_row.id})")
    else:
        print("  [persistence] Could not find matching HeatAssessment rows — comparison not saved")

    print("WHAT-IF COMPARISON COMPLETE")
    print("=" * 50)

    return {
        "current_schedule": current,
        "proposed_schedule": proposed,
        "exposure_reduction_percent": reduction_pct,
    }