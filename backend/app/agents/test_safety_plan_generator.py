from app.agents.safety_plan_generator import generate_safety_plan, _subtract_minutes

def test_subtract_minutes_basic():
    assert _subtract_minutes("15:00", 60) == "14:00"

def test_subtract_minutes_crosses_midnight():
    assert _subtract_minutes("00:30", 60) == "23:30"

def test_high_risk_has_shorter_monitoring_interval():
    plan = generate_safety_plan("HIGH RISK", "15:00", 93.0)
    assert plan["during_event"]["monitor_interval_minutes"] == 15

def test_moderate_risk_has_longer_monitoring_interval():
    plan = generate_safety_plan("MODERATE RISK", "15:00", 60.0)
    assert plan["during_event"]["monitor_interval_minutes"] == 30

def test_before_event_has_three_steps():
    plan = generate_safety_plan("HIGH RISK", "15:00", 93.0)
    assert len(plan["before_event"]) == 3
    assert plan["before_event"][-1]["time"] == "15:00"