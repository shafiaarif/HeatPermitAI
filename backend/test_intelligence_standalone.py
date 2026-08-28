# backend/test_intelligence_standalone.py
from app.services.heat_intelligence_service import generate_heat_intelligence_report

path = generate_heat_intelligence_report(
    latitude=36.1699, longitude=-115.1398,
    temperature=41.5, date_str="2024-07-20",
    analysis=["environmental", "events"],
)
print(f"\nDone! PDF saved at: {path}")