# backend/test_temp_unit_check.py
from app.services.heat_intelligence_service import generate_heat_intelligence_report

path = generate_heat_intelligence_report(
    latitude=36.1699, longitude=-115.1398,
    temperature=100,  # agar Celsius treat kiya, PDF mein "100°C (212°F)" dikhna chahiye
    date_str="2024-07-20",
    analysis=["environmental"],
)
print(f"Check the PDF: {path}")