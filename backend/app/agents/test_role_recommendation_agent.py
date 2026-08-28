from app.agents.role_recommendation_agent import get_role_recommendations

def test_high_risk_has_all_roles():
    recs = get_role_recommendations("HIGH RISK")
    assert set(recs.keys()) == {"attendees", "medical_team", "event_staff", "performers", "event_manager"}

def test_low_risk_returns_low_risk_content():
    recs = get_role_recommendations("LOW RISK")
    assert "No special heat precautions" in recs["attendees"]

def test_unknown_status_falls_back_to_moderate():
    recs = get_role_recommendations("SOME_UNKNOWN_STATUS")
    assert recs == get_role_recommendations("MODERATE RISK")