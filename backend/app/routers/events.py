import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.heat_data_service import get_event_heat_data, get_event_heatmap_tiles
from app.services.what_if_service import run_what_if_comparison
from app.schemas import EventCreate, EventResponse
from app.models.db_models import Event, HeatAssessment, SafetyPlan, WhatIfComparison
from app.services.heat_intelligence_service import generate_heat_intelligence_report
from fastapi.responses import FileResponse
from app.utils.time_validation import validate_same_day_window, InvalidTimeWindowError

router = APIRouter(prefix="/api/events", tags=["events"])

from app.agents.graph import build_pipeline


@router.post("/{event_id}/assess")
def assess_event(event_id: str, db: Session = Depends(get_db)):
    pipeline = build_pipeline(db)

    try:
        final_state = pipeline.invoke({"event_id": event_id})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    return {
        "event_id": event_id,
        "event_name": final_state["event"]["name"],
        "duration_hours": final_state["duration_hours"],
        **final_state["risk_assessment"],
        "hourly_timeline": final_state["hourly_timeline"],
        "decision": final_state.get("decision"),
        "what_if_evidence": final_state.get("what_if_result"),
    }


@router.get("/{event_id}/heat-data")
def get_heat_data(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        heat_data = get_event_heat_data(event, db)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    return {"event_id": str(event.id), "event_name": event.name, **heat_data}


@router.get("/{event_id}/heatmap-tiles")
def get_heatmap_tiles(event_id: str, db: Session = Depends(get_db)):
    """
    Returns the full spatial tile grid (lat/lng bounding boxes + temperature)
    for the event's location, used to render a color-coded heat map on the
    frontend — not just the single peak_temperature value.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        result = get_event_heatmap_tiles(event, db)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    return {"event_id": str(event.id), "event_name": event.name, **result}


@router.post("/{event_id}/what-if")
def what_if(event_id: str, proposed_start_time: str, proposed_end_time: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        result = run_what_if_comparison(event, proposed_start_time, proposed_end_time, db)
    except InvalidTimeWindowError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    return {"event_id": event_id, "event_name": event.name, **result}


@router.post("/{event_id}/decision")
def get_full_decision_bundle(event_id: str, db: Session = Depends(get_db)):
    """
    Day 6 deliverable: full bundle in one response — assessment, decision,
    role-specific recommendations, and the safety plan. Also includes
    no_safe_alternative when the system checked candidate windows but
    none brought the risk down to an acceptable level.
    """
    pipeline = build_pipeline(db)

    try:
        final_state = pipeline.invoke({"event_id": event_id})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    return {
        "event_id": event_id,
        "event_name": final_state["event"]["name"],
        "assessment": {
            "duration_hours": final_state["duration_hours"],
            **final_state["risk_assessment"],
            "hourly_timeline": final_state["hourly_timeline"],
        },
        "decision": final_state.get("decision"),
        "what_if_evidence": final_state.get("what_if_result"),
        "no_safe_alternative": final_state.get("no_safe_alternative"),
        "role_recommendations": final_state.get("role_recommendations"),
        "safety_plan": final_state.get("safety_plan"),
    }


@router.post("", response_model=EventResponse, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    """Day 7 prerequisite: lets the frontend create a new event."""
    try:
        validate_same_day_window(str(payload.start_time), str(payload.end_time))
    except InvalidTimeWindowError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_event = Event(
        name=payload.name,
        event_type=payload.event_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        event_date=payload.event_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        attendance=payload.attendance,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


@router.get("", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    """Returns all events, most recent first — used by the frontend's event list."""
    events = db.query(Event).order_by(Event.created_at.desc()).all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Basic event detail — no FortyGuard calls, just DB lookup."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """
    Deletes an event AND everything that references it — WhatIfComparison
    and SafetyPlan rows first (they have foreign keys into HeatAssessment),
    then HeatAssessment, then the event itself. Deleting in the wrong order
    trips a foreign key violation if the event has ever been fully assessed
    (i.e. /decision or /assess was run on it).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.query(WhatIfComparison).filter(WhatIfComparison.event_id == event_id).delete()
    db.query(SafetyPlan).filter(SafetyPlan.event_id == event_id).delete()
    db.query(HeatAssessment).filter(HeatAssessment.event_id == event_id).delete()
    db.delete(event)
    db.commit()
    return None


@router.get("/{event_id}/history")
def get_event_history(event_id: str, db: Session = Depends(get_db)):
    """Returns all past safety plans and what-if comparisons for an event —
    demonstrates the audit-trail value of persisting agent outputs."""
    plans = db.query(SafetyPlan).filter(SafetyPlan.event_id == event_id).order_by(SafetyPlan.created_at.desc()).all()
    what_ifs = db.query(WhatIfComparison).filter(WhatIfComparison.event_id == event_id).order_by(WhatIfComparison.created_at.desc()).all()

    return {
        "event_id": event_id,
        "safety_plans": [{"id": str(p.id), "plan": p.plan_json, "created_at": p.created_at.isoformat()} for p in plans],
        "what_if_comparisons": [
            {"id": str(w.id), "exposure_reduction_percent": w.exposure_reduction_percent, "created_at": w.created_at.isoformat()}
            for w in what_ifs
        ],
    }


@router.get("/{event_id}/summary")
def get_event_summary(event_id: str, db: Session = Depends(get_db)):
    """
    Human-readable 2-3 sentence summary — meant to be quoted directly in
    a pitch/demo rather than parsing raw JSON. Reuses the full pipeline
    so the summary always reflects the latest assessment.
    """
    pipeline = build_pipeline(db)

    try:
        final_state = pipeline.invoke({"event_id": event_id})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard error: {str(e)}")

    event_name = final_state["event"]["name"]
    risk = final_state["risk_assessment"]
    decision = final_state.get("decision") or {}
    what_if = final_state.get("what_if_result")

    lines = [f"{event_name} is currently {risk['status']} (score {risk['risk_score']}/100), "
             f"with a peak temperature of {risk['peak_temperature']}°C over its scheduled window."]

    recommendation = decision.get("recommendation")
    if recommendation and recommendation != "PROCEED":
        lines.append(f"The Decision Agent recommends {recommendation}: {decision.get('reasoning', '')}")
    elif recommendation == "PROCEED":
        lines.append("The Decision Agent recommends proceeding as scheduled with standard precautions.")

    if what_if:
        lines.append(
            f"Moving the event to {what_if['start_time']}-{what_if['end_time']} would change the "
            f"risk status to {what_if['status']} (score {what_if['risk_score']}/100)."
        )

    return {
        "event_id": event_id,
        "event_name": event_name,
        "summary": " ".join(lines),
    }


@router.post("/{event_id}/intelligence-report")
def get_intelligence_report(event_id: str, db: Session = Depends(get_db)):
    """
    Premium-tier: generates a full Heat Intelligence PDF for the event's
    location, using its assessed peak temperature as the anchor value.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    heat_data = get_event_heat_data(event, db)

    try:
        file_path = generate_heat_intelligence_report(
            latitude=event.latitude,
            longitude=event.longitude,
            temperature=heat_data["peak_temperature"] or 35.0,
            date_str=str(event.event_date),
            analysis=["environmental", "events"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Heat Intelligence error: {str(e)}")

    return FileResponse(file_path, media_type="application/pdf", filename=os.path.basename(file_path))