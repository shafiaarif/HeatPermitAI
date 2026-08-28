
import pytest
from app.services.risk_scoring import compute_risk_score, classify_hourly_tier, generate_hour_range

def test_high_risk():
    r = compute_risk_score(peak_temp=42, exceedance_hours=6, persistence_hours=5, event_duration_hours=6)
    assert r["status"] == "HIGH RISK"

def test_low_risk():
    r = compute_risk_score(peak_temp=26, exceedance_hours=0, persistence_hours=0, event_duration_hours=6)
    assert r["status"] == "LOW RISK"

def test_moderate_risk():
    r = compute_risk_score(peak_temp=33, exceedance_hours=2, persistence_hours=1, event_duration_hours=6)
    assert r["status"] in ("MODERATE RISK", "LOW-MODERATE RISK")

def test_zero_duration_raises():
    with pytest.raises(ValueError):
        compute_risk_score(peak_temp=35, exceedance_hours=1, persistence_hours=1, event_duration_hours=0)

def test_missing_peak_temp_raises():
    with pytest.raises(ValueError):
        compute_risk_score(peak_temp=None, exceedance_hours=1, persistence_hours=1, event_duration_hours=6)

def test_hourly_tier_safe():
    assert classify_hourly_tier(heat_index=25, wet_bulb_temp=22) == "Safe"

def test_hourly_tier_caution():
    assert classify_hourly_tier(heat_index=32, wet_bulb_temp=30) == "Caution"

def test_hourly_tier_danger():
    assert classify_hourly_tier(heat_index=36, wet_bulb_temp=33) == "Danger"

def test_hourly_tier_extreme_by_heat_index():
    assert classify_hourly_tier(heat_index=41, wet_bulb_temp=23) == "Extreme"

def test_hourly_tier_missing_both():
    assert classify_hourly_tier(heat_index=None, wet_bulb_temp=None) == "Unknown"

def test_hour_range_same_day():
    assert generate_hour_range("14:00", "18:00") == ["14:00", "15:00", "16:00", "17:00"]

def test_hour_range_overnight():
    assert generate_hour_range("22:00", "02:00") == ["22:00", "23:00", "00:00", "01:00"]


















# import pytest
# from app.services.risk_scoring import compute_risk_score, classify_hourly_tier, generate_hour_range

# def test_high_risk():
#     r = compute_risk_score(peak_temp=42, exceedance_hours=6, persistence_hours=5, event_duration_hours=6)
#     assert r["status"] == "HIGH RISK"

# def test_low_risk():
#     r = compute_risk_score(peak_temp=26, exceedance_hours=0, persistence_hours=0, event_duration_hours=6)
#     assert r["status"] == "LOW RISK"

# def test_moderate_risk():
#     r = compute_risk_score(peak_temp=33, exceedance_hours=2, persistence_hours=1, event_duration_hours=6)
#     assert r["status"] in ("MODERATE RISK", "LOW-MODERATE RISK")

# def test_zero_duration_raises():
#     with pytest.raises(ValueError):
#         compute_risk_score(peak_temp=35, exceedance_hours=1, persistence_hours=1, event_duration_hours=0)

# def test_missing_peak_temp_raises():
#     with pytest.raises(ValueError):
#         compute_risk_score(peak_temp=None, exceedance_hours=1, persistence_hours=1, event_duration_hours=6)

# def test_hourly_tier_safe():
#     assert classify_hourly_tier(heat_index=25, wet_bulb_temp=22) == "Safe"

# def test_hourly_tier_extreme_by_heat_index():
#     assert classify_hourly_tier(heat_index=41, wet_bulb_temp=23) == "Extreme"

# def test_hourly_tier_missing_both():
#     assert classify_hourly_tier(heat_index=None, wet_bulb_temp=None) == "Unknown"

# def test_hour_range_same_day():
#     assert generate_hour_range("14:00", "18:00") == ["14:00", "15:00", "16:00", "17:00"]

# def test_hour_range_overnight():
#     assert generate_hour_range("22:00", "02:00") == ["22:00", "23:00", "00:00", "01:00"]