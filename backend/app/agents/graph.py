"""
 LangGraph pipeline:
Node 1 (Event Context) -> Node 2 (Heat Data) -> Node 3 (Risk Scoring)
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.models.db_models import Event
from app.services.heat_data_service import get_event_heat_data
from app.services.timeline_service import get_event_hourly_timeline
from app.services.risk_scoring import compute_risk_score
from app.agents.decision_agent import get_decision
from app.services.what_if_service import assess_window, _compute_exposure_reduction
from app.services.window_optimizer import find_candidate_windows
from app.agents.window_selector_agent import select_best_window
from app.agents.role_recommendation_agent import get_role_recommendations
from app.agents.safety_plan_generator import generate_safety_plan
from app.models.db_models import SafetyPlan, WhatIfComparison, HeatAssessment
from app.utils.time_validation import validate_same_day_window, InvalidTimeWindowError
import datetime as dt


class PipelineState(TypedDict):
    event_id: str
    event: Optional[dict]
    duration_hours: Optional[float]
    heat_data: Optional[dict]
    hourly_timeline: Optional[list]
    risk_assessment: Optional[dict]
    decision: Optional[dict]
    what_if_result: Optional[dict]
    no_safe_alternative: Optional[dict]
    role_recommendations: Optional[dict]
    safety_plan: Optional[dict]


def make_event_context_node(db: Session):
    """Node 1: loads the event from DB, computes its duration in hours."""
    def node(state: PipelineState) -> PipelineState:
        event = db.query(Event).filter(Event.id == state["event_id"]).first()
        if not event:
            raise ValueError(f"Event {state['event_id']} not found")

        start_time_str = str(event.start_time)[:5]
        end_time_str = str(event.end_time)[:5]
        start_h = int(start_time_str.split(":")[0])
        end_h = int(end_time_str.split(":")[0])
        duration = (end_h - start_h) if end_h > start_h else (end_h + 24 - start_h)

        state["event"] = {
            "id": str(event.id),
            "name": event.name,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "event_date": str(event.event_date),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "attendance": event.attendance,
            "_orm": event,
        }
        state["duration_hours"] = duration
        return state
    return node


def make_heat_data_node(db: Session):
    """Node 2: fetches peak temp/exceedance/persistence (cached) + hourly timeline (live)."""
    def node(state: PipelineState) -> PipelineState:
        print("Node 2: fetching heat data...")
        event_ctx = state["event"]
        heat_data = get_event_heat_data(event_ctx["_orm"], db)
        print("Node 2: heat data done, source =", heat_data["source"])
        state["heat_data"] = heat_data

        print("Node 2: starting hourly timeline (1 call)...")
        timeline = get_event_hourly_timeline(
            latitude=event_ctx["latitude"],
            longitude=event_ctx["longitude"],
            date_str=event_ctx["event_date"],
            start_time=event_ctx["start_time"],
            end_time=event_ctx["end_time"],
            baseline_temperature=heat_data["peak_temperature"] or 35.0,
        )
        print("Node 2: timeline done")
        state["hourly_timeline"] = timeline
        return state
    return node


def risk_scoring_node(state: PipelineState) -> PipelineState:
    """Node 3: pure deterministic scoring — no API calls here."""
    heat_data = state["heat_data"]
    risk = compute_risk_score(
        peak_temp=heat_data["peak_temperature"],
        exceedance_hours=heat_data["exceedance_hours"],
        persistence_hours=heat_data["persistence_hours"],
        event_duration_hours=state["duration_hours"],
    )
    state["risk_assessment"] = risk
    return state


def make_decision_node(db: Session):
    """
    Node 4: calls the Decision Agent (LLM) to classify the recommendation.
    If risk is NOT acceptable, finds up to 3 realistic same-day candidate
    windows, fully assesses each one, then asks a SECOND LLM (the Window
    Selector Agent) to reason over the trade-offs and choose which one to
    recommend — not just the mathematically coldest option. Only surfaces
    the recommendation if the chosen window is a genuine improvement
    (LOW or LOW-MODERATE risk); otherwise records that no safe alternative
    exists, so the frontend can explain why the original decision stands.
    """
    ACCEPTABLE_ALTERNATIVE_STATUSES = {"LOW RISK", "LOW-MODERATE RISK"}

    def node(state: PipelineState) -> PipelineState:
        assessment = {**state["risk_assessment"], "duration_hours": state["duration_hours"]}
        event_ctx = state["event"]

        decision = get_decision(assessment, event_ctx)
        state["decision"] = decision.model_dump()

        risk_acceptable = decision.recommendation == "PROCEED"

        if not risk_acceptable:
            print("  [decision_agent] Risk not acceptable — finding candidate windows...")
            top_candidates = find_candidate_windows(
                event_ctx["_orm"], int(state["duration_hours"]), top_n=3
            )

            if not top_candidates:
                print("  [decision_agent] No valid candidate windows found")
                return state

            # Fully assess each candidate (real risk_score, not just peak temp)
            assessed_candidates = []
            for start_str, end_str, _ in top_candidates:
                try:
                    validate_same_day_window(start_str, end_str)
                except InvalidTimeWindowError:
                    continue
                result = assess_window(event_ctx["_orm"], start_str, end_str, db, label="CANDIDATE")
                assessed_candidates.append(result)

            if not assessed_candidates:
                print("  [decision_agent] No candidates passed validation")
                return state

            # Let the Window Selector Agent reason over the trade-offs
            choice = select_best_window(
                candidates=assessed_candidates,
                event_type=event_ctx.get("event_type", "general"),
                attendance=event_ctx.get("attendance", 0),
                current_start=event_ctx["start_time"],
                current_end=event_ctx["end_time"],
                current_risk=state["risk_assessment"]["risk_score"],
                current_status=state["risk_assessment"]["status"],
            )

            chosen = assessed_candidates[choice.chosen_index]

            if chosen["status"] in ACCEPTABLE_ALTERNATIVE_STATUSES:
                print(f"  [decision_agent] Agent recommends: {chosen['start_time']}-{chosen['end_time']} — {choice.reasoning}")
                chosen["selection_reasoning"] = choice.reasoning
                state["what_if_result"] = chosen
            else:
                print(f"  [decision_agent] Even the chosen window is still {chosen['status']} — no safe alternative exists")
                state["no_safe_alternative"] = {
                    "checked_window": f"{chosen['start_time']}-{chosen['end_time']}",
                    "best_status": chosen["status"],
                    "best_risk_score": chosen["risk_score"],
                    "reasoning": choice.reasoning,
                }

        return state
    return node


def role_recommendation_node(state: PipelineState) -> PipelineState:
    """Node 5: LLM-generated, event-specific guidance for 5 personas.
    Falls back to deterministic templates if the LLM call fails."""
    assessment = {**state["risk_assessment"], "duration_hours": state["duration_hours"]}
    event_ctx = state["event"]
    state["role_recommendations"] = get_role_recommendations(assessment, event_ctx)
    return state


def safety_plan_node(state: PipelineState) -> PipelineState:
    """Node 6: deterministic before/during/emergency plan."""
    status = state["risk_assessment"]["status"]
    start_time = state["event"]["start_time"]
    risk_score = state["risk_assessment"]["risk_score"]
    plan = generate_safety_plan(status, start_time, risk_score)
    state["safety_plan"] = plan
    return state


def persistence_node(db: Session):
    """Node 7: writes risk_score/status back onto the current window's
    HeatAssessment row, and persists the SafetyPlan + WhatIfComparison
    (if a what-if was run) as their own DB rows."""
    def node(state: PipelineState) -> PipelineState:
        event_ctx = state["event"]
        start_obj = dt.datetime.strptime(event_ctx["start_time"], "%H:%M").time()
        end_obj = dt.datetime.strptime(event_ctx["end_time"], "%H:%M").time()

        current_row = (
            db.query(HeatAssessment)
            .filter(HeatAssessment.event_id == event_ctx["_orm"].id)
            .filter(HeatAssessment.assessed_start_time == start_obj)
            .filter(HeatAssessment.assessed_end_time == end_obj)
            .order_by(HeatAssessment.fetched_at.desc())
            .first()
        )

        if current_row:
            current_row.risk_score = state["risk_assessment"]["risk_score"]
            current_row.status = state["risk_assessment"]["status"]
            db.commit()

            safety_plan_row = SafetyPlan(
                event_id=event_ctx["_orm"].id,
                heat_assessment_id=current_row.id,
                plan_json=state["safety_plan"],
            )
            db.add(safety_plan_row)
            db.commit()
            print(f"  [persistence] Saved safety plan (id={safety_plan_row.id})")

            what_if = state.get("what_if_result")
            if what_if:
                proposed_start_obj = dt.datetime.strptime(what_if["start_time"], "%H:%M").time()
                proposed_end_obj = dt.datetime.strptime(what_if["end_time"], "%H:%M").time()
                proposed_row = (
                    db.query(HeatAssessment)
                    .filter(HeatAssessment.event_id == event_ctx["_orm"].id)
                    .filter(HeatAssessment.assessed_start_time == proposed_start_obj)
                    .filter(HeatAssessment.assessed_end_time == proposed_end_obj)
                    .order_by(HeatAssessment.fetched_at.desc())
                    .first()
                )
                if proposed_row:
                    current_assessment = {
                        "exceedance_hours": state["risk_assessment"].get("exceedance_hours") or 0,
                        "risk_score": state["risk_assessment"].get("risk_score") or 0,
                    }
                    reduction_pct = _compute_exposure_reduction(current_assessment, what_if)
                    what_if_row = WhatIfComparison(
                        event_id=event_ctx["_orm"].id,
                        current_assessment_id=current_row.id,
                        proposed_assessment_id=proposed_row.id,
                        exposure_reduction_percent=reduction_pct,
                    )
                    db.add(what_if_row)
                    db.commit()
                    print(f"  [persistence] Saved what-if comparison (id={what_if_row.id})")

        return state
    return node


def build_pipeline(db: Session):
    graph = StateGraph(PipelineState)
    graph.add_node("event_context", make_event_context_node(db))
    graph.add_node("heat_data", make_heat_data_node(db))
    graph.add_node("risk_scoring", risk_scoring_node)
    graph.add_node("decision", make_decision_node(db))
    graph.add_node("role_recommendations", role_recommendation_node)
    graph.add_node("safety_plan", safety_plan_node)
    graph.add_node("persistence", persistence_node(db))

    graph.set_entry_point("event_context")
    graph.add_edge("event_context", "heat_data")
    graph.add_edge("heat_data", "risk_scoring")
    graph.add_edge("risk_scoring", "decision")
    graph.add_edge("decision", "role_recommendations")
    graph.add_edge("role_recommendations", "safety_plan")
    graph.add_edge("safety_plan", "persistence")
    graph.add_edge("persistence", END)

    return graph.compile()