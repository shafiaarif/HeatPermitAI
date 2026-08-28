# backend/test_decision_agent.py
from app.agents.decision_agent import get_decision

# High-risk test case (matches our Vegas 3PM-9PM data)
assessment = {
    "risk_score": 93.0,
    "status": "HIGH RISK",
    "peak_temperature": 41.5144,
    "exceedance_hours": 6.0,
    "persistence_hours": 6.0,
    "duration_hours": 6,
}
event = {
    "event_type": "festival",
    "attendance": 5000,
    "start_time": "15:00",
    "end_time": "21:00",
}

decision = get_decision(assessment, event)
print("\n=== DECISION ===")
print(decision.model_dump_json(indent=2))